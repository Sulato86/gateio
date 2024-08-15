import asyncio
import sys
import psycopg2
import json
import time
from datetime import datetime
from logging_config import configure_logging
from gateio_ws import GateIOWebSocket

logger = configure_logging('data_handler', 'logs/data_handler.log')

class DataHandler:
    def __init__(self):
        self.db_connection = self.connect_to_db()
        self.pairs = ["BTC_USDT", "ETH_USDT"]
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.websocket_instance = None

    def connect_to_db(self):
        try:
            connection = psycopg2.connect(
                database="gateio",
                user="postgres",
                password="Wongk3r3n!",
                host="localhost",
                port="5432"
            )
            return connection
        except Exception as e:
            logger.critical(f"Failed to connect to the database: {e}")
            sys.exit(1)

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

    def insert_data_to_db(self, data, window_close):
        try:
            cursor = self.db_connection.cursor()
            query = """
                INSERT INTO candlestick_data (
                    timestamp, open, high, low, close, total_volume, subscription_name,
                    base_currency_amount, window_close
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            local_timestamp = self.epoch_to_local_time(data.get('t'))
            if local_timestamp is None:
                return
            cursor.execute(query, (
                local_timestamp,
                data.get('o'),
                data.get('h'),
                data.get('l'),
                data.get('c'),
                data.get('v'),
                data.get('n'),
                data.get('a'),
                window_close
            ))
            self.db_connection.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Failed to insert data into the database: {e}")
            self.db_connection.rollback()

    def start_websocket(self):
        try:
            self.websocket_instance = GateIOWebSocket(
                message_callback=self.insert_data_to_db,
                pairs=self.pairs
            )
            self.loop.run_until_complete(self.websocket_instance.run())
        except Exception as e:
            logger.error(f"Failed to start WebSocket connection: {e}")

    def add_pair(self, pair):
        if pair not in self.pairs:
            self.pairs.append(pair)
            if self.websocket_instance and self.websocket_instance.websocket:
                asyncio.run_coroutine_threadsafe(
                    self.websocket_instance.websocket.send(json.dumps({
                        "time": int(time.time()),
                        "channel": "spot.candlesticks",
                        "event": "subscribe",
                        "payload": [self.websocket_instance.interval, pair]
                    })),
                    self.loop
                )
            logger.info(f"New pair {pair} added and subscribed.")

