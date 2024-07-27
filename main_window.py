import sys
import os
import asyncio
import pandas as pd
import qasync
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QHeaderView, QFileDialog, QProgressDialog, QMessageBox, QTableWidgetItem
from PyQt5.QtCore import Qt
from dotenv import load_dotenv
from control.pandasa import PandasModel, CustomSortFilterProxyModel
from control.workers import QThreadWorker, BalanceWorker
from control.csv_handler import export_marketdata_to_csv, export_notifprice_to_csv, handle_import_csv, handle_import_notifprice_csv
from control.logging_config import setup_logging  # Import setup_logging
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
        self.data_market = pd.DataFrame(columns=["TIME", "PAIR", "24H %", "PRICE", "VOLUME"])

        # Menggunakan CustomSortFilterProxyModel untuk sorting pada tableView_marketdata
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

        # Inisialisasi DataFrame dan model untuk tableView_notifprice
        self.data_notifprice = pd.DataFrame(columns=["PAIR", "PRICE"])
        self.notifprice_model = PandasModel(self.data_notifprice)
        self.tableView_notifprice.setModel(self.notifprice_model)

        # Inisialisasi QThreadWorker untuk update data
        self.worker = QThreadWorker(self.pairs, self.api_key, self.api_secret)
        self.worker.result_ready.connect(self.update_model_market)
        self.worker.price_check_signal.connect(self.check_price_and_notify)
        self.worker.start()

        # Inisialisasi BalanceWorker untuk update saldo akun
        self.balance_worker = BalanceWorker(self.api_key, self.api_secret)
        self.balance_worker.balance_signal.connect(self.update_balance)
        self.balance_worker.start()

        # Menghubungkan lineEdit_addpair dengan fungsi add_pair ketika ENTER ditekan
        self.lineEdit_addpair.returnPressed.connect(self.add_pair)
        
        ######################
        self.lineEdit_minprice.returnPressed.connect(self.add_pair)
        # Menghubungkan tombol pushButton_export ke fungsi export_marketdata_to_csv
        self.pushButton_export.clicked.connect(lambda: export_marketdata_to_csv(self.tableView_marketdata))
        
        # Menghubungkan tombol pushButton_import ke fungsi handle_import_csv
        self.pushButton_import.clicked.connect(self.import_pairs)

        # Inisialisasi untuk notifikasi harga
        self.pushButton_minprice.clicked.connect(self.handle_pushButton_minprice)
        self.pushButton_exportminprice.clicked.connect(lambda: export_notifprice_to_csv(self.tableView_notifprice))
        self.pushButton_importminprice.clicked.connect(self.import_notifprice)

        # Panggil initialize_combobox_minprice saat inisialisasi
        self.initialize_combobox_minprice()

    def initialize_combobox_minprice(self):
        current_items = set(self.comboBox_minprice.itemText(i) for i in range(self.comboBox_minprice.count()))
        model = self.tableView_marketdata.model()
        if model is not None:
            pairs = [model.index(row, 1).data() for row in range(model.rowCount())]
            for pair in pairs:
                if pair not in current_items:
                    self.comboBox_minprice.addItem(pair)

    def handle_pushButton_minprice(self):
        pair = self.comboBox_minprice.currentText()
        price = self.lineEdit_minprice.text()
        
        if not price.replace('.', '', 1).isdigit():
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number for the price.")
            return

        # Update DataFrame data_notifprice
        new_row = pd.DataFrame([[pair, price]], columns=self.data_notifprice.columns)
        self.data_notifprice = pd.concat([self.data_notifprice, new_row], ignore_index=True)

        # Update model notifprice_model
        self.notifprice_model.update_data(self.data_notifprice)
        self.tableView_notifprice.setModel(self.notifprice_model)

    def check_price_and_notify(self, data):
        pair = data['pair']
        current_price = float(data['price'])
        
        model = self.tableView_notifprice.model()
        if model is None:
            return

        for row in range(model.rowCount()):
            notif_pair = model.index(row, 0).data()
            target_price = float(model.index(row, 1).data())
            
            if notif_pair == pair and current_price <= target_price:
                self.play_notification_sound()  # Implementasikan fungsi ini untuk memutar suara notifikasi
                QMessageBox.information(self, "Price Alert", f"The price for {pair} has reached {current_price}")

    def play_notification_sound(self):
        try:
            pygame.mixer.music.load('source/mandalorian-guitar.mp3')  # Ganti dengan path file mp3 Anda
            pygame.mixer.music.play()
            logger.debug("Playing notification sound")
        except Exception as e:
            logger.error(f"Error playing notification sound: {e}")

    def import_pairs(self):
        imported_pairs = handle_import_csv()
        if imported_pairs is not None:
            self.pairs = imported_pairs
            self.update_market_data_with_new_pairs()
            self.restart_worker()
            QMessageBox.information(self, "Import Successful", "Pairs have been successfully imported.")

    def import_notifprice(self):
        imported_data = handle_import_notifprice_csv()
        if imported_data is not None:
            valid_pairs = [self.tableView_marketdata.model().index(row, 1).data() for row in range(self.tableView_marketdata.model().rowCount())]
            self.data_notifprice = pd.DataFrame(columns=["PAIR", "PRICE"])  # Bersihkan data sebelumnya

            for pair, price in imported_data.items():
                if pair in valid_pairs:
                    new_row = pd.DataFrame([[pair, price]], columns=self.data_notifprice.columns)
                    self.data_notifprice = pd.concat([self.data_notifprice, new_row], ignore_index=True)
                else:
                    QMessageBox.warning(self, "Invalid Data", f"Pair {pair} is not valid.")
            
            self.notifprice_model.update_data(self.data_notifprice)
            self.tableView_notifprice.setModel(self.notifprice_model)
            QMessageBox.information(self, "Import Successful", "Notification prices have been successfully imported.")

    def update_model_market(self, data_frame):
        logger.debug("Updating market model with new data")
        for column in ["24H %", "PRICE", "VOLUME"]:
            data_frame[column] = data_frame[column].astype(float)
        self.data_market = data_frame
        self.proxy_model_market.setSourceModel(PandasModel(self.data_market))
        self.initialize_combobox_minprice()  # Panggil lagi untuk memperbarui comboBox_minprice dengan data terbaru

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
            # Restart worker to include the new pair
            self.restart_worker()

    def update_market_data_with_new_pairs(self):
        # Bersihkan data sebelumnya
        self.data_market = pd.DataFrame(columns=["TIME", "PAIR", "24H %", "PRICE", "VOLUME"])
        
        # Tambahkan data baru berdasarkan pasangan yang diperbarui
        for pair in self.pairs:
            new_row = pd.DataFrame([[pd.Timestamp.now(), pair, None, None, None]], columns=self.data_market.columns)
            self.data_market = pd.concat([self.data_market, new_row], ignore_index=True)
        
        self.proxy_model_market.setSourceModel(PandasModel(self.data_market))
        self.tableView_marketdata.resizeColumnsToContents()
        self.tableView_marketdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        logger.debug("Market data updated with new pairs")
        self.initialize_combobox_minprice()  # Panggil lagi untuk memperbarui comboBox_minprice dengan data terbaru

    def restart_worker(self):
        # Hentikan worker jika sedang berjalan
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        
        # Inisialisasi ulang worker dengan pasangan yang diperbarui
        self.worker = QThreadWorker(self.pairs, self.api_key, self.api_secret)
        self.worker.result_ready.connect(self.update_model_market)
        self.worker.price_check_signal.connect(self.check_price_and_notify)
        self.worker.start()
        logger.debug("Worker restarted with updated pairs")

    def closeEvent(self, event):
        try:
            logger.debug("closeEvent triggered")
            
            # Hentikan QThreadWorker
            if hasattr(self, 'worker'):
                logger.debug("Stopping QThreadWorker")
                self.worker.stop()
                if not self.worker.wait(5000):  # Tunggu maksimal 5 detik
                    logger.debug("QThreadWorker not stopping, terminating")
                    self.worker.terminate()
            
            # Hentikan BalanceWorker
            if hasattr(self, 'balance_worker'):
                logger.debug("Stopping BalanceWorker")
                self.balance_worker.stop()
                if not self.balance_worker.wait(5000):  # Tunggu maksimal 5 detik
                    logger.debug("BalanceWorker not stopping, terminating")
                    self.balance_worker.terminate()

            # Tutup aplikasi
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
