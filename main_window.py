import sys
import os
import asyncio
import pandas as pd
import qasync
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QHeaderView, QFileDialog, QProgressDialog, QMessageBox, QTableWidgetItem, QMenu, QDialog)
from PyQt5.QtCore import Qt, QModelIndex, QMutex
from dotenv import load_dotenv
from control.csv_handler import export_marketdata_to_csv, handle_import_csv
from control.logging_config import setup_logging
from ui.ui_main_window import Ui_MainWindow
import pygame
from control.data_handler import (init_market_data_model, init_account_data_model, init_workers, 
                          update_model_market, update_model_account, update_balance, 
                          add_pair, update_market_data_with_new_pairs, restart_worker, close_event, 
                          delete_market_rows, delete_account_rows)
from control.worker import Worker
from control.login_dialog import LoginDialog
from PyQt5.QtGui import QBrush, QColor, QPalette
from PyQt5.QtWidgets import QStyledItemDelegate

# Memuat variabel lingkungan dari file .env
load_dotenv()

# Inisialisasi pygame mixer
pygame.mixer.init()

# Konfigurasi logging
logger = setup_logging('main_window.log')

# Inisialisasi mutex
mutex = QMutex()

class TableColorDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(TableColorDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        self.initStyleOption(option, index)  # Menginisialisasi opsi gaya
        
        value = index.model().data(index, Qt.DisplayRole)
        
        # Asumsikan kolom '24H %' berada pada indeks 2
        column_index = 2
        if index.column() == column_index:
            try:
                value = float(value)
            except (ValueError, AttributeError):
                value = 0

            if value < 0:
                option.backgroundBrush = QBrush(QColor(255, 0, 0))
                textColor = QColor(255, 255, 255)
                print(f"Row {index.row()} is red with value {value}")
            elif value > 0:
                option.backgroundBrush = QBrush(QColor(0, 128, 0))
                textColor = QColor(255, 255, 255)
                print(f"Row {index.row()} is green with value {value}")
            else:
                textColor = option.palette.color(QPalette.Text)  # Default text color
        
            painter.save()
            painter.fillRect(option.rect, option.backgroundBrush)  # Mengisi latar belakang
            painter.setPen(textColor)  # Mengatur warna teks
            
            # Menggambar teks
            textRect = option.rect
            painter.drawText(textRect, Qt.AlignCenter, str(value))
            painter.restore()
        else:
            super(TableColorDelegate, self).paint(painter, option, index)

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, worker):
        super().__init__()
        self.setupUi(self)
        self.worker = worker

        # Dapatkan instance API dari worker
        self.api = self.worker.get_api_instance()

        # Inisialisasi atribut self.pairs tanpa nilai default
        self.pairs = []

        # Inisialisasi DataFrame dan model untuk tableView_marketdata
        self.data_market, self.proxy_model_market = init_market_data_model()
        self.tableView_marketdata.setModel(self.proxy_model_market)
        self.tableView_marketdata.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.tableView_marketdata.setSelectionMode(QtWidgets.QTableView.ExtendedSelection)
        self.tableView_marketdata.setSortingEnabled(True)
        self.tableView_marketdata.horizontalHeader().setSortIndicatorShown(True)
        self.tableView_marketdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Set delegate untuk pewarnaan baris pada tableView_marketdata
        self.tableView_marketdata.setItemDelegate(TableColorDelegate(self.tableView_marketdata))

        # Inisialisasi DataFrame dan model untuk tableView_accountdata
        self.data_account, self.proxy_model_account = init_account_data_model()
        self.tableView_accountdata.setModel(self.proxy_model_account)
        self.tableView_accountdata.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.tableView_accountdata.setSelectionMode(QtWidgets.QTableView.ExtendedSelection)
        self.tableView_accountdata.setSortingEnabled(True)
        self.tableView_accountdata.horizontalHeader().setSortIndicatorShown(True)
        self.tableView_accountdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Menghubungkan signal dan slot
        self.init_signals()

        # Tambahkan menu konteks untuk tabel
        self.tableView_marketdata.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView_marketdata.customContextMenuRequested.connect(self.show_context_menu_market)

        # Inisialisasi worker
        self.init_workers()

    def init_workers(self):
        # Inisialisasi workers dengan api_key dan api_secret dari worker
        self.worker, self.balance_worker = init_workers(self.pairs, self.api.api_key, self.api.secret_key)
        self.worker.result_ready.connect(self.update_model_market)
        self.worker.start()
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
            self.data_market = update_market_data_with_new_pairs(self.pairs, self.data_market, self.proxy_model_market)
            self.worker = restart_worker(self.worker, self.pairs, self.api, self.update_model_market)
            QMessageBox.information(self, "Import Successful", "Pairs have been successfully imported.")

    def update_model_market(self, data_frame):
        self.data_market = update_model_market(data_frame, self.data_market, self.proxy_model_market)
        self.proxy_model_market.layoutChanged.emit()  # Emit layoutChanged signal
        logger.debug(f"Updated pairs after deletion: {self.pairs}")

    def update_model_account(self, data_frame):
        self.data_account = update_model_account(data_frame, self.data_account, self.proxy_model_account)
        self.proxy_model_account.layoutChanged.emit()  # Emit layoutChanged signal

    def update_balance(self, balance):
        self.data_account = update_balance(balance, self.data_account, self.proxy_model_account)
        self.proxy_model_account.layoutChanged.emit()  # Emit layoutChanged signal

    def add_pair(self):
        pair = self.lineEdit_addpair.text().strip().upper()
        if pair:
            self.pairs, self.data_market = add_pair(pair, self.pairs, self.data_market, self.proxy_model_market)
            self.lineEdit_addpair.clear()
            self.worker = restart_worker(self.worker, self.pairs, self.api, self.update_model_market)

    def show_context_menu_market(self, position):
        logger.debug("Context menu requested for market data")
        indexes = self.tableView_marketdata.selectionModel().selectedRows()
        logger.debug(f"Selected indexes: {indexes}")
        if indexes:
            context_menu = QMenu(self)
            delete_action = context_menu.addAction("Delete Row(s)")
            delete_action.triggered.connect(lambda: self.delete_selected_rows(self.tableView_marketdata, self.data_market, self.proxy_model_market))
            context_menu.exec_(self.tableView_marketdata.viewport().mapToGlobal(position))

    def show_context_menu_account(self, position):
        logger.debug("Context menu requested for account data")
        indexes = self.tableView_accountdata.selectionModel().selectedRows()
        logger.debug(f"Selected indexes: {indexes}")
        if indexes:
            context_menu = QMenu(self)
            delete_action = context_menu.addAction("Delete Row(s)")
            delete_action.triggered.connect(lambda: self.delete_selected_rows(self.tableView_accountdata, self.data_account, self.proxy_model_account))
            context_menu.exec_(self.tableView_accountdata.viewport().mapToGlobal(position))

    def delete_selected_rows(self, tableView, data_model, proxy_model):
        indexes = tableView.selectionModel().selectedRows()
        logger.debug(f"Selected indexes: {indexes}")

        if indexes:
            # Terjemahkan indeks tampilan ke indeks model
            model_indices = [proxy_model.mapToSource(index) for index in indexes]
            original_indices = [model_index.row() for model_index in model_indices]
            logger.debug(f"Original indices to be deleted: {original_indices}")

            # Hentikan worker sementara
            if tableView == self.tableView_marketdata:
                if self.worker and self.worker.isRunning():
                    self.worker.stop()
                    self.worker.wait()
                mutex.lock()
                try:
                    self.data_market = delete_market_rows(original_indices, self.data_market, self.proxy_model_market)
                    # Perbarui self.pairs dengan pasangan yang tersisa setelah penghapusan
                    self.pairs = self.data_market['PAIR'].tolist()
                    logger.debug(f"Updated pairs after deletion: {self.pairs}")
                finally:
                    mutex.unlock()
                # Mulai kembali worker setelah penghapusan
                self.worker = restart_worker(self.worker, self.pairs, self.api, self.update_model_market)

            elif tableView == self.tableView_accountdata:
                if self.balance_worker.isRunning():
                    self.balance_worker.stop()
                    self.balance_worker.wait()
                mutex.lock()
                try:
                    self.data_account = delete_account_rows(original_indices, self.data_account, self.proxy_model_account)
                finally:
                    mutex.unlock()
                # Mulai kembali worker setelah penghapusan
                self.balance_worker.start()

            tableView.clearSelection()
            proxy_model.layoutChanged.emit()  # Emit layoutChanged signal

    def closeEvent(self, event):
        if close_event(self.worker, self.balance_worker):
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    app = qasync.QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Inisialisasi worker
    worker = Worker()

    # Tampilkan dialog login sebelum main window
    login_dialog = LoginDialog(worker)
    if login_dialog.exec_() == QDialog.Accepted:
        window = MainWindow(worker)
        window.show()
    else:
        sys.exit(0)

    with loop:
        loop.run_forever()
