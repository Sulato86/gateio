import os
import json
import asyncio
import websockets
import logging
import time
from dotenv import load_dotenv
from gate_api import Configuration, ApiClient

# Load environment variables from .env file
load_dotenv()

# Inisialisasi logger
logger = logging.getLogger('api_gateio')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('api_gateio.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Mendapatkan API key dan API secret dari environment variables
api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')

# Konfigurasi API
configuration = Configuration(key=api_key, secret=api_secret)
api_client = ApiClient(configuration=configuration)

class GateIOWebSocket:
    def __init__(self, message_callback):
        self.message_callback = message_callback
        self.ws_url = "wss://api.gateio.ws/ws/v4/"

    async def on_message(self, message):
        try:
            data = json.loads(message)
            logger.info(f"Received message: {data}")
            self.message_callback(data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")

    async def on_error(self, error):
        logger.error(f"WebSocket error: {error}")

    async def on_close(self):
        logger.info("WebSocket closed")

    async def on_open(self, websocket):
        logger.info("WebSocket opened")
        await self.subscribe(websocket, "spot.tickers", ["BTC_USDT", "ETH_USDT", "SOL_USDT"])
        await self.subscribe(websocket, "spot.balances", [])
        logger.info("Subscribed to multiple channels")

    async def subscribe(self, websocket, channel, params):
        message = {
            "time": int(time.time()),
            "channel": channel,
            "event": "subscribe",
            "payload": params
        }
        logger.debug(f"Subscribing with message: {message}")
        await websocket.send(json.dumps(message))

    async def run(self):
        async with websockets.connect(self.ws_url) as websocket:
            await self.on_open(websocket)
            async for message in websocket:
                await self.on_message(message)

if __name__ == "__main__":
    def print_message(message):
        print("Received message in main:", message)

    gateio_ws = GateIOWebSocket(print_message)
    asyncio.get_event_loop().run_until_complete(gateio_ws.run())
