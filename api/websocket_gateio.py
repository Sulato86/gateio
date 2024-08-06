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
        self.message_callback = message_callback
        self.ws_url = "wss://api.gateio.ws/ws/v4/"
        self.pairs = pairs if pairs else []
        self.websocket = None
        self.pending_pairs = []
        self.connected = False

    async def on_message(self, message: str):
        try:
            data = json.loads(message)
            if callable(self.message_callback):
                if asyncio.iscoroutinefunction(self.message_callback):
                    await self.message_callback(data)
                else:
                    self.message_callback(data)
        except json.JSONDecodeError:
            pass
        except Exception:
            pass

    async def on_error(self, error: Exception):
        pass

    async def on_close(self):
        self.connected = False

    async def on_open(self, websocket: websockets.WebSocketClientProtocol):
        self.websocket = websocket
        self.connected = True
        await self.subscribe(self.pairs)
        if self.pending_pairs:
            await self.subscribe(self.pending_pairs)
            self.pending_pairs = []

    async def subscribe(self, pairs: List[str]):
        if not pairs:
            return
        message = {
            "time": int(time.time()),
            "channel": "spot.tickers",
            "event": "subscribe",
            "payload": pairs
        }
        try:
            await self.websocket.send(json.dumps(message))
        except Exception:
            pass

    async def subscribe_to_pair(self, pair: str):
        if pair not in self.pairs:
            self.pairs.append(pair)
            try:
                if self.connected:
                    await self.subscribe([pair])
                else:
                    self.pending_pairs.append(pair)
            except Exception:
                pass

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
                    await self.websocket.send(json.dumps(message))
            except Exception:
                pass

    async def run(self):
        retry_count = 0
        max_retries = 5
        while retry_count < max_retries:
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    self.websocket = websocket
                    await self.on_open(websocket)
                    async for message in websocket:
                        await self.on_message(message)
            except websockets.ConnectionClosed:
                retry_count += 1
                await asyncio.sleep(5 * retry_count)
            except Exception:
                retry_count += 1
                await asyncio.sleep(5 * retry_count)

    async def is_valid_pair(self, pair):
        async with aiohttp.ClientSession() as session:
            url = f"https://api.gateio.ws/api/v4/spot/currency_pairs/{pair}"
            async with session.get(url) as response:
                return response.status == 200
