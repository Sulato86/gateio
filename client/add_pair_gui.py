import tkinter as tk
from tkinter import messagebox
import requests
import threading
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logging_config import configure_logging  # Impor konfigurasi logging

# Inisialisasi logger
logger = configure_logging('add_pair_gui', 'logs/add_pair_gui.log')

class AddPairApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Add Trading Pair")

        # Label untuk API URL
        self.url_label = tk.Label(root, text="API URL:")
        self.url_label.pack(pady=5)

        # Entry untuk API URL
        self.url_entry = tk.Entry(root, width=50)
        self.url_entry.pack(pady=5)
        self.url_entry.insert(0, "http://194.233.66.8:5000/add_pair")

        # Label untuk Pair
        self.pair_label = tk.Label(root, text="Trading Pair:")
        self.pair_label.pack(pady=5)

        # Entry untuk Pair
        self.pair_entry = tk.Entry(root, width=20)
        self.pair_entry.pack(pady=5)
        self.pair_entry.insert(0, "ETH_USDT")

        # Tombol untuk Submit
        self.submit_button = tk.Button(root, text="Add Pair", command=self.start_thread)
        self.submit_button.pack(pady=20)

    def start_thread(self):
        # Mulai thread baru untuk menjalankan add_pair tanpa membekukan GUI
        thread = threading.Thread(target=self.add_pair)
        thread.start()

    def add_pair(self):
        url = self.url_entry.get()
        pair = self.pair_entry.get()
        data = {"pair": pair}

        try:
            logger.debug(f"Mengirim request untuk menambahkan pair: {pair}")
            response = requests.post(url, json=data)

            if response.status_code == 200:
                self.show_message("Success", f"Pair {pair} added successfully.")
                logger.info(f"Pair {pair} berhasil ditambahkan.")
            else:
                error_message = response.json().get('error', 'Unknown error')
                self.show_message("Error", f"Failed to add pair: {error_message}")
                logger.error(f"Gagal menambahkan pair {pair}: {error_message}")
        except Exception as e:
            self.show_message("Error", f"Request failed: {str(e)}")
            logger.error(f"Request gagal: {str(e)}")

    def show_message(self, title, message):
        # Pastikan bahwa update GUI dilakukan di thread utama
        self.root.after(0, lambda: messagebox.showinfo(title, message))

if __name__ == "__main__":
    root = tk.Tk()
    app = AddPairApp(root)
    root.mainloop()
