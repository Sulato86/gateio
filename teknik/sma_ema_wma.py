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

# Ganti dengan IP VPS Anda
BASE_URL = "http://154.26.128.195:5000"

# Konfigurasi logging
logger = configure_logging("sma_ema_ema", "logs/sma_ema_wma.log")

def get_candlestick_data(subscription_name):
    url = f"{BASE_URL}/get_candlestick_data"
    params = {"subscription_name": subscription_name}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Menghasilkan exception jika status code tidak 200
    except RequestException as e:
        logger.error(f"HTTP request failed: {e}")
        return None
    
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        
        # Pastikan kolom timestamp diubah menjadi datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Urutkan berdasarkan timestamp
        df = df.sort_values(by='timestamp').reset_index(drop=True)
        
        # Cek jika ada missing values
        if df.isnull().values.any():
            logger.warning("Data contains NaN values. Cleaning data...")
            df = df.dropna()
        
        return df
    else:
        logger.error(f"Failed to retrieve data. Status code: {response.status_code}")
        return None

def calculate_indicators(candlestick_data):
    # Mengubah kolom close menjadi array numpy dengan tipe float64
    close_prices = candlestick_data['close'].astype(np.float64).values
    
    # Hitung SMA, EMA, dan WMA dengan jendela 14 periode (bisa disesuaikan)
    sma_window = 14
    ema_window = 14
    wma_window = 14
    
    # Pastikan data cukup untuk menghitung indikator
    if len(candlestick_data) < sma_window:
        logger.warning("Data tidak mencukupi untuk menghitung indikator.")
        return
    
    # Menghitung menggunakan TA-Lib
    candlestick_data['SMA'] = talib.SMA(close_prices, timeperiod=sma_window)
    candlestick_data['EMA'] = talib.EMA(close_prices, timeperiod=ema_window)
    candlestick_data['WMA'] = talib.WMA(close_prices, timeperiod=wma_window)
    
    # Tampilkan nilai SMA, EMA, dan WMA terakhir, pastikan nilai indikator tidak NaN
    if not pd.isna(candlestick_data['SMA'].iloc[-1]):
        logger.info(f"SMA: {candlestick_data['SMA'].iloc[-1]}")
        logger.info(f"EMA: {candlestick_data['EMA'].iloc[-1]}")
        logger.info(f"WMA: {candlestick_data['WMA'].iloc[-1]}")
    else:
        logger.warning("Indikator belum tersedia untuk data terbaru.")

if __name__ == "__main__":
    subscription_name = "1m_BTC_USDT"
    
    while True:
        # Ambil data candlestick dari server Flask
        candlestick_data = get_candlestick_data(subscription_name)
        
        if candlestick_data is not None and not candlestick_data.empty:
            # Hitung indikator teknikal
            calculate_indicators(candlestick_data)
        else:
            logger.error(f"Tidak ada data yang ditemukan untuk subscription_name: {subscription_name}")
        
        # Tunggu 60 detik sebelum menghitung ulang
        time.sleep(60)
