import os
import json
import asyncio
import websockets
import logging
import time
from dotenv import load_dotenv
from gate_api import Configuration, ApiClient, SpotApi, WalletApi

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

if not api_key or not api_secret:
    raise ValueError("API_KEY dan API_SECRET harus disetel dalam environment variables")

# Konfigurasi API
configuration = Configuration(key=api_key, secret=api_secret)
api_client = ApiClient(configuration=configuration)

class GateIOAPI:
    def __init__(self, api_client):
        self.api_client = api_client
        self.spot_api = SpotApi(api_client)
        self.wallet_api = WalletApi(api_client)

    def get_balances(self):
        try:
            return self.wallet_api.list_all_balances()
        except Exception as e:
            logger.error(f"Error getting balances: {e}")
            return None

    def get_order_history(self, currency_pair):
        try:
            return self.spot_api.list_orders(currency_pair=currency_pair, status='finished')
        except Exception as e:
            logger.error(f"Error getting order history: {e}")
            return None

    def cancel_order(self, currency_pair, order_id):
        try:
            return self.spot_api.cancel_order(currency_pair=currency_pair, order_id=order_id)
        except Exception as e:
            logger.error(f"Error canceling order: {e}")
            return None

class GateIOWebSocket:
    def __init__(self, message_callback):
        self.message_callback = message_callback
        self.ws_url = "wss://api.gateio.ws/ws/v4/"

    async def on_message(self, message):
        try:
            data = json.loads(message)
            logger.info(f"Received message: {data}")
            if asyncio.iscoroutinefunction(self.message_callback):
                await self.message_callback(data)
            else:
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
        while True:
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    await self.on_open(websocket)
                    async for message in websocket:
                        await self.on_message(message)
            except websockets.ConnectionClosed as e:
                logger.error(f"WebSocket connection closed: {e}")
                await asyncio.sleep(5)  # Retry setelah 5 detik
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await asyncio.sleep(5)  # Retry setelah 5 detik

    async def get_account_balance(self):
        return GateIOAPI(api_client).get_balances()

    async def get_order_history(self, currency_pair):
        return GateIOAPI(api_client).get_order_history(currency_pair)
        
    async def cancel_order(self, currency_pair, order_id):
        return GateIOAPI(api_client).cancel_order(currency_pair, order_id)
