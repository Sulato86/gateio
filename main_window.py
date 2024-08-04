import sys
import asyncio
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QHeaderView
from PyQt5.QtCore import QAbstractTableModel, Qt, QTimer
from PyQt5.QtGui import QColor, QBrush, QFont
from ui.ui_main_window import Ui_MainWindow
from logging_config import configure_logging
from loaders.balances_loader import load_balances
from models.balances_table_model import BalancesTableModel
from api.websocket_gateio import GateIOWebSocket

logger = configure_logging('main_window', 'logs/main_window.log')

class MarketDataTableModel(QAbstractTableModel):
    def __init__(self, data):
        """
        Inisialisasi MarketDataTableModel.

        Args:
            data (list): Data awal untuk model tabel.
        """
        super().__init__()
        self._data = data
        self._headers = ["TIME", "PAIR", "24%", "PRICE", "VOLUME"]

    def data(self, index, role):
        """
        Mengembalikan data untuk tampilan tabel.

        Args:
            index (QModelIndex): Indeks model.
            role (int): Peran tampilan.

        Returns:
            Any: Data untuk tampilan.
        """
        if not index.isValid():
            return None

        value = self._data[index.row()][index.column()]

        if role == Qt.DisplayRole:
            if index.column() in [2, 4]:
                try:
                    return f"{float(value):.2f}"
                except ValueError:
                    return value
            return value

        if role == Qt.BackgroundRole:
            try:
                change_percentage = float(self._data[index.row()][2])
                if change_percentage < 0:
                    return QBrush(QColor('red'))
                elif change_percentage > 0:
                    return QBrush(QColor('green'))
            except ValueError:
                return None

        if role == Qt.ForegroundRole:
            try:
                change_percentage = float(self._data[index.row()][2])
                if change_percentage < 0 or change_percentage > 0:
                    return QBrush(QColor('white'))
            except ValueError:
                return None

        return None

    def rowCount(self, index):
        """
        Mengembalikan jumlah baris dalam model.

        Args:
            index (QModelIndex): Indeks model.

        Returns:
            int: Jumlah baris.
        """
        return len(self._data)

    def columnCount(self, index):
        """
        Mengembalikan jumlah kolom dalam model.

        Args:
            index (QModelIndex): Indeks model.

        Returns:
            int: Jumlah kolom.
        """
        return len(self._headers)

    def headerData(self, section, orientation, role):
        """
        Mengembalikan data header untuk tampilan tabel.

        Args:
            section (int): Seksi header.
            orientation (Qt.Orientation): Orientasi header.
            role (int): Peran tampilan.

        Returns:
            Any: Data untuk header.
        """
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._headers[section]
        if role == Qt.FontRole and orientation == Qt.Horizontal:
            font = QFont()
            font.setBold(True)
            return font
        return None

    def update_data(self, new_data):
        """
        Memperbarui data dalam model tabel.

        Args:
            new_data (list): Data baru untuk memperbarui model.
        """
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        """
        Inisialisasi MainWindow.
        """
        logger.debug("Inisialisasi MainWindow")
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.load_balances()

        self.market_data = []
        self.market_data_model = MarketDataTableModel(self.market_data)
        self.tableView_marketdata.setModel(self.market_data_model)
        self.tableView_marketdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.gateio_ws = GateIOWebSocket(self.on_message, pairs=["BTC_USDT", "ETH_USDT"])

        self.loop = asyncio.get_event_loop()
        self.timer = QTimer()
        self.timer.timeout.connect(self.run_asyncio_loop)
        self.timer.start(100)

        asyncio.ensure_future(self.gateio_ws.run())

    def run_asyncio_loop(self):
        """
        Menjalankan loop asyncio.
        """
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.loop.run_forever()

    def load_balances(self):
        """
        Memuat saldo akun dan menampilkannya di tabel.
        """
        logger.debug("Memuat saldo akun di MainWindow")
        try:
            table_data = load_balances()
            self.model = BalancesTableModel(table_data)
            self.tableView_accountdata.setModel(self.model)
            self.tableView_accountdata.resizeColumnsToContents()
            self.tableView_accountdata.resizeRowsToContents()
            logger.info("Saldo akun berhasil dimuat dan ditampilkan di tabel")
        except Exception as e:
            logger.error(f"Error saat memuat saldo akun: {e}")

    def on_message(self, data):
        """
        Memproses data yang diterima dari WebSocket.

        Args:
            data (dict): Data dari WebSocket.
        """
        logger.debug("Menerima data market dari WebSocket")
        logger.debug(f"Data diterima: {data}")
        try:
            result = data['result']
            market_entry = [
                time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data['time'])),
                result['currency_pair'],
                result['change_percentage'],
                result['last'],
                result['base_volume']
            ]
            updated = False
            for i, entry in enumerate(self.market_data):
                if entry[1] == market_entry[1]:
                    self.market_data[i] = market_entry
                    updated = True
                    break
            if not updated:
                self.market_data.append(market_entry)
            self.market_data_model.update_data(self.market_data)
            logger.info("Data market berhasil dimuat dan ditampilkan di tabel")
        except KeyError as e:
            logger.error(f"Error saat memuat data market: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    logger.debug("Menjalankan aplikasi main_window.py")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
