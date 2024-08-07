import sys
import asyncio
from PyQt5.QtWidgets import QApplication, QMainWindow, QHeaderView, QMessageBox
from PyQt5.QtCore import Qt
from ui.ui_main_window import Ui_MainWindow
from utils.logging_config import configure_logging
from loaders.balances_loader import load_balances
from models.balances_table_model import BalancesTableModel
from control.websocket_handler import WebSocketHandler
from models.panda_market_data import PandaMarketData
from control.csv_handler import export_csv, import_csv

logger = configure_logging('main_window', 'logs/main_window.log')

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.load_balances()
        
        # Setup PandaMarketData model
        self.market_data_model = PandaMarketData([])
        self.tableView_marketdata.setModel(self.market_data_model)
        self.tableView_marketdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableView_marketdata.setSortingEnabled(True)
        self.tableView_marketdata.horizontalHeader().sectionClicked.connect(self.sort_market_data)
        
        self.ws_handler = WebSocketHandler(self.on_data_received)
        self.ws_handler.start()
        
        self.lineEdit_addpair.returnPressed.connect(self.add_pair)
        self.pushButton_exportmarketdata.clicked.connect(lambda: export_csv(self.tableView_marketdata))
        self.pushButton_importmarketdata.clicked.connect(self.import_market_data)

    def load_balances(self):
        try:
            table_data = load_balances()
            self.model = BalancesTableModel(table_data)
            self.tableView_accountdata.setModel(self.model)
            self.tableView_accountdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        except Exception as e:
            self.show_error_message('Error', f'Gagal memuat saldo akun: {e}')
            logger.error(f"Error loading balances: {e}")

    def on_data_received(self, market_data):
        try:
            logger.info("Data received in MainWindow, calling update_data")
            self.market_data_model.update_data(market_data)
            logger.info("Data updated in MainWindow")
            self.log_table_data()
        except Exception as e:
            self.show_error_message('Error', f'Terjadi kesalahan saat memperbarui data market: {e}')
            logger.error(f"Error updating data in MainWindow: {e}")

    def log_table_data(self):
        row_count = self.market_data_model.rowCount(None)
        col_count = self.market_data_model.columnCount(None)
        for row in range(row_count):
            row_data = [self.market_data_model.get_data(row, col) for col in range(col_count)]
            logger.info(f"Row {row}: {row_data}")

    def add_pair(self):
        pair = self.lineEdit_addpair.text().upper()
        if pair:
            try:
                future = asyncio.run_coroutine_threadsafe(self.ws_handler.add_pair(pair), self.ws_handler.loop)
                is_added = future.result()
                if is_added:
                    self.show_info_message('Pasangan Mata Uang Ditambahkan', f'Pasangan mata uang {pair} berhasil ditambahkan.')
                    self.lineEdit_addpair.clear()
                    self.on_data_received(self.ws_handler.market_data)
                else:
                    self.show_warning_message('Input Error', f'Pasangan mata uang {pair} tidak valid atau sudah ada.')
            except Exception as e:
                self.show_error_message('Error', f'Gagal menambahkan pasangan mata uang: {e}')
                logger.error(f"Error adding pair in MainWindow: {e}")
        else:
            self.show_warning_message('Input Error', 'Masukkan pasangan mata uang yang valid.')

    def import_market_data(self):
        headers, data = import_csv(self.tableView_marketdata)
        if headers and data:
            try:
                self.market_data_model.import_data(headers, data)
                pairs = [row[1] for row in data]
                asyncio.run_coroutine_threadsafe(self.ws_handler.add_pairs_from_csv(pairs), self.ws_handler.loop)
                self.on_data_received(self.market_data_model._data.values.tolist())
                self.show_info_message('Impor Sukses', 'Data berhasil diimpor dari file CSV.')
            except Exception as e:
                self.show_error_message('Error', f'Terjadi kesalahan saat mengimpor data: {e}')
                logger.error(f"Error importing market data in MainWindow: {e}")
        else:
            self.show_warning_message('Tidak Ada Data', 'Tidak ada data yang diimpor atau terjadi kesalahan saat mengimpor.')

    def sort_market_data(self, column):
        try:
            order = self.tableView_marketdata.horizontalHeader().sortIndicatorOrder()
            logger.info(f"Sorting column {column} with order {order}")
            self.market_data_model.sort(column, order)
            logger.info("Data sorted in MainWindow")
        except Exception as e:
            self.show_error_message('Error', f'Terjadi kesalahan saat mengurutkan data: {e}')
            logger.error(f"Error sorting data in MainWindow: {e}")

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