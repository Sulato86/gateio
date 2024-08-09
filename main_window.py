import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QHeaderView, QMessageBox, QAbstractItemView, QMenu
from PyQt5.QtCore import Qt
from ui.ui_main_window import Ui_MainWindow
from utils.logging_config import configure_logging
from loaders.balances_loader import load_balances
from models.balances_table_model import BalancesTableModel
from models.panda_market_data import PandaMarketData
from control.csv_handler import export_csv

logger = configure_logging('main_window', 'logs/main_window.log')

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.load_balances()
        self.market_data_model = PandaMarketData(self, [])
        self.market_data_model.data_changed.connect(self.on_data_changed)
        self.tableView_marketdata.setModel(self.market_data_model)
        self.tableView_marketdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableView_marketdata.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView_marketdata.setSortingEnabled(True)
        self.tableView_marketdata.horizontalHeader().sectionClicked.connect(self.sort_market_data)
        self.tableView_marketdata.setSelectionMode(QAbstractItemView.MultiSelection)
        self.tableView_marketdata.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView_marketdata.customContextMenuRequested.connect(self.show_context_menu)
        self.lineEdit_addpair.returnPressed.connect(self.add_pair)
        self.pushButton_exportmarketdata.clicked.connect(self.export_market_data)

    def load_balances(self):
        try:
            table_data = load_balances()
            if table_data is None:
                raise ValueError("Data saldo kosong atau tidak valid.")
            self.model = BalancesTableModel(table_data)
            self.tableView_accountdata.setModel(self.model)
            self.tableView_accountdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        except Exception as e:
            self.show_error_message('Error', f'Gagal memuat saldo akun: {e}')

    def on_data_changed(self):
        self.tableView_marketdata.model().layoutChanged.emit()
        self.tableView_marketdata.viewport().update()

    def add_pair(self):
        pair = self.lineEdit_addpair.text().upper().strip()
        if pair:
            is_added = self.market_data_model.add_pair(pair)
            if is_added:
                self.show_info_message('PAIR Ditambahkan', f'PAIR {pair} berhasil ditambahkan.')
                self.lineEdit_addpair.clear()
                self.on_data_changed()
            else:
                self.show_warning_message('Input Error', f'PAIR {pair} tidak valid atau sudah ada.')
        else:
            self.show_warning_message('Input Error', 'Masukkan PAIR yang valid.')

    def sort_market_data(self, column):
        try:
            order = self.tableView_marketdata.horizontalHeader().sortIndicatorOrder()
            self.market_data_model.sort(column, order)
        except Exception as e:
            self.show_error_message('Error', f'Terjadi kesalahan saat mengurutkan data: {e}')

    def export_market_data(self):
        try:
            export_csv(self.tableView_marketdata)
            self.show_info_message('Ekspor Berhasil', 'Data pasar berhasil diekspor.')
        except Exception as e:
            self.show_error_message('Error', f'Gagal mengekspor data: {e}')

    def delete_selected_pairs(self):
        selected_indexes = self.tableView_marketdata.selectionModel().selectedRows()
        if not selected_indexes:
            self.show_warning_message('Delete Error', 'Tidak ada PAIR yang dipilih untuk dihapus.')
            return
        selected_rows = [index.row() for index in selected_indexes]
        if selected_rows:
            self.market_data_model.delete_selected_rows(selected_rows)
            self.show_info_message('PAIR Dihapus', 'PAIR yang dipilih berhasil dihapus.')

    def show_context_menu(self, pos):
        menu = QMenu(self)
        delete_action = menu.addAction("Hapus PAIR")
        delete_action.triggered.connect(self.delete_selected_pairs)
        menu.exec_(self.tableView_marketdata.viewport().mapToGlobal(pos))

    def show_error_message(self, title: str, message: str):
        QMessageBox.critical(self, title, message)

    def show_warning_message(self, title: str, message: str):
        QMessageBox.warning(self, title, message)

    def show_info_message(self, title: str, message: str):
        QMessageBox.information(self, title, message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
