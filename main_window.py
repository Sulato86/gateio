import sys
import os
import asyncio
import pandas as pd
import logging
import qasync
from control.pandasa import PandasModel
from control.workers import QThreadWorker, BalanceWorker
from dotenv import load_dotenv
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QHeaderView
from PyQt5.QtCore import QSortFilterProxyModel, QTimer, Qt
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
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levellevelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Menambahkan handler ke logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

class CustomSortFilterProxyModel(QSortFilterProxyModel):
    def lessThan(self, left, right):
        left_data = self.sourceModel().data(left)
        right_data = self.sourceModel().data(right)
        if left.column() != 0:  # Assuming 0 is the column index for TIME
            left_data = float(left_data)
            right_data = float(right_data)
        return left_data < right_data

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Inisialisasi API Gate.io dengan API key dan secret dari environment variables
        self.api_key = os.getenv('API_KEY')
        self.api_secret = os.getenv('SECRET_KEY')
        self.api = GateioAPI(self.api_key, self.api_secret)
        logger.debug("GateioAPI initialized")

        # Inisialisasi daftar pasangan
        self.pairs = ["BTC_USDT", "ETH_USDT", "LTC_USDT", "XRP_USDT", "EOS_USDT", "BCH_USDT", "TRX_USDT", "ETC_USDT"]
        
        # Inisialisasi DataFrame dan model untuk tableView_marketdata
        self.data_market = pd.DataFrame(columns=["TIME", "PAIR", "24H %", "PRICE", "VOLUME"])

        # Menggunakan CustomSortFilterProxyModel untuk sorting
        self.proxy_model_market = CustomSortFilterProxyModel(self)
        self.proxy_model_market.setSourceModel(PandasModel(self.data_market))
        self.proxy_model_market.setSortRole(Qt.DisplayRole)
        
        self.tableView_marketdata.setModel(self.proxy_model_market)
        self.tableView_marketdata.setSortingEnabled(True)
        self.tableView_marketdata.horizontalHeader().setSortIndicatorShown(True)
        self.tableView_marketdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Inisialisasi DataFrame dan model untuk tableView_accountdata
        self.data_account = pd.DataFrame(columns=["CURRENCY", "AVAILABLE"])
        
        # Menggunakan CustomSortFilterProxyModel untuk sorting pada tableView_accountdata
        self.proxy_model_account = CustomSortFilterProxyModel(self)
        self.proxy_model_account.setSourceModel(PandasModel(self.data_account))
        self.proxy_model_account.setSortRole(Qt.DisplayRole)
        
        self.tableView_accountdata.setModel(self.proxy_model_account)
        self.tableView_accountdata.setSortingEnabled(True)
        self.tableView_accountdata.horizontalHeader().setSortIndicatorShown(True)
        self.tableView_accountdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Inisialisasi QThreadWorker untuk update data
        self.worker = None
        self.balance_worker = None  # Inisialisasi BalanceWorker
        self.schedule_update()

        # Menggunakan QTimer untuk update berkala
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.schedule_update)
        self.timer.start(10000)  # Update setiap 60 detik

        # Menghubungkan lineEdit_addpair dengan fungsi add_pair ketika ENTER ditekan
        self.lineEdit_addpair.returnPressed.connect(self.add_pair)

    def update_model_market(self, data_frame):
        logger.debug("Updating market model with new data")
        for column in ["24H %", "PRICE", "VOLUME"]:
            data_frame[column] = data_frame[column].astype(float)
        self.data_market = data_frame
        self.proxy_model_market.setSourceModel(PandasModel(self.data_market))

    def update_model_account(self, data_frame):
        logger.debug("Updating account model with new data")
        logger.debug(f"Account DataFrame:\n{data_frame}")
        self.data_account = data_frame
        self.proxy_model_account.setSourceModel(PandasModel(self.data_account))
        logger.debug("Account model updated.")

    def schedule_update(self):
        logger.debug("Scheduling data update")
        if self.worker is not None:
            logger.debug("Stopping existing worker")
            self.worker.stop()
            self.worker.quit()
            self.worker.wait()
        logger.debug("Starting new worker")
        self.worker = QThreadWorker(self.pairs, self.api_key, self.api_secret)
        self.worker.result_ready.connect(self.update_model_market)
        self.worker.start()

        # Mulai BalanceWorker untuk mendapatkan saldo akun
        if self.balance_worker is not None:
            logger.debug("Stopping existing balance worker")
            self.balance_worker.quit()
            self.balance_worker.wait()
        logger.debug("Starting new balance worker")
        self.balance_worker = BalanceWorker(self.api_key, self.api_secret)
        self.balance_worker.balance_signal.connect(self.update_balance)
        self.balance_worker.start()

    def update_balance(self, balance):
        logger.debug("Update balance called.")
        if 'error' in balance:
            logger.error(f"Error: {balance['message']}")
        else:
            data = [{"CURRENCY": currency, "AVAILABLE": available} for currency, available in balance.items()]
            df = pd.DataFrame(data)
            logger.debug(f"Balance DataFrame:\n{df}")
            self.update_model_account(df)
            logger.debug("Account balance updated")

    def add_pair(self):
        pair = self.lineEdit_addpair.text().strip().upper()
        if pair and pair not in self.pairs:
            logger.debug(f"Adding new pair: {pair}")
            self.pairs.append(pair)
            new_row = pd.DataFrame([[pd.Timestamp.now(), pair, None, None, None]], columns=self.data_market.columns)
            self.data_market = pd.concat([self.data_market, new_row], ignore_index=True)
            self.proxy_model_market.setSourceModel(PandasModel(self.data_market))
            self.lineEdit_addpair.clear()
            logger.debug(f"Pair added: {pair}")

    def some_function(self):
        # Placeholder function for other UI elements
        logger.debug("Some function called")

if __name__ == "__main__":
    app = qasync.QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    with loop:
        loop.run_forever()
