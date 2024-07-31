import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QHeaderView
from PyQt5.QtGui import QStandardItemModel
from control.websocket_worker import WebSocketWorker, TickerTableUpdater
from control.logging_config import setup_logging
from ui.ui_main_window import Ui_MainWindow
from control.http_worker import HTTPWorker

# Inisialisasi logger dengan file log terpisah
logger = setup_logging('main_window.log')

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, pairs=None):
        super().__init__()
        self.setupUi(self)

        # Dictionary untuk melacak baris pasangan mata uang
        self.row_mapping = {}

        # Inisialisasi model untuk tableView_marketdata
        self.market_model = QStandardItemModel()
        self.market_model.setHorizontalHeaderLabels(['TIME', 'PAIR', '24%', 'PRICE', 'VOLUME(Base)'])
        self.tableView_marketdata.setModel(self.market_model)
        self.tableView_marketdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Inisialisasi model untuk tableView_accountdata
        self.account_model = QStandardItemModel()
        self.account_model.setHorizontalHeaderLabels(['ASSET', 'FREE', 'LOCKED'])
        self.tableView_accountdata.setModel(self.account_model)
        self.tableView_accountdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Inisialisasi TickerTableUpdater pada worker.py
        self.ticker_updater = TickerTableUpdater(self.market_model, self.row_mapping)

        # Menjalankan thread websocket pada worker.py
        self.websocket_thread = WebSocketWorker(pairs)
        self.websocket_thread.message_received.connect(self.ticker_updater.update_ticker_table)
        logger.info("Starting WebSocket thread")
        self.websocket_thread.start()

        # Inisialisasi HTTPWorker
        self.http_worker = HTTPWorker()
        self.http_worker.data_ready.connect(self.update_account_view)
        self.http_worker.fetch_balances()

    def update_market_data(self, data):
        logger.debug(f"Market data updated: {data}")

    def update_account_view(self, account_model):
        self.tableView_accountdata.setModel(account_model)

if __name__ == "__main__":
    logger.info("Starting application")

    pairs = ["BTC_USDT", "ETH_USDT", "SOL_USDT", "SHIB_USDT", "GT_USDT", "BABYDOGE_USDT"]
    app = QApplication(sys.argv)
    window = MainWindow(pairs)
    window.show()
    sys.exit(app.exec_())

    # Flush and close file handlers
    logging.shutdown()


