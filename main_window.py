import sys
import os
import asyncio
import pandas as pd
import qasync
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QHeaderView, QFileDialog, QProgressDialog, QMessageBox, QTableWidgetItem)
from PyQt5.QtCore import Qt
from dotenv import load_dotenv
from control.csv_handler import export_marketdata_to_csv, handle_import_csv
from control.logging_config import setup_logging
from ui.ui_main_window import Ui_MainWindow
import pygame
from control.data_handler import (init_market_data_model, init_account_data_model, init_workers, 
                          update_model_market, update_model_account, update_balance, 
                          add_pair, update_market_data_with_new_pairs, restart_worker, close_event)

# Memuat variabel lingkungan dari file .env
load_dotenv()

# Inisialisasi pygame mixer
pygame.mixer.init()

# Konfigurasi logging
logger = setup_logging('main_window.log')

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Inisialisasi API Gate.io dengan API key dan secret dari environment variables
        self.api_key = os.getenv('API_KEY')
        self.api_secret = os.getenv('SECRET_KEY')
        logger.debug("API keys initialized")

        # Inisialisasi daftar pasangan
        self.pairs = ["BTC_USDT", "ETH_USDT"]
        
        # Inisialisasi DataFrame dan model untuk tableView_marketdata
        self.data_market, self.proxy_model_market = init_market_data_model()
        self.tableView_marketdata.setModel(self.proxy_model_market)
        self.tableView_marketdata.setSortingEnabled(True)
        self.tableView_marketdata.horizontalHeader().setSortIndicatorShown(True)
        self.tableView_marketdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Inisialisasi DataFrame dan model untuk tableView_accountdata
        self.data_account, self.proxy_model_account = init_account_data_model()
        self.tableView_accountdata.setModel(self.proxy_model_account)
        self.tableView_accountdata.setSortingEnabled(True)
        self.tableView_accountdata.horizontalHeader().setSortIndicatorShown(True)
        self.tableView_accountdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Inisialisasi workers
        self.worker, self.balance_worker = init_workers(self.pairs, self.api_key, self.api_secret)
        self.worker.result_ready.connect(self.update_model_market)
        self.worker.start()

        self.balance_worker.balance_signal.connect(self.update_balance)
        self.balance_worker.start()

        # Menghubungkan signal dan slot
        self.init_signals()

    def init_signals(self):
        self.lineEdit_addpair.returnPressed.connect(self.add_pair)
        self.pushButton_export.clicked.connect(lambda: export_marketdata_to_csv(self.tableView_marketdata))
        self.pushButton_import.clicked.connect(self.import_pairs)

    def import_pairs(self):
        imported_pairs = handle_import_csv()
        if imported_pairs is not None:
            self.pairs = imported_pairs
            self.data_market = update_market_data_with_new_pairs(self.pairs, self.data_market, self.proxy_model_market)
            self.worker = restart_worker(self.worker, self.pairs, self.api_key, self.api_secret, self.update_model_market)
            QMessageBox.information(self, "Import Successful", "Pairs have been successfully imported.")

    def update_model_market(self, data_frame):
        self.data_market = update_model_market(data_frame, self.data_market, self.proxy_model_market)

    def update_model_account(self, data_frame):
        self.data_account = update_model_account(data_frame, self.data_account, self.proxy_model_account)

    def update_balance(self, balance):
        self.data_account = update_balance(balance, self.data_account, self.proxy_model_account)

    def add_pair(self):
        pair = self.lineEdit_addpair.text().strip().upper()
        if pair:
            self.pairs, self.data_market = add_pair(pair, self.pairs, self.data_market, self.proxy_model_market)
            self.lineEdit_addpair.clear()
            self.worker = restart_worker(self.worker, self.pairs, self.api_key, self.api_secret, self.update_model_market)

    def closeEvent(self, event):
        if close_event(self.worker, self.balance_worker):
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    app = qasync.QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = MainWindow()
    window.show()
    with loop:
        loop.run_forever()
