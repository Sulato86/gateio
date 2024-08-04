import json
import asyncio
import websockets
import time
from logging_config import configure_logging

# Konfigurasi logging untuk balances_loader
logger = configure_logging('websocket_gateio', 'logs/websocket_gateio.log')

class GateIOWebSocket:
    """
    Kelas untuk berinteraksi dengan WebSocket Gate.io.
    """

    def __init__(self, message_callback, pairs=None):
        """
        Inisialisasi GateIOWebSocket.

        Args:
            message_callback (function): Callback untuk menangani pesan yang diterima.
            pairs (list): Daftar pasangan mata uang untuk disubscribe.
        """
        logger.debug("Inisialisasi GateIOWebSocket")
        self.message_callback = message_callback
        self.ws_url = "wss://api.gateio.ws/ws/v4/"
        self.pairs = pairs if pairs else []
        self.websocket = None
        self.pending_pairs = []
        if not self.pairs:
            logger.error("Pairs list is empty. Please provide at least one pair.")

    async def on_message(self, message):
        """
        Menghandle pesan yang diterima dari WebSocket.

        Args:
            message (str): Pesan dalam bentuk string JSON.
        """
        logger.debug("on_message dipanggil")
        try:
            data = json.loads(message)
            logger.info(f"Received message: {data}")
            if asyncio.iscoroutinefunction(self.message_callback):
                await self.message_callback(data)
            else:
                self.message_callback(data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e} - message: {message}")

    async def on_error(self, error):
        """
        Menghandle error yang terjadi pada WebSocket.

        Args:
            error (Exception): Error yang terjadi.
        """
        logger.error(f"WebSocket error: {error}")

    async def on_close(self):
        """
        Menghandle penutupan koneksi WebSocket.
        """
        logger.info("WebSocket closed")

    async def on_open(self, websocket):
        """
        Dipanggil saat koneksi WebSocket dibuka.

        Args:
            websocket (WebSocketClientProtocol): Objek WebSocket.
        """
        logger.info("WebSocket opened")
        self.websocket = websocket
        await self.subscribe(self.pairs)
        logger.info(f"Subscribed to pairs: {self.pairs}")

        if self.pending_pairs:
            await self.subscribe(self.pending_pairs)
            logger.info(f"Subscribed to pending pairs: {self.pending_pairs}")
            self.pending_pairs = []

    async def subscribe(self, pairs):
        """
        Subscribe ke channel untuk pasangan mata uang tertentu.

        Args:
            pairs (list): Daftar pasangan mata uang untuk disubscribe.
        """
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
        await self.websocket.send(json.dumps(message))
        logger.debug(f"Current pairs: {self.pairs}")

    async def subscribe_to_pair(self, pair):
        """
        Menambah subscription ke pasangan mata uang baru.

        Args:
            pair (str): Pasangan mata uang baru untuk disubscribe.
        """
        if pair not in self.pairs:
            self.pairs.append(pair)
            if self.websocket:
                logger.info(f"Subscribing to new pair: {pair}")
                await self.subscribe([pair])
                logger.info(f"Subscribed to new pair: {pair}")
            else:
                logger.error("WebSocket is not connected. Adding to pending pairs.")
                self.pending_pairs.append(pair)

    async def unsubscribe_from_pair(self, pair):
        """
        Unsubscribe dari pasangan mata uang tertentu.

        Args:
            pair (str): Pasangan mata uang untuk diunsubscribe.
        """
        if pair in self.pairs:
            self.pairs.remove(pair)
            if self.websocket and self.websocket.open:
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
        else:
            logger.warning(f"Pair {pair} is not in the list. Cannot unsubscribe.")

    async def run(self):
        """
        Menjalankan loop WebSocket untuk menghubungkan dan menangani pesan.
        """
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
                await asyncio.sleep(5 * retry_count)  # Exponential backoff
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                retry_count += 1
                await asyncio.sleep(5 * retry_count)  # Exponential backoff
        logger.error("Max retries reached, exiting run loop")
