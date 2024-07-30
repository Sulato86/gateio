import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QHeaderView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from control.websocket_worker import WebSocketWorker, TickerTableUpdater
from control.logging_config import setup_logging
from ui.ui_main_window import Ui_MainWindow

# Inisialisasi logger dengan file log terpisah
logger = setup_logging('main_window.log')

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        # Inisialisasi kelas MainWindow yang mengatur UI.
        super().__init__()
        self.setupUi(self)

        # Inisialisasi model untuk tableView_marketdata
        self.market_model = QStandardItemModel()
        self.market_model.setHorizontalHeaderLabels(['TIME', 'PAIR', '24%', 'PRICE', 'VOLUME(B)'])  # Urutan kolom baru
        self.tableView_marketdata.setModel(self.market_model)
        self.tableView_marketdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Dictionary untuk melacak baris pasangan mata uang
        self.row_mapping = {}

        # Inisialisasi TickerTableUpdater websocket_worker.py
        self.ticker_updater = TickerTableUpdater(self.market_model, self.row_mapping)

        # Inisialisasi model untuk tableView_accountdata
        self.balance_model = QStandardItemModel()
        self.balance_model.setHorizontalHeaderLabels(['Currency', 'Available', 'Locked'])
        self.tableView_accountdata.setModel(self.balance_model)
        self.tableView_accountdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Menjalankan thread websocket
        self.websocket_thread = WebSocketWorker()
        self.websocket_thread.message_received.connect(self.ticker_updater.update_ticker_table)
        self.websocket_thread.balance_received.connect(self.update_balance_table)
        logger.info("Starting WebSocket thread")
        self.websocket_thread.start()

    def update_balance_table(self, balances):
        self.balance_model.clear()
        self.balance_model.setHorizontalHeaderLabels(['Currency', 'Available', 'Locked'])
        logger.info(f"Updating balance table with data: {balances}")
        for balance in balances:
            currency = QStandardItem(balance.get("currency", ""))
            available = QStandardItem(balance.get("available", ""))
            locked = QStandardItem(balance.get("locked", ""))
            self.balance_model.appendRow([currency, available, locked])

if __name__ == "__main__":
    logger.info("Starting application")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

    # Flush and close file handlers
    logging.shutdown()
