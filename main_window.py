import sys
import asyncio
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from PyQt5.QtWidgets import QApplication, QMainWindow, QHeaderView, QMessageBox
from PyQt5.QtCore import QTimer
from ui.ui_main_window import Ui_MainWindow
from utils.logging_config import configure_logging
from loaders.balances_loader import load_balances
from models.balances_table_model import BalancesTableModel
from control.websocket_handler import WebSocketHandler
from models.market_data_table_model import MarketDataTableModel

logger = configure_logging('main_window', 'logs/main_window.log')

class MainWindow(QMainWindow, Ui_MainWindow):
    """
    Kelas untuk menangani logika utama aplikasi dan interaksi pengguna.
    """

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

        self.ws_handler = WebSocketHandler(self.update_market_data)

        self.timer = QTimer()
        self.timer.timeout.connect(self.ws_handler.run_asyncio_loop)
        self.timer.start(100)

        self.lineEdit_addpair.returnPressed.connect(self.add_pair)

    def run_asyncio_loop(self):
        """
        Menjalankan loop asyncio.
        """
        self.ws_handler.run_asyncio_loop()

    def load_balances(self):
        """
        Memuat saldo akun dan menampilkannya di tabel.
        """
        logger.debug("Memuat saldo akun di MainWindow")
        try:
            table_data = load_balances()
            self.model = BalancesTableModel(table_data)
            self.tableView_accountdata.setModel(self.model)
            self.tableView_accountdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            logger.info("Saldo akun berhasil dimuat dan ditampilkan di tabel")
        except Exception as e:
            logger.error(f"Error saat memuat saldo akun: {e}")

    def update_market_data(self, market_data):
        """
        Memperbarui data market di tabel.

        Args:
            market_data (list): Data market terbaru.
        """
        logger.debug("Memperbarui data market di tabel dengan data: %s", market_data)
        self.market_data_model.update_data(market_data)
        logger.info("Data market di tabel berhasil diperbarui")

    def add_pair(self):
        """
        Menambahkan pasangan mata uang baru berdasarkan input pengguna.
        """
        pair = self.lineEdit_addpair.text().upper()
        logger.debug(f"Menambahkan pasangan mata uang baru: {pair}")
        if pair:
            try:
                self.ws_handler.add_pair(pair)
                QMessageBox.information(self, 'Pasangan Mata Uang Ditambahkan', f'Pasangan mata uang {pair} berhasil ditambahkan.')
                self.lineEdit_addpair.clear()
                logger.info(f"Pasangan mata uang {pair} berhasil ditambahkan")
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Gagal menambahkan pasangan mata uang: {e}')
                logger.error(f"Gagal menambahkan pasangan mata uang: {e}")
        else:
            QMessageBox.warning(self, 'Input Error', 'Masukkan pasangan mata uang yang valid.')
            logger.warning("Input pasangan mata uang tidak valid")

if __name__ == "__main__":
    logger.debug("Menjalankan aplikasi main_window.py")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
