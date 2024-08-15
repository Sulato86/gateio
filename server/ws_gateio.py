import asyncio
import sys
import psycopg2
import json
import time
import random
from datetime import datetime
import websockets
from logging_config import configure_logging

# Initialize logger using logging_config.py
logger = configure_logging('data_handler', 'logs/data_handler.log')

# DatabaseHandler class for managing database operations
class DatabaseHandler:
    def __init__(self):
        self.db_connection = self.connect_to_db()
        self.data_queue = asyncio.Queue()

    def connect_to_db(self):
        try:
            connection = psycopg2.connect(
                database="gateio_db",
                user="postgres",
                password="Wongk3r3n!",
                host="localhost",
                port="5432"
            )
            return connection
        except Exception as e:
            logger.critical(f"Failed to connect to the database: {e}")
            sys.exit(1)

    async def data_consumer(self):
        while True:
            data_batch = []
            while not self.data_queue.empty():
                data_batch.append(await self.data_queue.get())
            
            if data_batch:
                self.insert_data_to_db(data_batch)
            
            await asyncio.sleep(1)  # Adjust sleep time based on data frequency

    def insert_data_to_db(self, data_batch):
        try:
            cursor = self.db_connection.cursor()
            query = """
                INSERT INTO candlestick_data (
                    timestamp, open, high, low, close, total_volume, subscription_name,
                    base_currency_amount, window_close
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.executemany(query, data_batch)
            self.db_connection.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Failed to insert data into the database: {e}")
            self.db_connection.rollback()

    async def enqueue_data(self, data):
        await self.data_queue.put(data)

# GateIOWebSocket class for handling WebSocket connection and data subscription
class GateIOWebSocket:
    def __init__(self, message_callback=None, pairs=None, interval="1m"):
        if pairs is None or not pairs:
            raise ValueError("Pairs list cannot be None or empty.")
        self.message_callback = message_callback
        self.pairs = pairs
        self.interval = interval
        self.websocket = None

    def epoch_to_local_time(self, epoch_time):
        try:
            if epoch_time is None:
                return None
            epoch_time = float(epoch_time)
            local_time = datetime.fromtimestamp(epoch_time).strftime('%Y-%m-%d %H:%M:%S')
            return local_time
        except (TypeError, ValueError) as e:
            logger.error(f"Error converting epoch time: {e}")
            return None

    async def on_message(self, message: str):
        try:
            data = json.loads(message)
            if 'result' in data and 'n' in data['result']:
                result = data['result']
                window_close = result.get('w')

                if window_close:
                    extracted_data = (
                        self.epoch_to_local_time(result.get('t')),
                        result.get('o'),
                        result.get('h'),
                        result.get('l'),
                        result.get('c'),
                        result.get('v'),
                        result.get('n'),
                        result.get('a'),
                        window_close
                    )
                    await self.message_callback(extracted_data)
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
        backoff_time = 1  # Initial backoff time (1 second)
        max_backoff = 32  # Maximum backoff time (32 seconds)

        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    self.websocket = websocket
                    await self.subscribe()
                    backoff_time = 1  # Reset backoff time on successful connection
                    async for message in websocket:
                        await self.on_message(message)
            except Exception as e:
                logger.error(f"WebSocket connection failed: {e}")
                sleep_time = backoff_time + random.uniform(0, 1)  # Add randomness to avoid thundering herd problem
                logger.info(f"Reconnecting in {sleep_time} seconds...")
                await asyncio.sleep(sleep_time)
                backoff_time = min(backoff_time * 2, max_backoff)  # Exponentially increase the backoff time

# DataHandler class for managing both WebSocket and Database operations
class DataHandler:
    def __init__(self):
        self.database_handler = DatabaseHandler()
        self.websocket_handler = GateIOWebSocket(
            message_callback=self.database_handler.enqueue_data,
            pairs=["BTC_USDT", "ETH_USDT"]
        )

    async def start(self):
        # Use asyncio.gather to run both tasks concurrently
        await asyncio.gather(
            self.database_handler.data_consumer(),
            self.websocket_handler.run()
        )

if __name__ == "__main__":
    handler = DataHandler()
    # Use asyncio.run to start the event loop
    asyncio.run(handler.start())
