import sys
import logging
import sqlite3
from PyQt5.QtWidgets import QApplication, QMainWindow, QHeaderView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
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

        # Setup database connection
        self.conn = sqlite3.connect('pairs.db')
        self.create_table()

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
        pairs = self.load_pairs()
        self.websocket_thread = WebSocketWorker(pairs)
        self.websocket_thread.message_received.connect(self.ticker_updater.update_ticker_table)
        logger.info("Starting WebSocket thread")
        self.websocket_thread.start()

        # Inisialisasi HTTPWorker
        self.http_worker = HTTPWorker()
        self.http_worker.data_ready.connect(self.update_account_view)
        self.http_worker.fetch_balances()

        # Hubungkan QLineEdit untuk input pasangan baru
        self.lineEdit_addpair.returnPressed.connect(self.add_pair)

        # Tampilkan pasangan mata uang yang sudah ada saat inisialisasi
        self.update_pairs_display(pairs)

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS pairs (name TEXT UNIQUE)''')
        self.conn.commit()

    def add_pair(self):
        pair = self.lineEdit_addpair.text().upper()
        if pair and pair not in self.websocket_thread.gateio_ws.pairs:
            logger.info(f"Adding pair: {pair}")
            self.websocket_thread.gateio_ws.pairs.append(pair)
            self.websocket_thread.add_pair(pair)
            self.save_pair(pair)
            self.update_pairs_display([pair])
            self.lineEdit_addpair.clear()
        else:
            logger.info(f"Pair {pair} already exists or is invalid.")

    def save_pair(self, pair):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO pairs (name) VALUES (?)', (pair,))
        self.conn.commit()
        logger.info(f"Pair {pair} saved to database.")

    def load_pairs(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT name FROM pairs')
        pairs = [row[0] for row in cursor.fetchall()]
        logger.info(f"Loaded pairs from database: {pairs}")
        return pairs

    def update_pairs_display(self, pairs=None):
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
        logger.debug(f"Market data updated: {data}")

    def update_account_view(self, account_model):
        self.tableView_accountdata.setModel(account_model)

    def closeEvent(self, event):
        self.conn.close()
        event.accept()

if __name__ == "__main__":
    logger.info("Starting application")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

    # Flush and close file handlers
    logging.shutdown()
