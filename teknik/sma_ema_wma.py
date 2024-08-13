import time
import requests
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logging_config import configure_logging

logger = logger = configure_logging('sma_ema_wma', 'logs/sma_ema_wma.log')

def fetch_data_from_api(pair, period, limit=100):
    url = f"http://194.233.66.8:5000/get_candlestick_data?pair={pair}&period={period}&limit={limit}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return [float(value) for value in response.json()]
        else:
            logger.error(f"Failed to fetch data from API: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to API: {e}")
        return []

def calculate_ema(values, period):
    if not values:
        raise ValueError("Daftar nilai tidak boleh kosong.")
    ema_values = []
    multiplier = 2 / (period + 1)
    ema_values.append(float(values[0]))
    for value in values[1:]:
        ema = (float(value) - ema_values[-1]) * multiplier + ema_values[-1]
        ema_values.append(ema)
    return ema_values[-1]

def calculate_sma(values, period):
    if len(values) < period:
        raise ValueError("Jumlah nilai lebih kecil dari periode.")
    return sum(float(value) for value in values[-period:]) / period

def calculate_wma(values, period):
    if len(values) < period:
        raise ValueError("Jumlah nilai lebih kecil dari periode.")
    weights = list(range(1, period + 1))
    weighted_values = [float(value) * weight for value, weight in zip(values[-period:], weights)]
    return sum(weighted_values) / sum(weights)

def calculate_moving_averages(pair, period):
    close_prices = fetch_data_from_api(pair, period)
    if len(close_prices) < period:
        logger.warning(f"Not enough data to calculate SMA, EMA, WMA for {pair}.")
        return None, None, None
    sma_value = calculate_sma(close_prices, period)
    ema_value = calculate_ema(close_prices, period)
    wma_value = calculate_wma(close_prices, period)
    return sma_value, ema_value, wma_value

if __name__ == "__main__":
    pair = "BTC_USDT"
    period = 14

    while True:
        sma_value, ema_value, wma_value = calculate_moving_averages(pair, period)

        if sma_value and ema_value and wma_value:
            print(f"SMA for {pair}: {sma_value}")
            print(f"EMA for {pair}: {ema_value}")
            print(f"WMA for {pair}: {wma_value}")
        else:
            print(f"Not enough data to calculate moving averages for {pair}.")

        time.sleep(60)
