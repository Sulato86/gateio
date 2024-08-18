import requests
import pandas as pd
import numpy as np
import talib
import time

# Ganti dengan IP VPS Anda
BASE_URL = "http://154.26.128.195:5000"

def get_candlestick_data(subscription_name):
    url = f"{BASE_URL}/get_candlestick_data"
    params = {"subscription_name": subscription_name}
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        
        # Pastikan kolom timestamp diubah menjadi datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Urutkan berdasarkan timestamp
        df = df.sort_values(by='timestamp').reset_index(drop=True)
        
        return df
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")
        return None

def calculate_indicators(candlestick_data):
    # Mengubah kolom close menjadi array numpy dengan tipe float64
    close_prices = candlestick_data['close'].astype(np.float64).values
    
    # Hitung SMA, EMA, dan WMA dengan jendela 9 periode (bisa disesuaikan)
    sma_window = 14
    ema_window = 14
    wma_window = 14
    
    # Menghitung menggunakan TA-Lib
    candlestick_data['SMA'] = talib.SMA(close_prices, timeperiod=sma_window)
    candlestick_data['EMA'] = talib.EMA(close_prices, timeperiod=ema_window)
    candlestick_data['WMA'] = talib.WMA(close_prices, timeperiod=wma_window)
    
    # Tampilkan nilai SMA, EMA, dan WMA terakhir, pastikan nilai indikator tidak NaN
    if not pd.isna(candlestick_data['SMA'].iloc[-1]):
        print("\nNilai Terbaru:")
        print(f"SMA: {candlestick_data['SMA'].iloc[-1]}")
        print(f"EMA: {candlestick_data['EMA'].iloc[-1]}")
        print(f"WMA: {candlestick_data['WMA'].iloc[-1]}")
    else:
        print("Indikator belum tersedia untuk data terbaru.")

if __name__ == "__main__":
    subscription_name = "1h_BTC_USDT"
    
    while True:
        # Ambil data candlestick dari server Flask
        candlestick_data = get_candlestick_data(subscription_name)
        
        if candlestick_data is not None and not candlestick_data.empty:
            # Hitung indikator teknikal
            calculate_indicators(candlestick_data)
        else:
            print("Tidak ada data yang ditemukan untuk subscription_name:", subscription_name)
        
        # Tunggu 60 detik sebelum menghitung ulang
        time.sleep(60)
