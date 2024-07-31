import logging
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from api.api_gateio import GateIOAPI, api_client
from decimal import Decimal  # Import modul Decimal

# Inisialisasi logger
logger = logging.getLogger('http_worker')
logger.setLevel(logging.DEBUG)

# Handler untuk file logging
file_handler = logging.FileHandler('http_worker.log')
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levellevel)s - %(message)s')
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
        super().__init__()
        # Inisialisasi GateIOAPI
        self.api = GateIOAPI(api_client)
        self.account_model = QStandardItemModel()
        self.account_model.setHorizontalHeaderLabels(['ASSET', 'FREE', 'LOCKED'])
        logger.debug("HTTPWorker initialized with account model headers set.")

    def fetch_balances(self):
        # Mengambil saldo dari API
        logger.info("Fetching balances from API.")
        try:
            balances = self.api.get_balances()
            if balances:
                logger.debug(f"Balances fetched: {balances}")
                self.update_balances(balances)
            else:
                logger.error("Failed to fetch balances: No data received.")
        except Exception as e:
            logger.exception("Exception occurred while fetching balances: %s", e)

    def update_balances(self, balances):
        # Memperbarui model akun dengan saldo yang diambil
        logger.info("Updating account model with fetched balances.")
        self.account_model.setRowCount(0)  # Clear the model

        # Memproses saldo dari berbagai jenis akun jika ada
        for balance_type, balance_list in balances.items():
            for balance in balance_list:
                # Creating QStandardItem for each attribute and adding to the model
                items = [
                    QStandardItem(str(getattr(balance, 'currency'))),
                    QStandardItem(format(Decimal(getattr(balance, 'available')), '.2f')),
                    QStandardItem(format(Decimal(getattr(balance, 'locked')), '.2f'))
                ]
                self.account_model.appendRow(items)

        logger.debug(f"Account model updated with {sum(len(b) for b in balances.values())} balances.")
        self.data_ready.emit(self.account_model)  # Emit signal indicating data is ready
        logger.info("Data ready signal emitted.")
