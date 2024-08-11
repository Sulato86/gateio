import sys
import os
import json
import time
import asyncio
import websockets
from datetime import datetime
from collections import deque

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logging_config import configure_logging

logger = configure_logging('moving_averages_calculator', 'logs/moving_averages_calculator.log')

def calculate_ema(values, period):
    if not values:
        raise ValueError("Daftar nilai tidak boleh kosong.")
    
    ema_values = []
    multiplier = 2 / (period + 1)
    ema_values.append(values[0])
    for value in values[1:]:
        ema = (value - ema_values[-1]) * multiplier + ema_values[-1]
        ema_values.append(ema)
    
    return ema_values[-1]

def calculate_sma(values, period):
    if len(values) < period:
        raise ValueError("Jumlah nilai lebih kecil dari periode.")
    
    return sum(values[-period:]) / period

def calculate_wma(values, period):
    if len(values) < period:
        raise ValueError("Jumlah nilai lebih kecil dari periode.")
    
    weights = list(range(1, period + 1))
    weighted_values = [value * weight for value, weight in zip(values[-period:], weights)]
    
    return sum(weighted_values) / sum(weights)

class GateIOWebSocket:
    def __init__(self, message_callback=None, pairs=None, interval='1m', ma_period=14):
        if pairs is None:
            pairs = ["BTC_USDT"]
        self.message_callback = message_callback
        self.pairs = pairs
        self.interval = interval
        self.ma_period = ma_period
        self.websocket = None
        self.last_update_time = None
        self.close_prices = {pair: deque(maxlen=ma_period) for pair in self.pairs}

    async def on_message(self, message: str):
        try:
            data = json.loads(message)
            
            if 'result' in data and 'n' in data['result']:
                result = data['result']
                if 'c' in result:
                    n_value = result['n']
                    pair = "_".join(n_value.split('_')[1:])
                    close_price = float(result['c'])

                    current_time = datetime.now()
                    if self.last_update_time is None or (current_time - self.last_update_time).seconds >= 60:
                        self.last_update_time = current_time
                        self.close_prices[pair].append(close_price)

                        if len(self.close_prices[pair]) == self.ma_period:
                            sma_value = calculate_sma(list(self.close_prices[pair]), self.ma_period)
                            ema_value = calculate_ema(list(self.close_prices[pair]), self.ma_period)
                            wma_value = calculate_wma(list(self.close_prices[pair]), self.ma_period)
                            print(f"SMA for {pair}: {sma_value}")
                            print(f"EMA for {pair}: {ema_value}")
                            print(f"WMA for {pair}: {wma_value}")
                        else:
                            print(f"Not enough data to calculate SMA, EMA, WMA for {pair}.")
                    else:
                        pass
                else:
                    pass
            else:
                pass

            if callable(self.message_callback):
                if asyncio.iscoroutinefunction(self.message_callback):
                    await self.message_callback(data)
                else:
                    self.message_callback(data)
        except Exception as e:
            pass

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
            ma_period=14
        )
        asyncio.run(websocket_instance.run())
    except Exception as e:
        print(f"An error occurred: {e}")
        input("Press Enter to exit...")
