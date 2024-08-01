import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QHeaderView, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
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

    def add_pair(self):
        """Menambahkan pasangan mata uang baru ke database dan WebSocket."""
        pair = self.lineEdit_addpair.text().upper()
        if pair and pair not in self.websocket_thread.gateio_ws.pairs:
            if self.data_handler.validate_pair(self.http_worker, pair):
                logger.info(f"Adding pair: {pair}")
                self.data_handler.add_pair_to_db(pair)
                self.lineEdit_addpair.clear()
                self.restart_websocket_worker()
            else:
                QMessageBox.warning(self, "Invalid Pair", f"The pair {pair} does not exist on Gate.io.")
                logger.info(f"Pair {pair} does not exist on Gate.io.")
        else:
            QMessageBox.warning(self, "Invalid Pair", f"The pair {pair} already exists or is invalid.")
            logger.info(f"Pair {pair} already exists or is invalid.")

    def update_pairs_display(self, pairs=None):
        """Memperbarui tampilan pasangan mata uang di tableView_marketdata."""
        if pairs is None:
            pairs = self.websocket_thread.gateio_ws.pairs

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

    def update_market_data(self, data):
        """Meng-update data pasar (market data) di tableView_marketdata."""
        logger.debug(f"Market data updated: {data}")

    def update_account_view(self, account_model):
        """Meng-update tampilan data akun di tableView_accountdata."""
        logger.info("Updating account view with new data.")
        self.tableView_accountdata.setModel(account_model)

    def restart_websocket_worker(self):
        """Merestart ulang WebSocket worker dengan pasangan mata uang baru."""
        logger.info("Restarting WebSocket worker")
        self.websocket_thread.stop()
        self.websocket_thread.wait()
        pairs = self.data_handler.load_pairs()
        self.websocket_thread = WebSocketWorker(pairs)
        self.websocket_thread.message_received.connect(self.ticker_updater.update_ticker_table)
        self.websocket_thread.start()
        self.update_pairs_display(pairs)

    def closeEvent(self, event):
        """Menangani event penutupan aplikasi, memastikan koneksi dan thread ditutup dengan benar."""
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

    # Flush and close file handlers
    logging.shutdown()
