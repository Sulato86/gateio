import aiohttp
import asyncio
import json
import websockets
import time
from typing import Callable, List, Optional
from utils.logging_config import configure_logging

logger = configure_logging('websocket_gateio', 'logs/websocket_gateio.log')

class GateIOWebSocket:
    def __init__(self, message_callback: Callable, pairs: Optional[List[str]] = None):
        logger.debug("Inisialisasi GateIOWebSocket")
        self.message_callback = message_callback
        self.ws_url = "wss://api.gateio.ws/ws/v4/"
        self.pairs = pairs if pairs else []
        self.websocket = None
        self.pending_pairs = []
        self.connected = False

        if not self.pairs:
            logger.error("Pairs list is empty. Please provide at least one pair.")

    async def on_message(self, message: str):
        logger.debug("on_message dipanggil")
        try:
            data = json.loads(message)
            logger.info(f"Received message: {data}")
            if callable(self.message_callback):
                if asyncio.iscoroutinefunction(self.message_callback):
                    await self.message_callback(data)
                else:
                    self.message_callback(data)
            else:
                logger.error("message_callback is not callable")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e} - message: {message}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def on_error(self, error: Exception):
        logger.error(f"WebSocket error: {error}")

    async def on_close(self):
        logger.info("WebSocket closed")
        self.connected = False

    async def on_open(self, websocket: websockets.WebSocketClientProtocol):
        logger.info("WebSocket opened")
        self.websocket = websocket
        self.connected = True
        await self.subscribe(self.pairs)
        logger.info(f"Subscribed to pairs: {self.pairs}")

        if self.pending_pairs:
            await self.subscribe(self.pending_pairs)
            logger.info(f"Subscribed to pending pairs: {self.pending_pairs}")
            self.pending_pairs = []

    async def subscribe(self, pairs: List[str]):
        if not pairs:
            logger.error("Subscribe failed: No pairs provided")
            return
        message = {
            "time": int(time.time()),
            "channel": "spot.tickers",
            "event": "subscribe",
            "payload": pairs
        }
        logger.debug(f"Subscribing with message: {message}")
        try:
            await self.websocket.send(json.dumps(message))
            logger.debug(f"Current pairs: {self.pairs}")
        except Exception as e:
            logger.error(f"Error sending subscribe message: {e}")

    async def subscribe_to_pair(self, pair: str):
        logger.debug(f"Memulai subscription untuk pair baru: {pair}")
        if pair not in self.pairs:
            self.pairs.append(pair)
            logger.debug(f"Pair {pair} ditambahkan ke daftar pairs: {self.pairs}")
            try:
                if self.connected:
                    logger.info(f"Subscribing to new pair: {pair}")
                    await self.subscribe([pair])
                    logger.info(f"Subscribed to new pair: {pair}")
                else:
                    logger.error("WebSocket is not connected. Adding to pending pairs.")
                    self.pending_pairs.append(pair)
                    logger.debug(f"Pair {pair} ditambahkan ke pending pairs: {self.pending_pairs}")
            except Exception as e:
                logger.error(f"Error subscribing to pair {pair}: {e}")

    async def unsubscribe_from_pair(self, pair: str):
        if pair in self.pairs:
            self.pairs.remove(pair)
            try:
                if self.connected:
                    message = {
                        "time": int(time.time()),
                        "channel": "spot.tickers",
                        "event": "unsubscribe",
                        "payload": [pair]
                    }
                    logger.debug(f"Unsubscribing with message: {message}")
                    await self.websocket.send(json.dumps(message))
                    logger.info(f"Unsubscribed from pair: {pair}")
                else:
                    logger.error("WebSocket is not connected. Cannot unsubscribe.")
            except Exception as e:
                logger.error(f"Error unsubscribing from pair {pair}: {e}")
        else:
            logger.warning(f"Pair {pair} is not in the list. Cannot unsubscribe.")

    async def run(self):
        logger.debug("Memulai websocket run loop")
        retry_count = 0
        max_retries = 5
        while retry_count < max_retries:
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    self.websocket = websocket
                    await self.on_open(websocket)
                    async for message in websocket:
                        await self.on_message(message)
            except websockets.ConnectionClosed as e:
                logger.error(f"WebSocket connection closed: {e}")
                retry_count += 1
                logger.info(f"Attempting to reconnect: Retry {retry_count} of {max_retries}")
                await asyncio.sleep(5 * retry_count)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                retry_count += 1
                logger.info(f"Attempting to reconnect: Retry {retry_count} of {max_retries}")
                await asyncio.sleep(5 * retry_count)
        logger.error("Max retries reached, exiting run loop")

    async def is_valid_pair(self, pair):
        async with aiohttp.ClientSession() as session:
            url = f"https://api.gateio.ws/api/v4/spot/currency_pairs/{pair}"
            async with session.get(url) as response:
                return response.status == 200
