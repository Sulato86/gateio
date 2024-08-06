import sys
import asyncio
from PyQt5.QtWidgets import QApplication, QMainWindow, QHeaderView, QMessageBox, QMenu
from PyQt5.QtCore import Qt
from ui.ui_main_window import Ui_MainWindow
from utils.logging_config import configure_logging
from loaders.balances_loader import load_balances
from models.balances_table_model import BalancesTableModel
from control.websocket_handler import WebSocketHandler
from models.market_data_table_model import MarketDataTableModel
from control.csv_handler import export_csv, import_csv
from models.sortable_proxy_model import SortableProxyModel

logger = configure_logging('main_window', 'logs/main_window.log')

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        logger.debug("Inisialisasi MainWindow")
        self.setupUi(self)
        self.load_balances()

        self.market_data = []
        self.market_data_model = MarketDataTableModel(self.market_data)
        self.proxy_model = SortableProxyModel()
        self.proxy_model.setSourceModel(self.market_data_model)
        self.tableView_marketdata.setModel(self.proxy_model)
        self.tableView_marketdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableView_marketdata.setSelectionBehavior(self.tableView_marketdata.SelectRows)
        self.tableView_marketdata.setSelectionMode(self.tableView_marketdata.ExtendedSelection)

        self.ws_handler = WebSocketHandler(self.on_data_received)
        self.ws_handler.start()

        self.lineEdit_addpair.returnPressed.connect(self.add_pair)
        self.pushButton_exportmarketdata.clicked.connect(lambda: export_csv(self.tableView_marketdata))
        self.pushButton_importmarketdata.clicked.connect(self.import_market_data)

        self.tableView_marketdata.horizontalHeader().sectionClicked.connect(self.handle_header_clicked)

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

    def on_data_received(self, market_data):
        logger.debug("Data diterima dari WebSocketHandler: %s", market_data)
        self.market_data_model.update_data(market_data)
        logger.info("Data market berhasil diperbarui di tabel")

    def add_pair(self):
        pair = self.lineEdit_addpair.text().upper()
        logger.debug(f"Menambahkan pasangan mata uang baru: {pair}")
        if pair:
            try:
                future = asyncio.run_coroutine_threadsafe(self.ws_handler.add_pair(pair), self.ws_handler.loop)
                is_added = future.result()
                if is_added:
                    QMessageBox.information(self, 'Pasangan Mata Uang Ditambahkan', f'Pasangan mata uang {pair} berhasil ditambahkan.')
                    self.lineEdit_addpair.clear()
                    logger.info(f"Pasangan mata uang {pair} berhasil ditambahkan")
                    self.on_data_received(self.ws_handler.market_data)
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
            rows = sorted(self.proxy_model.mapToSource(index).row() for index in selected_indexes)
            pairs = [self.market_data_model._data[row][1] for row in rows]
            try:
                self.market_data_model.remove_rows(rows)
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

    def handle_header_clicked(self, logicalIndex):
        order = self.proxy_model.sortOrder()
        selected_indexes = self.tableView_marketdata.selectionModel().selectedIndexes()
        selected_pairs = [self.market_data_model.get_data(self.proxy_model.mapToSource(index).row(), 1) for index in selected_indexes]
        self.proxy_model.sort(logicalIndex, Qt.DescendingOrder if order == Qt.AscendingOrder else Qt.AscendingOrder)
        selection_model = self.tableView_marketdata.selectionModel()
        selection_model.clearSelection()
        for pair in selected_pairs:
            row = self.market_data_model.find_row_by_pair(pair)
            if row != -1:
                index = self.proxy_model.mapFromSource(self.market_data_model.index(row, 0))
                selection_model.select(index, selection_model.Select | selection_model.Rows)

if __name__ == "__main__":
    logger.debug("Menjalankan aplikasi main_window.py")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
