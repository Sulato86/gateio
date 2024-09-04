import requests
import os
import sys
import pandas as pd
import numpy as np
import talib
import time
import threading
import tkinter as tk
from tkinter import ttk
from requests.exceptions import RequestException
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logging_config import configure_logging

BASE_URL = "http://154.26.128.195:5000"

logger = configure_logging("rsi_calculator_gui", "logs/rsi_calculator_gui.log")

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

def fetch_available_intervals_and_pairs():
    subscription_name = "5m_BTC_USDT"
    data = get_candlestick_data(subscription_name)
    if data is not None:
        intervals = sorted(set(data['subscription_name'].str.split('_').str[0]))
        pairs = sorted(set(data['subscription_name'].str.split('_').str[1] + '_' + data['subscription_name'].str.split('_').str[2]))
        return intervals, pairs
    else:
        logger.error("Gagal mengambil data untuk interval dan pair.")
        return [], []

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
        return None
    try:
        indicators = {}
        indicators['SMA'] = talib.SMA(close_prices, timeperiod=length)
        indicators['EMA'] = talib.EMA(close_prices, timeperiod=length)
        indicators['WMA'] = talib.WMA(close_prices, timeperiod=length)
        indicators['RSI'] = calculate_rsi(close_prices, length, smoothing_method=smoothing_method, smoothing_length=smoothing_length)
        latest_data = {
            'SMA': indicators['SMA'][-1],
            'EMA': indicators['EMA'][-1],
            'WMA': indicators['WMA'][-1],
            'RSI': indicators['RSI'][-1]
        }
        return latest_data
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        return None

def update_gui_with_indicators(indicators, text_widget):
    text_widget.config(state=tk.NORMAL)
    text_widget.delete(1.0, tk.END)
    if indicators:
        text_widget.insert(tk.END, f"SMA: {indicators['SMA']}\n")
        text_widget.insert(tk.END, f"EMA: {indicators['EMA']}\n")
        text_widget.insert(tk.END, f"WMA: {indicators['WMA']}\n")
        text_widget.insert(tk.END, f"RSI: {indicators['RSI']}\n")
    else:
        text_widget.insert(tk.END, "Tidak ada indikator yang tersedia.\n")
    text_widget.config(state=tk.DISABLED)

def start_calculation(interval, pair, length, smoothing_method, smoothing_length, text_widget):
    subscription_name = f"{interval}_{pair}"
    def calculate():
        while True:
            try:
                candlestick_data = get_candlestick_data(subscription_name)
                if candlestick_data is not None and not candlestick_data.empty:
                    indicators = calculate_indicators(candlestick_data, length, smoothing_method, smoothing_length)
                    update_gui_with_indicators(indicators, text_widget)
                else:
                    logger.error(f"Tidak ada data yang ditemukan untuk subscription_name: {subscription_name}")
                time.sleep(60)
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(60)
    threading.Thread(target=calculate, daemon=True).start()

def create_gui(intervals, pairs):
    root = tk.Tk()
    root.title("RSI Calculator")
    ttk.Label(root, text="Pilih Interval:").grid(column=0, row=0, padx=10, pady=10)
    interval = tk.StringVar()
    interval_combo = ttk.Combobox(root, textvariable=interval)
    interval_combo['values'] = intervals
    interval_combo.grid(column=1, row=0, padx=10, pady=10)
    interval_combo.current(0)
    ttk.Label(root, text="Pilih Pasangan:").grid(column=0, row=1, padx=10, pady=10)
    pair = tk.StringVar()
    pair_combo = ttk.Combobox(root, textvariable=pair)
    pair_combo['values'] = pairs
    pair_combo.grid(column=1, row=1, padx=10, pady=10)
    pair_combo.current(0)
    ttk.Label(root, text="Pilih Metode Smoothing:").grid(column=0, row=2, padx=10, pady=10)
    smoothing_method = tk.StringVar()
    smoothing_combo = ttk.Combobox(root, textvariable=smoothing_method)
    smoothing_combo['values'] = ['SMA', 'EMA', 'WMA']
    smoothing_combo.grid(column=1, row=2, padx=10, pady=10)
    smoothing_combo.current(1)
    ttk.Label(root, text="Panjang Periode:").grid(column=0, row=3, padx=10, pady=10)
    length = tk.IntVar(value=14)
    length_spinbox = ttk.Spinbox(root, from_=1, to=100, textvariable=length)
    length_spinbox.grid(column=1, row=3, padx=10, pady=10)
    ttk.Label(root, text="Panjang Smoothing:").grid(column=0, row=4, padx=10, pady=10)
    smoothing_length = tk.IntVar(value=14)
    smoothing_length_spinbox = ttk.Spinbox(root, from_=1, to=100, textvariable=smoothing_length)
    smoothing_length_spinbox.grid(column=1, row=4, padx=10, pady=10)
    text_widget = tk.Text(root, height=10, width=50, state=tk.DISABLED)
    text_widget.grid(column=0, row=5, columnspan=2, padx=10, pady=10)

    def on_start():
        selected_interval = interval.get()
        selected_pair = pair.get()
        selected_smoothing_method = smoothing_method.get()
        selected_length = length.get()
        selected_smoothing_length = smoothing_length.get()
        start_calculation(selected_interval, selected_pair, selected_length, selected_smoothing_method, selected_smoothing_length, text_widget)
    start_button = ttk.Button(root, text="Mulai", command=on_start)
    start_button.grid(column=0, row=6, columnspan=2, pady=20)

    root.mainloop()

if __name__ == "__main__":
    intervals, pairs = fetch_available_intervals_and_pairs()
    
    if intervals and pairs:
        create_gui(intervals, pairs)
    else:
        logger.error("Gagal mendapatkan interval dan pair dari API.")
