import sys
import asyncio
from PyQt5.QtWidgets import QApplication, QMainWindow, QHeaderView, QMessageBox, QMenu
from PyQt5.QtCore import QTimer, Qt
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
        self.tableView_marketdata.setSelectionBehavior(self.tableView_marketdata.SelectRows)
        self.tableView_marketdata.setSelectionMode(self.tableView_marketdata.ExtendedSelection)

        self.ws_handler = WebSocketHandler(self.update_market_data)

        self.timer = QTimer()
        self.timer.timeout.connect(self.run_asyncio_loop)
        self.timer.start(500)  # Interval diubah menjadi 500 milidetik

        self.lineEdit_addpair.returnPressed.connect(self.add_pair)

    def run_asyncio_loop(self):
        """
        Menjalankan loop asyncio.
        """
        try:
            self.ws_handler.run_asyncio_loop()
        except Exception as e:
            logger.error(f"Error in asyncio loop: {e}")

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

        # Simpan indeks yang dipilih
        selected_indexes = self.tableView_marketdata.selectionModel().selectedIndexes()

        self.market_data_model.update_data(market_data)
        logger.info("Data market di tabel berhasil diperbarui")

        # Kembalikan sorotan
        for index in selected_indexes:
            self.tableView_marketdata.selectionModel().select(index, self.tableView_marketdata.selectionModel().Select)

    def add_pair(self):
        """
        Menambahkan pasangan mata uang baru berdasarkan input pengguna.
        """
        pair = self.lineEdit_addpair.text().upper()
        logger.debug(f"Menambahkan pasangan mata uang baru: {pair}")
        if pair:
            try:
                # Menggunakan asyncio.run untuk menjalankan coroutine dari add_pair
                loop = asyncio.get_event_loop()
                is_added = loop.run_until_complete(self.ws_handler.add_pair(pair))
                if is_added:
                    QMessageBox.information(self, 'Pasangan Mata Uang Ditambahkan', f'Pasangan mata uang {pair} berhasil ditambahkan.')
                    self.lineEdit_addpair.clear()
                    logger.info(f"Pasangan mata uang {pair} berhasil ditambahkan")
                else:
                    QMessageBox.warning(self, 'Input Error', f'Pasangan mata uang {pair} tidak valid atau sudah ada.')
                    logger.warning(f"Pasangan mata uang {pair} tidak valid atau sudah ada")
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Gagal menambahkan pasangan mata uang: {e}')
                logger.error(f"Gagal menambahkan pasangan mata uang: {e}")
        else:
            QMessageBox.warning(self, 'Input Error', 'Masukkan pasangan mata uang yang valid.')
            logger.warning("Input pasangan mata uang tidak valid")

    def contextMenuEvent(self, event):
        """
        Menangani event klik kanan untuk menampilkan menu konteks.
        """
        context_menu = QMenu(self)
        delete_action = context_menu.addAction("Hapus Baris")
        action = context_menu.exec_(self.mapToGlobal(event.pos()))
        if action == delete_action:
            self.delete_selected_rows()

    def delete_selected_rows(self):
        """
        Menghapus baris yang dipilih dari tabel market data.
        """
        selected_indexes = self.tableView_marketdata.selectionModel().selectedRows()
        if selected_indexes:
            rows = sorted(index.row() for index in selected_indexes)
            pairs = [self.market_data_model._data[row][1] for row in rows]
            self.ws_handler.delete_selected_rows(pairs)
            QMessageBox.information(self, 'Baris Dihapus', 'Baris yang dipilih berhasil dihapus.')
        else:
            QMessageBox.warning(self, 'Tidak Ada Baris Terpilih', 'Pilih baris yang akan dihapus.')

if __name__ == "__main__":
    logger.debug("Menjalankan aplikasi main_window.py")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
