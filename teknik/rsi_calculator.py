import sys
import os
import json
import time
import asyncio
import websockets
from datetime import datetime
from collections import deque

# Menambahkan root path project ke sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Menggunakan fungsi configure_logging yang sudah ada
from utils.logging_config import configure_logging

logger = configure_logging('rsi_calculator', 'logs/rsi_calculator.log')

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

class RSI:
    def __init__(self, period=14, smoothing_length=14):
        self.period = period
        self.smoothing_length = smoothing_length
        self.close_prices = deque(maxlen=period + 1)
        self.previous_avg_gain = None
        self.previous_avg_loss = None

    def add_close_price(self, close_price):
        self.close_prices.append(close_price)
        if len(self.close_prices) == self.close_prices.maxlen:
            return self.calculate_rsi()
        else:
            logger.debug(f"Waiting for more data to calculate RSI. Close prices: {list(self.close_prices)}")
            return None

    def calculate_rsi(self):
        gains = []
        losses = []

        for i in range(1, len(self.close_prices)):
            change = self.close_prices[i] - self.close_prices[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        if self.previous_avg_gain is None or self.previous_avg_loss is None:
            average_gain = sum(gains) / self.period
            average_loss = sum(losses) / self.period
        else:
            average_gain = (self.previous_avg_gain * (self.period - 1) + gains[-1]) / self.period
            average_loss = (self.previous_avg_loss * (self.period - 1) + losses[-1]) / self.period

        self.previous_avg_gain = average_gain
        self.previous_avg_loss = average_loss

        logger.debug(f"Average Gain: {average_gain}, Average Loss: {average_loss}")

        if average_loss == 0:
            return 100

        rs = average_gain / average_loss
        rsi = 100 - (100 / (1 + rs))
        logger.debug(f"Calculated RSI: {rsi}")
        return rsi

class GateIOWebSocketWithRSI:
    def __init__(self, message_callback=None, pairs=None, rsi_period=14, interval='1m'):
        if pairs is None:
            pairs = ["BTC_USDT"]
        self.message_callback = message_callback
        self.pairs = pairs
        self.rsi_calculators = {pair: RSI(period=rsi_period, smoothing_length=rsi_period) for pair in self.pairs}
        self.interval = interval
        self.websocket = None
        self.last_update_time = None

    async def on_message(self, message: str):
        try:
            data = json.loads(message)
            logger.info(f"Received data: {data}")
            
            if 'result' in data and 'n' in data['result']:
                result = data['result']
                if 'c' in result:
                    n_value = result['n']
                    pair = "_".join(n_value.split('_')[1:])
                    close_price = float(result['c'])

                    current_time = datetime.now()
                    if self.last_update_time is None or (current_time - self.last_update_time).seconds >= 60:
                        self.last_update_time = current_time
                        if pair in self.rsi_calculators:
                            rsi_value = self.rsi_calculators[pair].add_close_price(close_price)
                            if rsi_value is not None:
                                logger.info(f"RSI for {pair}: {rsi_value}")
                                print(f"RSI for {pair}: {rsi_value}")
                            else:
                                logger.debug(f"RSI value not calculated yet for {pair}.")
                        else:
                            logger.error(f"Pair {pair} not found in RSI calculators")
                    else:
                        logger.debug(f"Skipping RSI calculation for {pair}, time since last update: {(current_time - self.last_update_time).seconds} seconds.")
                else:
                    logger.error(f"Data tidak berisi harga penutupan (close price)")
            else:
                logger.error(f"Key 'n' not found in result or 'result' not as expected: {data}")

            if callable(self.message_callback):
                if asyncio.iscoroutinefunction(self.message_callback):
                    await self.message_callback(data)
                else:
                    self.message_callback(data)
        except Exception as e:
            logger.error(f"Error processing message: {e}")

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
            logger.error(f"WebSocket connection failed: {e}")
            print(f"WebSocket connection failed: {e}")

if __name__ == "__main__":
    try:
        websocket_with_rsi = GateIOWebSocketWithRSI(
            message_callback=None,
            interval='1m'
        )
        asyncio.run(websocket_with_rsi.run())
    except Exception as e:
        print(f"An error occurred: {e}")
        input("Press Enter to exit...")
