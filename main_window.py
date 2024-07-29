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
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Currency Pair', 'Last Price', 'Change Percentage'])
        self.tableView_marketdata.setModel(self.model)
        self.tableView_marketdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Dictionary untuk melacak baris pasangan mata uang
        self.row_mapping = {}

        # Inisialisasi TickerTableUpdater
        self.ticker_updater = TickerTableUpdater(self.model, self.row_mapping)

        # Menjalankan thread websocket
        self.websocket_thread = WebSocketWorker()
        self.websocket_thread.message_received.connect(self.ticker_updater.update_ticker_table)
        logger.info("Starting WebSocket thread")
        self.websocket_thread.start()

if __name__ == "__main__":
    logger.info("Starting application")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

    # Flush and close file handlers
    logging.shutdown()
