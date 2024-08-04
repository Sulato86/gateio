import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from ui.ui_main_window import Ui_MainWindow
from logging_config import configure_logging
from loaders.balances_loader import load_balances
from models.balances_table_model import BalancesTableModel

# Konfigurasi logging untuk main_window
logger = configure_logging('main_window', 'logs/main_window.log')

class MainWindow(QMainWindow, Ui_MainWindow):
    """
    Kelas untuk jendela utama aplikasi trading.

    Methods:
        __init__: Inisialisasi jendela utama.
        load_balances: Memuat saldo akun dan menampilkannya di tabel.
    """
    def __init__(self):
        logger.debug("Inisialisasi MainWindow")
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.load_balances()

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

if __name__ == "__main__":
    logger.debug("Menjalankan aplikasi main_window.py")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
