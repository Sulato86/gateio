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
from control.csv_handler import export_csv, import_csv

logger = configure_logging('main_window', 'logs/main_window.log')

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        logger.debug("Inisialisasi MainWindow")
        self.setupUi(self)
        self.load_balances()

        self.market_data = []
        self.market_data_model = MarketDataTableModel(self.market_data)
        self.tableView_marketdata.setModel(self.market_data_model)
        self.tableView_marketdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableView_marketdata.setSelectionBehavior(self.tableView_marketdata.SelectRows)
        self.tableView_marketdata.setSelectionMode(self.tableView_marketdata.ExtendedSelection)

        self.ws_handler = WebSocketHandler(self.update_market_data)
        self.ws_handler.market_data_updated.connect(self.update_market_data)

        self.timer = QTimer()
        self.timer.timeout.connect(self.run_asyncio_loop)
        self.timer.start(100)

        self.lineEdit_addpair.returnPressed.connect(self.add_pair)
        self.pushButton_exportmarketdata.clicked.connect(lambda: export_csv(self.tableView_marketdata))
        self.pushButton_importmarketdata.clicked.connect(self.import_market_data)

    def run_asyncio_loop(self):
        try:
            self.ws_handler.run_asyncio_loop()
        except Exception as e:
            logger.error(f"Error in asyncio loop: {e}")

    def load_balances(self):
        logger.debug("Memuat saldo akun di MainWindow")
        try:
            table_data = load_balances()
            self.model = BalancesTableModel(table_data)
            self.tableView_accountdata.setModel(self.model)
            self.tableView_accountdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            logger.info("Saldo akun berhasil dimuat dan ditampilkan di tabel")
        except Exception as e:
            logger.error(f"Error saat memuat saldo akun: {e}")
            QMessageBox.critical(self, 'Error', f'Gagal memuat saldo akun: {e}')

    def update_market_data(self, market_data):
        logger.debug("Memperbarui data market di tabel dengan data: %s", market_data)
        try:
            selected_indexes = self.tableView_marketdata.selectionModel().selectedIndexes()
            self.market_data_model.update_data(market_data)
            logger.info("Data market di tabel berhasil diperbarui")
            for index in selected_indexes:
                self.tableView_marketdata.selectionModel().select(index, self.tableView_marketdata.selectionModel().Select)
        except Exception as e:
            logger.error(f"Error saat memperbarui data market: {e}")
            QMessageBox.critical(self, 'Error', f'Gagal memperbarui data market: {e}')

    def add_pair(self):
        pair = self.lineEdit_addpair.text().upper()
        logger.debug(f"Menambahkan pasangan mata uang baru: {pair}")
        if pair:
            try:
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
        context_menu = QMenu(self)
        delete_action = context_menu.addAction("Hapus Baris")
        action = context_menu.exec_(self.mapToGlobal(event.pos()))
        if action == delete_action:
            self.delete_selected_rows()

    def delete_selected_rows(self):
        selected_indexes = self.tableView_marketdata.selectionModel().selectedRows()
        if selected_indexes:
            rows = sorted(index.row() for index in selected_indexes)
            pairs = [self.market_data_model._data[row][1] for row in rows]
            try:
                self.ws_handler.delete_selected_rows(pairs)
                QMessageBox.information(self, 'Baris Dihapus', 'Baris yang dipilih berhasil dihapus.')
                logger.info("Baris yang dipilih berhasil dihapus")
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Gagal menghapus baris yang dipilih: {e}')
                logger.error(f"Gagal menghapus baris yang dipilih: {e}")
        else:
            QMessageBox.warning(self, 'Tidak Ada Baris Terpilih', 'Pilih baris yang akan dihapus.')
            logger.warning("Tidak ada baris terpilih untuk dihapus")

    def import_market_data(self):
        headers, data = import_csv(self.tableView_marketdata)
        if headers and data:
            self.market_data_model.import_data(headers, data)
            pairs = [row[1] for row in data]
            asyncio.run_coroutine_threadsafe(self.ws_handler.add_pairs_from_csv(pairs), self.ws_handler.loop)
            QMessageBox.information(self, 'Impor Sukses', 'Data berhasil diimpor dari file CSV.')
            logger.info("Data berhasil diimpor dari file CSV")
        else:
            logger.warning("Tidak ada data yang diimpor atau terjadi kesalahan saat mengimpor")

if __name__ == "__main__":
    logger.debug("Menjalankan aplikasi main_window.py")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
