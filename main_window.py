import sys
import os
import asyncio
import pandas as pd
import qasync
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QHeaderView, 
                             QFileDialog, QProgressDialog, QMessageBox, QTableWidgetItem)
from PyQt5.QtCore import Qt
from dotenv import load_dotenv
from control.pandasa import PandasModel, CustomSortFilterProxyModel
from control.workers import QThreadWorker, BalanceWorker
from control.csv_handler import export_marketdata_to_csv, handle_import_csv
from control.logging_config import setup_logging
from ui.ui_main_window import Ui_MainWindow
import pygame

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
        self.init_market_data_model()

        # Inisialisasi DataFrame dan model untuk tableView_accountdata
        self.init_account_data_model()

        # Inisialisasi workers
        self.init_workers()

        # Menghubungkan signal dan slot
        self.init_signals()

    def init_market_data_model(self):
        self.data_market = pd.DataFrame(columns=["TIME", "PAIR", "24H %", "PRICE", "VOLUME"])
        self.proxy_model_market = CustomSortFilterProxyModel(self)
        self.proxy_model_market.setSourceModel(PandasModel(self.data_market))
        self.proxy_model_market.setSortRole(Qt.DisplayRole)
        self.tableView_marketdata.setModel(self.proxy_model_market)
        self.tableView_marketdata.setSortingEnabled(True)
        self.tableView_marketdata.horizontalHeader().setSortIndicatorShown(True)
        self.tableView_marketdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def init_account_data_model(self):
        self.data_account = pd.DataFrame(columns=["CURRENCY", "AVAILABLE"])
        self.proxy_model_account = CustomSortFilterProxyModel(self)
        self.proxy_model_account.setSourceModel(PandasModel(self.data_account))
        self.proxy_model_account.setSortRole(Qt.DisplayRole)
        self.tableView_accountdata.setModel(self.proxy_model_account)
        self.tableView_accountdata.setSortingEnabled(True)
        self.tableView_accountdata.horizontalHeader().setSortIndicatorShown(True)
        self.tableView_accountdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def init_workers(self):
        self.worker = QThreadWorker(self.pairs, self.api_key, self.api_secret)
        self.worker.result_ready.connect(self.update_model_market)
        self.worker.start()

        self.balance_worker = BalanceWorker(self.api_key, self.api_secret)
        self.balance_worker.balance_signal.connect(self.update_balance)
        self.balance_worker.start()

    def init_signals(self):
        self.lineEdit_addpair.returnPressed.connect(self.add_pair)
        self.pushButton_export.clicked.connect(lambda: export_marketdata_to_csv(self.tableView_marketdata))
        self.pushButton_import.clicked.connect(self.import_pairs)

    def import_pairs(self):
        imported_pairs = handle_import_csv()
        if imported_pairs is not None:
            self.pairs = imported_pairs
            self.update_market_data_with_new_pairs()
            self.restart_worker()
            QMessageBox.information(self, "Import Successful", "Pairs have been successfully imported.")

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
            self.restart_worker()

    def update_market_data_with_new_pairs(self):
        self.data_market = pd.DataFrame(columns=["TIME", "PAIR", "24H %", "PRICE", "VOLUME"])
        for pair in self.pairs:
            new_row = pd.DataFrame([[pd.Timestamp.now(), pair, None, None, None]], columns=self.data_market.columns)
            self.data_market = pd.concat([self.data_market, new_row], ignore_index=True)
        self.proxy_model_market.setSourceModel(PandasModel(self.data_market))
        self.tableView_marketdata.resizeColumnsToContents()
        self.tableView_marketdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        logger.debug("Market data updated with new pairs")

    def restart_worker(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()

        self.worker = QThreadWorker(self.pairs, self.api_key, self.api_secret)
        self.worker.result_ready.connect(self.update_model_market)
        self.worker.start()
        logger.debug("Worker restarted with updated pairs")

    def closeEvent(self, event):
        try:
            logger.debug("closeEvent triggered")
            if hasattr(self, 'worker'):
                logger.debug("Stopping QThreadWorker")
                self.worker.stop()
                if not self.worker.wait(5000):
                    logger.debug("QThreadWorker not stopping, terminating")
                    self.worker.terminate()
            
            if hasattr(self, 'balance_worker'):
                logger.debug("Stopping BalanceWorker")
                self.balance_worker.stop()
                if not self.balance_worker.wait(5000):
                    logger.debug("BalanceWorker not stopping, terminating")
                    self.balance_worker.terminate()

            logger.debug("Closing application")
            event.accept()
            logger.info("Application closed cleanly")
        except Exception as e:
            logger.error(f"Error during closeEvent: {e}")
            event.ignore()

if __name__ == "__main__":
    app = qasync.QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = MainWindow()
    window.show()
    with loop:
        loop.run_forever()
