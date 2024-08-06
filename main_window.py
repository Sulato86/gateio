import sys
import asyncio
from PyQt5.QtWidgets import QApplication, QMainWindow, QHeaderView, QMessageBox, QMenu
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QItemSelectionModel
from ui.ui_main_window import Ui_MainWindow
from utils.logging_config import configure_logging
from loaders.balances_loader import load_balances
from models.balances_table_model import BalancesTableModel
from control.websocket_handler import WebSocketHandler
from models.market_data_table_model import MarketDataTableModel
from control.csv_handler import export_csv, import_csv
from models.sortable_proxy_model import SortableProxyModel

configure_logging('main_window', 'logs/main_window.log')

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
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
        try:
            table_data = load_balances()
            self.model = BalancesTableModel(table_data)
            self.tableView_accountdata.setModel(self.model)
            self.tableView_accountdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Gagal memuat saldo akun: {e}')

    def on_data_received(self, market_data):
        try:
            selected_pairs = self.save_selection()
            self.market_data_model.update_data(market_data)
            self.restore_selection(selected_pairs)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Terjadi kesalahan saat memperbarui data market: {e}')

    def add_pair(self):
        pair = self.lineEdit_addpair.text().upper()
        if pair:
            try:
                future = asyncio.run_coroutine_threadsafe(self.ws_handler.add_pair(pair), self.ws_handler.loop)
                is_added = future.result()
                if is_added:
                    QMessageBox.information(self, 'Pasangan Mata Uang Ditambahkan', f'Pasangan mata uang {pair} berhasil ditambahkan.')
                    self.lineEdit_addpair.clear()
                    self.on_data_received(self.ws_handler.market_data)
                else:
                    QMessageBox.warning(self, 'Input Error', f'Pasangan mata uang {pair} tidak valid atau sudah ada.')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Gagal menambahkan pasangan mata uang: {e}')
        else:
            QMessageBox.warning(self, 'Input Error', 'Masukkan pasangan mata uang yang valid.')

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
            pairs = [self.market_data_model.get_data(row, 1) for row in rows]
            try:
                self.market_data_model.remove_rows(rows)
                self.ws_handler.delete_selected_rows(pairs)
                self.on_data_received(self.market_data_model._data)
                QMessageBox.information(self, 'Baris Dihapus', 'Baris yang dipilih berhasil dihapus.')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Gagal menghapus baris yang dipilih: {e}')
        else:
            QMessageBox.warning(self, 'Tidak Ada Baris Terpilih', 'Pilih baris yang akan dihapus.')

    def import_market_data(self):
        headers, data = import_csv(self.tableView_marketdata)
        if headers and data:
            self.market_data_model.import_data(headers, data)
            pairs = [row[1] for row in data]
            asyncio.run_coroutine_threadsafe(self.ws_handler.add_pairs_from_csv(pairs), self.ws_handler.loop)
            self.on_data_received(self.market_data_model._data)
            QMessageBox.information(self, 'Impor Sukses', 'Data berhasil diimpor dari file CSV.')
        else:
            QMessageBox.warning(self, 'Tidak Ada Data', 'Tidak ada data yang diimpor atau terjadi kesalahan saat mengimpor.')

    def handle_header_clicked(self, logicalIndex):
        try:
            order = self.proxy_model.sortOrder()
            selected_pairs = self.save_selection()
            self.proxy_model.sort(logicalIndex, Qt.DescendingOrder if order == Qt.AscendingOrder else Qt.AscendingOrder)
            self.restore_selection(selected_pairs)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Terjadi kesalahan saat mengurutkan: {e}')

    def save_selection(self):
        try:
            selected_indexes = self.tableView_marketdata.selectionModel().selectedIndexes()
            selected_pairs = []
            for index in selected_indexes:
                if index.isValid():
                    source_index = self.proxy_model.mapToSource(index)
                    pair = self.market_data_model.get_data(source_index.row(), 1)
                    selected_pairs.append(pair)
            return selected_pairs
        except Exception as e:
            return []

    def restore_selection(self, selected_pairs):
        try:
            selection_model = self.tableView_marketdata.selectionModel()
            selection_model.clearSelection()
            for pair in selected_pairs:
                row = self.market_data_model.find_row_by_pair(pair)
                if row != -1:
                    index = self.proxy_model.mapFromSource(self.market_data_model.index(row, 0))
                    selection_model.select(index, QItemSelectionModel.Select | QItemSelectionModel.Rows)
        except Exception as e:
            pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
