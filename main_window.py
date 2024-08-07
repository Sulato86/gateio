import sys
import asyncio
from PyQt5.QtWidgets import QApplication, QMainWindow, QHeaderView, QMessageBox
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
        self.market_data_model = PandaMarketData([])
        self.tableView_marketdata.setModel(self.market_data_model)
        self.tableView_marketdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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
            QMessageBox.critical(self, 'Error', f'Gagal memuat saldo akun: {e}')

    def on_data_received(self, market_data):
        try:
            self.market_data_model.update_data(market_data)
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

    def import_market_data(self):
        headers, data = import_csv(self.tableView_marketdata)
        if headers and data:
            self.market_data_model.import_data(headers, data)
            pairs = [row[1] for row in data]
            asyncio.run_coroutine_threadsafe(self.ws_handler.add_pairs_from_csv(pairs), self.ws_handler.loop)
            self.on_data_received(self.market_data_model._data.values.tolist())
            QMessageBox.information(self, 'Impor Sukses', 'Data berhasil diimpor dari file CSV.')
        else:
            QMessageBox.warning(self, 'Tidak Ada Data', 'Tidak ada data yang diimpor atau terjadi kesalahan saat mengimpor.')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
