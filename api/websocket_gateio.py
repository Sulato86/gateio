import json
import asyncio
import websockets
import logging
import time

# Inisialisasi logger
logger = logging.getLogger('websocket_gateio')
logger.setLevel(logging.DEBUG)

# Handler untuk file logging
file_handler = logging.FileHandler('websocket_gateio.log')
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Handler untuk console logging
console_handler = logging.StreamHandler()
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# Menambahkan handler ke logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

class GateIOWebSocket:
    # Inisialisasi GateIOWebSocket
    def __init__(self, message_callback, pairs=None):
        logger.debug("Inisialisasi GateIOWebSocket")
        self.message_callback = message_callback
        self.ws_url = "wss://api.gateio.ws/ws/v4/"
        self.pairs = pairs if pairs else ["BTC_USDT", "ETH_USDT", "SOL_USDT"]

    # Method untuk menghandle pesan yang diterima
    async def on_message(self, message):
        logger.debug("on_message dipanggil")
        try:
            data = json.loads(message)
            logger.info(f"Received message: {data}")
            if asyncio.iscoroutinefunction(self.message_callback):
                await self.message_callback(data)
            else:
                self.message_callback(data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")

    # Method untuk menghandle error
    async def on_error(self, error):
        logger.error(f"WebSocket error: {error}")

    # Method untuk menghandle penutupan koneksi
    async def on_close(self):
        logger.info("WebSocket closed")

    # Method yang dipanggil saat koneksi WebSocket dibuka
    async def on_open(self, websocket):
        logger.info("WebSocket opened")
        await self.subscribe(websocket, "spot.tickers", self.pairs)
        logger.info(f"Subscribed to pairs: {self.pairs}")

    # Method untuk subscribe ke channel
    async def subscribe(self, websocket, channel, pairs):
        message = {
            "time": int(time.time()),
            "channel": channel,
            "event": "subscribe",
            "payload": pairs
        }
        logger.debug(f"Subscribing with message: {message}")
        await websocket.send(json.dumps(message))

    # Method untuk menjalankan loop WebSocket
    async def run(self):
        logger.debug("Memulai websocket run loop")
        while True:
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    await self.on_open(websocket)
                    async for message in websocket:
                        await self.on_message(message)
            except websockets.ConnectionClosed as e:
                logger.error(f"WebSocket connection closed: {e}")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    logger.debug("Menjalankan script websocket_gateio.py")
    
    async def message_handler(message):
        logger.info(f"Handling message: {message}")

    pairs = ["BTC_USDT", "ETH_USDT", "SOL_USDT"]
    ws = GateIOWebSocket(message_handler, pairs)
    
    asyncio.run(ws.run())
