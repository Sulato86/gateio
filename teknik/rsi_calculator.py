import requests
import os
import sys
import pandas as pd
import numpy as np
import talib
import time
from requests.exceptions import RequestException

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logging_config import configure_logging

BASE_URL = "http://154.26.128.195:5000"

logger = configure_logging("rsi_calculator", "logs/rsi_calculator.log")

def get_candlestick_data(subscription_name):
    url = f"{BASE_URL}/get_candlestick_data"
    params = {"subscription_name": subscription_name}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
    except RequestException as e:
        logger.error(f"HTTP request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None
    if response.status_code == 200:
        try:
            data = response.json()
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values(by='timestamp').reset_index(drop=True)
            if df.isnull().values.any():
                logger.warning("Data contains NaN values. Cleaning data...")
                df = df.dropna()
            return df
        except (ValueError, KeyError) as e:
            logger.error(f"Data processing error: {e}")
            return None
    else:
        logger.error(f"Failed to retrieve data. Status code: {response.status_code}")
        return None

def calculate_rsi(prices, length, smoothing_method='EMA', smoothing_length=1):
    if len(prices) < length:
        logger.warning(f"Insufficient data to calculate RSI. Data length: {len(prices)}, required: {length}")
        return np.full(len(prices), np.nan)
    try:
        delta = np.diff(prices, prepend=np.nan)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        if smoothing_method == 'SMA':
            avg_gain = talib.SMA(gain, timeperiod=length)
            avg_loss = talib.SMA(loss, timeperiod=length)
        elif smoothing_method == 'EMA':
            avg_gain = talib.EMA(gain, timeperiod=length)
            avg_loss = talib.EMA(loss, timeperiod=length)
        elif smoothing_method == 'WMA':
            avg_gain = talib.WMA(gain, timeperiod=length)
            avg_loss = talib.WMA(loss, timeperiod=length)
        else:
            raise ValueError("Invalid smoothing method. Use 'SMA', 'EMA', or 'WMA'.")
        if smoothing_length > 1:
            avg_gain = talib.EMA(avg_gain, timeperiod=smoothing_length)
            avg_loss = talib.EMA(avg_loss, timeperiod=smoothing_length)
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsi = np.concatenate([np.full(length, np.nan), rsi[length:]])
        if len(rsi) < len(prices):
            rsi = np.concatenate([np.full(len(prices) - len(rsi), np.nan), rsi])
        return rsi
    except Exception as e:
        logger.error(f"Error calculating RSI: {e}")
        return np.full(len(prices), np.nan)

def calculate_indicators(candlestick_data, length=14, smoothing_method='SMA', smoothing_length=14):
    close_prices = candlestick_data['close'].astype(np.float64).values
    if len(candlestick_data) < length:
        logger.warning("Data tidak mencukupi untuk menghitung indikator.")
        return
    try:
        candlestick_data['SMA'] = talib.SMA(close_prices, timeperiod=length)
        candlestick_data['EMA'] = talib.EMA(close_prices, timeperiod=length)
        candlestick_data['WMA'] = talib.WMA(close_prices, timeperiod=length)
        candlestick_data['RSI'] = calculate_rsi(close_prices, length, smoothing_method=smoothing_method, smoothing_length=smoothing_length)
        latest_data = candlestick_data.iloc[-1]
        if not pd.isna(latest_data['SMA']):
            logger.info(f"SMA: {latest_data['SMA']}")
            logger.info(f"EMA: {latest_data['EMA']}")
            logger.info(f"WMA: {latest_data['WMA']}")
            logger.info(f"RSI ({smoothing_method}): {latest_data['RSI']}")
        else:
            logger.warning("Indikator belum tersedia untuk data terbaru.")
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")

if __name__ == "__main__":
    subscription_name = "1m_BTC_USDT"
    length = 14
    smoothing_method = 'EMA'
    smoothing_length = 14

    while True:
        try:
            candlestick_data = get_candlestick_data(subscription_name)
            
            if candlestick_data is not None and not candlestick_data.empty:
                calculate_indicators(candlestick_data, length, smoothing_method, smoothing_length)
            else:
                logger.error(f"Tidak ada data yang ditemukan untuk subscription_name: {subscription_name}")
            
            time.sleep(60)
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            time.sleep(60)
