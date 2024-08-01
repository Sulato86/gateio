import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QHeaderView, QMessageBox, QMenu
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor, QBrush
from PyQt5.QtCore import Qt, QPoint
from control.logging_config import setup_logging
from ui.ui_main_window import Ui_MainWindow
from control.data_handler import DataHandler, TickerTableUpdater, CustomSortFilterProxyModel
from control.websocket_worker import WebSocketWorker
from control.http_worker import HTTPWorker

# Inisialisasi logger dengan file log terpisah
logger = setup_logging('main_window.log')

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, pairs=None):
        super().__init__()
        self.setupUi(self)

        # Inisialisasi DataHandler
        self.data_handler = DataHandler()
        self.data_handler.data_ready.connect(self.update_account_view)
        self.data_handler.pair_added.connect(self.add_pair_to_websocket)
        self.data_handler.pair_deleted.connect(self.remove_pair_from_websocket)

        # Inisialisasi HTTPWorker
        self.http_worker = HTTPWorker()
        self.http_worker.data_ready.connect(self.update_account_view)

        # Dictionary untuk melacak baris pasangan mata uang
        self.row_mapping = {}

        # Inisialisasi model untuk tableView_marketdata
        self.market_model = QStandardItemModel()
        self.market_model.setHorizontalHeaderLabels(['TIME', 'PAIR', '24%', 'PRICE', 'VOLUME(Base)'])

        # Inisialisasi custom proxy model untuk sorting
        self.proxy_model = CustomSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.market_model)
        self.tableView_marketdata.setModel(self.proxy_model)
        self.tableView_marketdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Mengaktifkan fitur sorting
        self.tableView_marketdata.setSortingEnabled(True)

        # Inisialisasi model untuk tableView_accountdata
        self.account_model = QStandardItemModel()
        self.account_model.setHorizontalHeaderLabels(['ASSET', 'FREE', 'LOCKED'])
        self.tableView_accountdata.setModel(self.account_model)
        self.tableView_accountdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Inisialisasi TickerTableUpdater
        self.ticker_updater = TickerTableUpdater(self.market_model, self.row_mapping)

        # Menjalankan thread websocket pada worker.py
        pairs = self.data_handler.load_pairs()
        self.websocket_thread = WebSocketWorker(pairs)
        self.websocket_thread.message_received.connect(self.ticker_updater.update_ticker_table)
        logger.info("Starting WebSocket thread")
        self.websocket_thread.start()

        # Memulai pengambilan saldo dengan HTTPWorker
        self.data_handler.fetch_balances(self.http_worker)

        # Hubungkan QLineEdit untuk input pasangan baru
        self.lineEdit_addpair.returnPressed.connect(self.add_pair)
        self.lineEdit_addpair.setPlaceholderText("e.g BTC_USDT")

        # Tampilkan pasangan mata uang yang sudah ada saat inisialisasi
        self.update_pairs_display(pairs)

        # Tambahkan event handler untuk klik pada tableView_marketdata
        self.tableView_marketdata.clicked.connect(self.handle_click)

        # Tambahkan event handler untuk klik kanan pada tableView_marketdata
        self.tableView_marketdata.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView_marketdata.customContextMenuRequested.connect(self.show_context_menu)

    def handle_click(self, index):
        self.clear_highlights()
        self.highlight_rows(index)

    def highlight_rows(self, index):
        value = self.proxy_model.data(index)
        column = index.column()
        for row in range(self.proxy_model.rowCount()):
            item = self.proxy_model.index(row, column)
            if self.proxy_model.data(item) == value:
                for col in range(self.proxy_model.columnCount()):
                    self.proxy_model.item(row, col).setBackground(QBrush(QColor("yellow")))

    def clear_highlights(self):
        for row in range(self.proxy_model.rowCount()):
            for col in range(self.proxy_model.columnCount()):
                self.proxy_model.item(row, col).setBackground(QBrush(QColor("white")))

    def show_context_menu(self, position: QPoint):
        index = self.tableView_marketdata.indexAt(position)
        if not index.isValid():
            logger.debug(f"Invalid index at position: {position}")
            return

        # Ambil indeks dari model sumber
        source_index = self.proxy_model.mapToSource(index)

        # Ambil pair dari baris yang diklik kanan
        pair = self.market_model.data(self.market_model.index(source_index.row(), 1))  # Asumsikan kolom 1 adalah pasangan mata uang

        logger.debug(f"Context menu requested at position: {position}, index: {index.row()}, source index: {source_index.row()}, pair: {pair}")

        # Buat menu konteks
        menu = QMenu()
        delete_action = menu.addAction(f"Delete {pair}")
        action = menu.exec_(self.tableView_marketdata.viewport().mapToGlobal(position))
        
        if action == delete_action:
            logger.debug(f"Delete action selected for pair: {pair} at index: {index.row()}, source index: {source_index.row()}")
            self.delete_row_by_value(source_index, pair)

    def delete_row_by_value(self, index, pair):
        # Konfirmasi penghapusan
        confirmation = QMessageBox.question(self, "Delete Pair", f"Are you sure you want to delete the pair {pair}?", QMessageBox.Yes | QMessageBox.No)
        if confirmation == QMessageBox.Yes:
            try:
                logger.debug(f"Deleting row at index: {index.row()} with pair: {pair}")
                self.data_handler.delete_rows_by_column_value(self.market_model, index.column(), pair)
                self.data_handler.delete_pair_from_db(pair)
                self.remove_pair_from_websocket(pair)  # Panggil fungsi untuk unsubscribe
                self.proxy_model.invalidate()
                self.update_pairs_display()
            except Exception as e:
                logger.error(f"Failed to delete pair: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete pair {pair}. Please try again.")

    def add_pair(self):
        pair = self.lineEdit_addpair.text().upper()
        if pair and pair not in self.websocket_thread.gateio_ws.pairs:
            if self.data_handler.validate_pair(self.http_worker, pair):
                try:
                    logger.info(f"Adding pair: {pair}")
                    self.data_handler.add_pair_to_db(pair)
                    self.lineEdit_addpair.clear()
                    self.update_pairs_display()
                except Exception as e:
                    logger.error(f"Failed to add pair: {e}")
                    QMessageBox.critical(self, "Error", f"Failed to add pair {pair}. Please try again.")
            else:
                QMessageBox.warning(self, "Invalid Pair", f"The pair {pair} does not exist on Gate.io.")
                logger.info(f"Pair {pair} does not exist on Gate.io.")
        else:
            QMessageBox.warning(self, "Invalid Pair", f"The pair {pair} already exists or is invalid.")
            logger.info(f"Pair {pair} already exists or is invalid.")

    def update_pairs_display(self, pairs=None):
        if pairs is None:
            pairs = self.data_handler.load_pairs()

        self.market_model.removeRows(0, self.market_model.rowCount())
        self.row_mapping.clear()

        for pair in pairs:
            if pair not in self.row_mapping:
                row_index = self.market_model.rowCount()
                self.row_mapping[pair] = row_index
                self.market_model.appendRow([
                    QStandardItem(""), 
                    QStandardItem(pair), 
                    QStandardItem(""), 
                    QStandardItem(""), 
                    QStandardItem("")
                ])
                logger.info(f"Added pair {pair} to tableView_marketdata at row {row_index}")

    def add_pair_to_websocket(self, pair):
        self.websocket_thread.add_pair(pair)

    def remove_pair_from_websocket(self, pair):
        self.websocket_thread.remove_pair(pair)

    def update_market_data(self, data):
        logger.debug(f"Market data updated: {data}")

    def update_account_view(self, account_model):
        logger.info("Updating account view with new data.")
        self.tableView_accountdata.setModel(account_model)

    def closeEvent(self, event):
        self.data_handler.conn.close()
        self.websocket_thread.stop()
        self.websocket_thread.wait()
        event.accept()

if __name__ == "__main__":
    logger.info("Starting application")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

    logging.shutdown()
