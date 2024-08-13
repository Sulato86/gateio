import json
import asyncio
import websockets
import time
from logging_config import configure_logging

logger = configure_logging('gateio', 'logs/gateio.log')

class GateIOWebSocket:
    def __init__(self, message_callback=None, pairs=None, interval="1m"):
        if pairs is None or not pairs:
            raise ValueError("Pairs list cannot be None or empty.")
        self.message_callback = message_callback
        self.pairs = pairs
        self.interval = interval
        self.websocket = None

    async def on_message(self, message: str):
        try:
            data = json.loads(message)
            if 'result' in data and 'n' in data['result']:
                result = data['result']
                extracted_data = {
                    't': result.get('t'),
                    'o': result.get('o'),
                    'h': result.get('h'),
                    'l': result.get('l'),
                    'c': result.get('c'),
                    'v': result.get('v'),
                    'n': result.get('n'),
                    'a': result.get('a'),
                    'w': result.get('w')
                }
                if callable(self.message_callback):
                    if asyncio.iscoroutinefunction(self.message_callback):
                        await self.message_callback(extracted_data)
                    else:
                        self.message_callback(extracted_data)
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def subscribe(self):
        for pair in self.pairs:
            message = {
                "time": int(time.time()),
                "channel": "spot.candlesticks",
                "event": "subscribe",
                "payload": [self.interval, pair]
            }
            await self.websocket.send(json.dumps(message))
            logger.info(f"Subscribed to {pair} with interval {self.interval}")

    async def run(self):
        uri = "wss://api.gateio.ws/ws/v4/"
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    self.websocket = websocket
                    await self.subscribe()
                    async for message in websocket:
                        await self.on_message(message)
            except Exception as e:
                logger.error(f"WebSocket connection failed: {e}")
                logger.info("Reconnecting in 5 seconds...")
                await asyncio.sleep(5)
