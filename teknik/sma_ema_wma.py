import time
import requests
import os
import sys
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logging_config import configure_logging

logger = configure_logging('sma_ema_wma', 'logs/sma_ema_wma.log')

def fetch_data_from_api(pair, period, timeframe, limit=100, retries=3, backoff_factor=1):
    # URL endpoint /get_candlestick_data di server Flask (api_server.py)
    url = f"http://194.233.66.8:5000/get_candlestick_data?pair={pair}&period={period}&timeframe={timeframe}&limit={limit}"

    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    try:
        response = session.get(url, timeout=10)
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

def calculate_moving_averages(pair, period, timeframe):
    close_prices = fetch_data_from_api(pair, period, timeframe)
    if len(close_prices) < period:
        logger.warning(f"Not enough data to calculate SMA, EMA, WMA for {pair} on {timeframe} timeframe.")
        return None, None, None
    try:
        sma_value = calculate_sma(close_prices, period)
        ema_value = calculate_ema(close_prices, period)
        wma_value = calculate_wma(close_prices, period)
        return sma_value, ema_value, wma_value
    except ValueError as e:
        logger.error(f"Error in calculating moving averages: {e}")
        return None, None, None

if __name__ == "__main__":
    pair = "BTC_USDT"
    period = 14
    timeframe = "5m"  # Contoh penggunaan timeframe 5 menit

    while True:
        sma_value, ema_value, wma_value = calculate_moving_averages(pair, period, timeframe)

        if sma_value and ema_value and wma_value:
            print(f"SMA for {pair} on {timeframe} timeframe: {sma_value}")
            print(f"EMA for {pair} on {timeframe} timeframe: {ema_value}")
            print(f"WMA for {pair} on {timeframe} timeframe: {wma_value}")
        else:
            print(f"Not enough data to calculate moving averages for {pair} on {timeframe} timeframe.")

        time.sleep(60)
