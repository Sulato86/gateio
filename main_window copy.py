import sys
import os
import asyncio
import pandas as pd
import logging
import qasync
from control.pandas import PandasModel  # Pastikan impor dari pandas_model.py
from control.workers import QThreadWorker, BalanceWorker  # Pastikan import BalanceWorker
from dotenv import load_dotenv
from PyQt5 import QtCore, QtWidgets  # Tambahkan QtCore untuk Geometry
from PyQt5.QtWidgets import QApplication, QMainWindow, QHeaderView
from PyQt5.QtCore import QSortFilterProxyModel, QTimer
from api.api_gateio import GateioAPI
from ui.ui_main_window import Ui_MainWindow

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
formatter = logging.Formatter('%(asctime)s - %(name)s - %(level)s - %(message)s')
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

        # Inisialisasi daftar pasangan
        self.pairs = ["BTC_USDT", "ETH_USDT", "LTC_USDT", "XRP_USDT", "EOS_USDT", "BCH_USDT", "TRX_USDT", "ETC_USDT"]
        
        # Inisialisasi DataFrame dan model untuk tableView_marketdata
        self.data_market = pd.DataFrame(columns=["TIME", "PAIR", "24H %", "PRICE", "VOLUME"])
        self.model_market = PandasModel(self.data_market)
        self.proxy_market = QSortFilterProxyModel()
        self.proxy_market.setSourceModel(self.model_market)
        self.tableView_marketdata.setModel(self.proxy_market)
        self.tableView_marketdata.setSortingEnabled(True)
        self.tableView_marketdata.horizontalHeader().setSortIndicatorShown(True)
        self.tableView_marketdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableView_marketdata.verticalHeader().setVisible(False)
        logger.debug("TableView for market data initialized")

        # Inisialisasi DataFrame dan model untuk tableView_accountdata
        self.data_account = pd.DataFrame(columns=["CURRENCY", "AVAILABLE"])
        self.model_account = PandasModel(self.data_account)
        self.proxy_account = QSortFilterProxyModel()
        self.proxy_account.setSourceModel(self.model_account)
        self.tableView_accountdata.setModel(self.proxy_account)
        self.tableView_accountdata.setSortingEnabled(True)
        self.tableView_accountdata.horizontalHeader().setSortIndicatorShown(True)
        self.tableView_accountdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableView_accountdata.verticalHeader().setVisible(False)
        logger.debug("TableView for account data initialized")

        # Inisialisasi saldo akun
        self.balance_worker = BalanceWorker()
        self.balance_worker.balance_signal.connect(self.update_balance)
        self.balance_worker.start()

        # Inisialisasi timer untuk memperbarui data pasar
        self.timer = QTimer()
        self.timer.timeout.connect(self.schedule_update)
        self.timer.start(10000)  # Update setiap 10 detik
        logger.debug("Update timer initialized")

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
        if self.balance_worker is not None:
            self.balance_worker.quit()
            self.balance_worker.wait()
        event.accept()

    def update_model_market(self, data_frame):
        logger.debug("Updating market model with new data")
        self.model_market.update_data(data_frame)

    def update_model_account(self, data_frame):
        logger.debug("Updating account model with new data")
        self.model_account.update_data(data_frame)

    def schedule_update(self):
        logger.debug("Scheduling data update")
        if self.worker is not None:
            logger.debug("Stopping existing worker")
            self.worker.stop()
            self.worker.quit()
            self.worker.wait()
        logger.debug("Starting new worker")
        self.worker = QThreadWorker(self.pairs, self.api)
        self.worker.result_ready.connect(self.update_model_market)
        self.worker.start()

    def update_balance(self, balance):
        if 'error' in balance:
            logger.error(f"Error: {balance['message']}")
        else:
            data = [{"CURRENCY": currency, "AVAILABLE": balance} for currency, balance in balance.items()]
            df = pd.DataFrame(data)
            self.update_model_account(df)
            logger.debug("Account balance updated")

    def add_pair(self):
        pair = self.lineEdit_addpair.text().strip().upper()
        if pair and pair not in self.pairs:  # Pastikan pasangan tidak kosong dan belum ada di daftar
            logger.debug(f"Adding new pair: {pair}")
            # Tambahkan pasangan baru ke daftar pasangan
            self.pairs.append(pair)
            # Perbarui DataFrame dengan pasangan baru
            new_row = pd.DataFrame([[pd.Timestamp.now(), pair, None, None, None]], columns=self.data_market.columns)
            self.data_market = pd.concat([self.data_market, new_row], ignore_index=True)
            self.update_model_market(self.data_market)  # Perbarui model dengan data terbaru
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
