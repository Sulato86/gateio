import sqlite3
import logging
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class DataHandler(QObject):
    data_ready = pyqtSignal(QStandardItemModel)
    message_received = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.conn = self.create_connection('pairs.db')
        self.create_table(self.conn)
        self.row_mapping = {}

    def create_connection(self, db_file):
        """Membuat koneksi ke database SQLite."""
        conn = sqlite3.connect(db_file)
        return conn

    def create_table(self, conn):
        """Membuat tabel 'pairs' dalam database jika belum ada."""
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS pairs (name TEXT UNIQUE)''')
        conn.commit()

    def add_pair_to_db(self, pair):
        """Menyimpan pasangan mata uang ke database."""
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO pairs (name) VALUES (?)', (pair,))
        self.conn.commit()
        logger.info(f"Pair {pair} saved to database.")

    def load_pairs(self):
        """Memuat semua pasangan mata uang dari database."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT name FROM pairs')
        pairs = [row[0] for row in cursor.fetchall()]
        logger.info(f"Loaded pairs from database: {pairs}")
        return pairs

    def fetch_balances(self, http_worker):
        """Meminta saldo dari HTTPWorker."""
        http_worker.fetch_balances()

    def validate_pair(self, http_worker, pair):
        """Memvalidasi pasangan mata uang dengan HTTPWorker."""
        return http_worker.validate_pair(pair)

class TickerTableUpdater:
    def __init__(self, model, row_mapping):
        self.model = model
        self.row_mapping = row_mapping
        logger.debug("TickerTableUpdater initialized")

    def update_ticker_table(self, message):
        logger.debug(f"Received message for ticker update: {message}")
        ticker_data = message.get('result', {})
        required_keys = ['currency_pair', 'change_percentage', 'last', 'base_volume']

        if all(key in ticker_data for key in required_keys):
            epoch_time = message.get('time', 0)
            local_time = datetime.fromtimestamp(epoch_time, timezone.utc).astimezone()
            time_str = local_time.strftime('%d-%m-%Y %H:%M:%S')

            currency_pair = ticker_data['currency_pair']
            change_percentage = float(ticker_data['change_percentage'])
            last_price = ticker_data['last']
            volume = ticker_data.get('base_volume', 0.0)
            volume = float(volume) if volume is not None else 0.0

            change_percentage = f"{change_percentage:.1f}"
            volume = f"{volume:.2f}"

            logger.info(f"Updating ticker table for {currency_pair}")

            if currency_pair in self.row_mapping:
                row_index = self.row_mapping[currency_pair]
                logger.debug(f"Updating existing row for {currency_pair} at index {row_index}")
                self.model.setItem(row_index, 0, QStandardItem(str(time_str)))
                self.model.setItem(row_index, 1, QStandardItem(currency_pair))
                self.model.setItem(row_index, 2, QStandardItem(change_percentage))
                self.model.setItem(row_index, 3, QStandardItem(last_price))
                self.model.setItem(row_index, 4, QStandardItem(volume))
            else:
                row_index = self.model.rowCount()
                logger.debug(f"Inserting new row for {currency_pair} at index {row_index}")
                self.row_mapping[currency_pair] = row_index
                time_item = QStandardItem(str(time_str))
                currency_pair_item = QStandardItem(currency_pair)
                change_percentage_item = QStandardItem(change_percentage)
                last_price_item = QStandardItem(last_price)
                volume_item = QStandardItem(volume)
                self.model.appendRow([time_item, currency_pair_item, change_percentage_item, last_price_item, volume_item])
                logger.debug(f"Row added for {currency_pair}")
        else:
            missing_keys = [key for key in required_keys if key not in ticker_data]
            logger.error(f"Missing expected keys in data: {missing_keys}, data: {ticker_data}")
