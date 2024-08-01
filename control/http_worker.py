import logging
import requests
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from decimal import Decimal
from api.api_gateio import GateIOAPI, api_client

# Inisialisasi logger
logger = logging.getLogger('http_worker')
logger.setLevel(logging.DEBUG)

# Handler untuk file logging
file_handler = logging.FileHandler('http_worker.log')
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Handler untuk console logging
console_handler = logging.StreamHandler()
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# Menambahkan handler ke logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

class HTTPWorker(QObject):
    # Signal untuk mengirimkan model ke UI
    data_ready = pyqtSignal(QStandardItemModel)

    def __init__(self):
        """Inisialisasi HTTPWorker dan konfigurasikan API serta model akun."""
        super().__init__()
        self.api = GateIOAPI(api_client)
        self.account_model = QStandardItemModel()
        self.account_model.setHorizontalHeaderLabels(['ASSET', 'FREE', 'LOCKED'])
        logger.debug("HTTPWorker initialized with account model headers set.")
        
        # Inisialisasi QTimer untuk pembaruan data periodik
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.fetch_balances)
        self.timer.start(10000)
        logger.debug("Timer initialized to fetch balances every 10 seconds.")

    def fetch_balances(self):
        """Mengambil saldo dari API GateIO dan memperbarui model akun."""
        logger.info("Fetching balances from API.")
        try:
            balances = self.api.get_balances()
            if balances and isinstance(balances, dict):
                logger.debug(f"Balances fetched: {balances}")
                self.update_balances(balances)
            else:
                logger.error("Failed to fetch balances: Invalid data received.")
        except Exception as e:
            logger.exception("Exception occurred while fetching balances: %s", e)

    def update_balances(self, balances):
        """Memperbarui model akun dengan saldo yang diambil dari API."""
        logger.info("Updating account model with fetched balances.")
        self.account_model.setRowCount(0)  # Bersihkan model

        for balance_type, balance_list in balances.items():
            for balance in balance_list:
                # Akses atribut langsung dari objek balance
                if hasattr(balance, 'currency') and hasattr(balance, 'available') and hasattr(balance, 'locked'):
                    available_balance = Decimal(balance.available)
                    locked_balance = Decimal(balance.locked)
                    
                    # Sembunyikan saldo jika available dan locked kurang dari 1
                    if available_balance < 1 and locked_balance < 1:
                        continue

                    items = [
                        QStandardItem(str(balance.currency)),
                        QStandardItem(format(available_balance, '.2f')),
                        QStandardItem(format(locked_balance, '.2f'))
                    ]
                    self.account_model.appendRow(items)

        # Log jumlah saldo yang diperbarui
        logger.debug(f"Account model updated with {sum(len(b) for b in balances.values())} balances.")
        # Emit signal untuk memberitahukan UI bahwa data telah siap
        self.data_ready.emit(self.account_model)
        logger.info("Data ready signal emitted.")

    def validate_pair(self, pair):
        url = f"https://api.gateio.ws/api/v4/spot/currency_pairs/{pair}"
        response = requests.get(url)
        return response.status_code == 200
