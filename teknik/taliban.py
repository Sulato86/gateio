import sys
import os
import json
import asyncio
import websockets
from datetime import datetime
from collections import deque
import numpy as np
import talib
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.logging_config import configure_logging

logger = configure_logging('moving_averages_calculator', 'logs/moving_averages_calculator.log')


class GateIOWebSocket:
    def __init__(self, message_callback=None, pairs=None, interval='1m', length=14):
        if pairs is None:
            pairs = ["BTC_USDT"]
        self.message_callback = message_callback
        self.pairs = pairs
        self.interval = interval
        self.length = length
        self.websocket = None
        self.last_update_time = None  # Menyimpan waktu pembaruan terakhir
        self.close_prices = {pair: deque(maxlen=length) for pair in self.pairs}

    async def on_message(self, message: str):
        try:
            data = json.loads(message)
            
            if 'result' in data and 'n' in data['result']:
                result = data['result']
                
                timestamp = int(result.get('t'))  # Unix timestamp dalam detik
                total_volume = result.get('v')
                close_price = float(result.get('c'))
                highest_price = result.get('h')
                lowest_price = result.get('l')
                open_price = result.get('o')
                subscription_name = result.get('n')
                base_currency_amount = result.get('a')
                window_close = result.get('w')

                pair = "_".join(subscription_name.split('_')[1:])
                
                current_time = datetime.now()

                # Memeriksa apakah sudah 1 menit sejak pembaruan terakhir
                if self.last_update_time is None or (current_time - self.last_update_time).seconds >= 60:
                    self.last_update_time = current_time
                    self.close_prices[pair].append(close_price)

                    if len(self.close_prices[pair]) == self.length:
                        close_prices_array = np.array(self.close_prices[pair])

                        # Menghitung SMA, EMA, dan WMA menggunakan TA-Lib
                        sma_value = talib.SMA(close_prices_array, timeperiod=self.length)[-1]
                        ema_value = talib.EMA(close_prices_array, timeperiod=self.length)[-1]
                        wma_value = talib.WMA(close_prices_array, timeperiod=self.length)[-1]

                        print(f"SMA for {pair}: {sma_value}")
                        print(f"EMA for {pair}: {ema_value}")
                        print(f"WMA for {pair}: {wma_value}")
                    else:
                        print(f"Not enough data to calculate SMA, EMA, WMA for {pair}.")
                else:
                    print(f"Skipping update as 1 minute has not passed yet.")

                """print(f"Timestamp: {timestamp}")
                print(f"Total Volume: {total_volume}")
                print(f"Close Price: {close_price}")
                print(f"Highest Price: {highest_price}")
                print(f"Lowest Price: {lowest_price}")
                print(f"Open Price: {open_price}")
                print(f"Subscription Name: {subscription_name}")
                print(f"Base Currency Trading Amount: {base_currency_amount}")
                print(f"Window Close: {window_close}")"""
            
            if callable(self.message_callback):
                if asyncio.iscoroutinefunction(self.message_callback):
                    await self.message_callback(data)
                else:
                    self.message_callback(data)
        except Exception as e:
            print(f"Error processing message: {e}")

    async def subscribe(self, pairs):
        message = {
            "time": int(time.time()),
            "channel": "spot.candlesticks",
            "event": "subscribe",
            "payload": [self.interval, pairs[0]]
        }
        await self.websocket.send(json.dumps(message))

    async def run(self):
        uri = "wss://api.gateio.ws/ws/v4/"
        try:
            async with websockets.connect(uri) as websocket:
                self.websocket = websocket
                await self.subscribe(self.pairs)
                async for message in websocket:
                    await self.on_message(message)
        except Exception as e:
            print(f"WebSocket connection failed: {e}")


if __name__ == "__main__":
    try:
        websocket_instance = GateIOWebSocket(
            message_callback=None,
            interval='1m',
            length=14
        )
        asyncio.run(websocket_instance.run())
    except Exception as e:
        print(f"An error occurred: {e}")
        input("Press Enter to exit...")
