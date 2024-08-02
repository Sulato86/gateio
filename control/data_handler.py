import sqlite3
import logging
from PyQt5.QtCore import QObject, pyqtSignal, QSortFilterProxyModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from datetime import datetime, timezone

# Konfigurasi logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Buat handler untuk menulis log ke file
file_handler = logging.FileHandler('data_handler.log')
file_handler.setLevel(logging.DEBUG)

# Buat handler untuk menulis log ke console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Buat formatter dan tambahkan ke handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Tambahkan handler ke logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

class CustomSortFilterProxyModel(QSortFilterProxyModel):
    """
    Model kustom untuk mengurutkan data dalam QStandardItemModel.
    """

    def lessThan(self, left, right):
        """
        Mengurutkan data pada kolom tertentu sebagai angka.

        Args:
            left (QModelIndex): Indeks data sebelah kiri.
            right (QModelIndex): Indeks data sebelah kanan.

        Returns:
            bool: True jika data sebelah kiri kurang dari data sebelah kanan.
        """
        columns_to_sort_as_numbers = [2, 3]  # Kolom yang perlu sorting sebagai angka

        left_data = self.sourceModel().data(left)
        right_data = self.sourceModel().data(right)

        if left_data is None:
            return True
        if right_data is None:
            return False

        try:
            left_value = float(left_data)
            right_value = float(right_data)
        except ValueError:
            left_value = left_data
            right_value = right_data

        if left.column() in columns_to_sort_as_numbers:
            return left_value < right_value

        return super(CustomSortFilterProxyModel, self).lessThan(left, right)

class DataHandler(QObject):
    """
    Kelas untuk menangani data, termasuk koneksi ke database dan pemrosesan data.
    """
    data_ready = pyqtSignal(QStandardItemModel)
    message_received = pyqtSignal(dict)
    pair_added = pyqtSignal(str)
    pair_deleted = pyqtSignal(str)

    def __init__(self):
        """
        Inisialisasi DataHandler dan konfigurasikan koneksi ke database.
        """
        super().__init__()
        self.conn = self.create_connection('pairs.db')
        self.create_table(self.conn)
        self.row_mapping = {}
        logger.info("DataHandler initialized")

    def create_connection(self, db_file):
        """
        Membuat koneksi ke database SQLite.

        Args:
            db_file (str): Nama file database.

        Returns:
            sqlite3.Connection: Koneksi ke database.
        """
        logger.debug(f"Creating connection to database: {db_file}")
        try:
            conn = sqlite3.connect(db_file)
            logger.info("Connection to database established")
            return conn
        except sqlite3.Error as e:
            logger.error(f"Failed to create connection: {e}")
            return None

    def create_table(self, conn):
        """
        Membuat tabel 'pairs' dalam database jika belum ada.

        Args:
            conn (sqlite3.Connection): Koneksi ke database.
        """
        logger.debug("Creating table 'pairs' if it doesn't exist")
        try:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS pairs (name TEXT UNIQUE)''')
            conn.commit()
            logger.info("Table 'pairs' checked/created")
        except sqlite3.Error as e:
            logger.error(f"Failed to create table: {e}")

    def add_pair_to_db(self, pair):
        """
        Menyimpan pasangan mata uang ke database.

        Args:
            pair (str): Pasangan mata uang yang akan disimpan.
        """
        logger.debug(f"Adding pair to database: {pair}")
        try:
            cursor = self.conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO pairs (name) VALUES (?)', (pair,))
            self.conn.commit()
            logger.info(f"Pair {pair} saved to database")
            self.pair_added.emit(pair)
        except sqlite3.Error as e:
            logger.error(f"Failed to add pair to database: {e}")

    def load_pairs(self):
        """
        Memuat semua pasangan mata uang dari database.

        Returns:
            list: Daftar pasangan mata uang.
        """
        logger.debug("Loading pairs from database")
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT name FROM pairs')
            pairs = [row[0] for row in cursor.fetchall()]
            logger.info(f"Loaded pairs from database: {pairs}")
            return pairs
        except sqlite3.Error as e:
            logger.error(f"Failed to load pairs from database: {e}")
            return []

    def fetch_balances(self, http_worker):
        """
        Meminta saldo dari HTTPWorker.

        Args:
            http_worker (HTTPWorker): Instans dari HTTPWorker.
        """
        logger.debug("Fetching balances using HTTPWorker")
        http_worker.fetch_balances()

    def validate_pair(self, http_worker, pair):
        """
        Memvalidasi pasangan mata uang dengan HTTPWorker.

        Args:
            http_worker (HTTPWorker): Instans dari HTTPWorker.
            pair (str): Pasangan mata uang yang akan divalidasi.

        Returns:
            bool: True jika pasangan mata uang valid, False jika tidak.
        """
        logger.debug(f"Validating pair: {pair}")
        return http_worker.validate_pair(pair)

    def delete_pair_from_db(self, pair):
        """
        Menghapus pasangan mata uang dari database.

        Args:
            pair (str): Pasangan mata uang yang akan dihapus.
        """
        logger.debug(f"Deleting pair from database: {pair}")
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM pairs WHERE name = ?', (pair,))
            self.conn.commit()
            logger.info(f"Pair {pair} deleted from database")
            self.pair_deleted.emit(pair)

            cursor.execute('SELECT name FROM pairs WHERE name = ?', (pair,))
            result = cursor.fetchone()
            if result is None:
                logger.debug(f"Pair {pair} successfully removed from database.")
            else:
                logger.error(f"Pair {pair} still exists in database.")
        except sqlite3.Error as e:
            logger.error(f"Failed to delete pair from database: {e}")

    def delete_rows_by_column_value(self, model, column_index, value):
        """
        Menghapus baris pada model berdasarkan nilai kolom.

        Args:
            model (QStandardItemModel): Model data.
            column_index (int): Indeks kolom.
            value (str): Nilai yang akan dicocokkan untuk penghapusan baris.
        """
        logger.debug(f"Deleting rows with value {value} in column {column_index}")
        rows_to_remove = []
        for row in range(model.rowCount()):
            index = model.index(row, column_index)
            if model.data(index) == value:
                rows_to_remove.append(row)

        for row in reversed(rows_to_remove):
            model.removeRow(row)
            logger.info(f"Row {row} with value {value} in column {column_index} removed")

class TickerTableUpdater:
    """
    Kelas untuk memperbarui tabel ticker dengan data yang diterima.
    """

    def __init__(self, model, row_mapping):
        """
        Inisialisasi TickerTableUpdater.

        Args:
            model (QStandardItemModel): Model data untuk tabel ticker.
            row_mapping (dict): Pemetaan baris untuk pasangan mata uang.
        """
        self.model = model
        self.row_mapping = row_mapping
        logger.debug("TickerTableUpdater initialized")

    def update_ticker_table(self, message):
        """
        Memperbarui tabel ticker dengan pesan data yang diterima.

        Args:
            message (dict): Pesan data yang diterima.
        """
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

            if (currency_pair in self.row_mapping) and (self.row_mapping[currency_pair] < self.model.rowCount()):
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
