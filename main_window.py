import sys
import os
import asyncio
import pandas as pd
import logging
import qasync
from control.pandas import PandasModel
from control.workers import QThreadWorker
from dotenv import load_dotenv
from PyQt5.QtWidgets import QApplication, QMainWindow, QHeaderView
from PyQt5.QtCore import QSortFilterProxyModel, QTimer
from aiohttp import ClientSession
from api.api_gateio import GateioAPI
from ui.ui_main_window import Ui_MainWindow
from datetime import datetime

# Memuat variabel lingkungan dari file .env
load_dotenv()

# Konfigurasi logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Handler untuk logging ke file
file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.DEBUG)

# Handler untuk logging ke console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Format logging
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Menambahkan handler ke logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Inisialisasi API Gate.io
        self.api = GateioAPI()
        logger.debug("GateioAPI initialized")
        
        # Inisialisasi DataFrame dan model untuk tableView_marketdata
        self.data = pd.DataFrame(columns=["TIME", "PAIR", "24H %", "PRICE", "VOLUME"])
        self.model = PandasModel(self.data)
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        self.tableView_marketdata.setModel(self.proxy)
        self.tableView_marketdata.setSortingEnabled(True)
        self.tableView_marketdata.horizontalHeader().setSortIndicatorShown(True)
        self.tableView_marketdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableView_marketdata.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tableView_accountdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableView_accountdata.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.lineEdit_addpair.setPlaceholderText("e.g. BTC_USDT")
        logger.debug("TableView configured")

        # Inisialisasi pasangan default
        self.pairs = ['BTC_USDT', 'ETH_USDT']
        logger.debug(f"Pairs set: {self.pairs}")

        # Timer untuk pembaruan data
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.schedule_update)
        self.timer.start(15000)
        logger.debug("Timer started for data updates every 15 seconds")

        # Hubungkan sinyal returnPressed dari lineEdit_addpair ke metode add_pair
        self.lineEdit_addpair.returnPressed.connect(self.add_pair)
        self.worker = None
        self.show()

    def closeEvent(self, event):
        logger.debug("Closing application")
        if self.worker is not None:
            self.worker.stop()
            self.worker.quit()
            self.worker.wait()
        event.accept()

    def update_model(self, data_frame):
        logger.debug("Updating model with new data")
        self.model.update_data(data_frame)

    def schedule_update(self):
        logger.debug("Scheduling data update")
        if self.worker is not None:
            logger.debug("Stopping existing worker")
            self.worker.stop()
            self.worker.quit()
            self.worker.wait()
        logger.debug("Starting new worker")
        self.worker = QThreadWorker(self.pairs, self.api)
        self.worker.result_ready.connect(self.update_model)
        self.worker.start()

    def add_pair(self):
        pair = self.lineEdit_addpair.text().strip().upper()
        if pair and pair not in self.pairs:  # Pastikan pasangan tidak kosong dan belum ada di daftar
            logger.debug(f"Adding new pair: {pair}")
            # Tambahkan pasangan baru ke daftar pasangan
            self.pairs.append(pair)
            # Perbarui DataFrame dengan pasangan baru
            new_row = pd.DataFrame([[pd.Timestamp.now(), pair, None, None, None]], columns=self.data.columns)
            self.data = pd.concat([self.data, new_row], ignore_index=True)
            self.update_model(self.data)  # Perbarui model dengan data terbaru
            self.lineEdit_addpair.clear()
            logger.debug(f"Pair added: {pair}")

if __name__ == "__main__":
    app = qasync.QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    with loop:
        loop.run_forever()
