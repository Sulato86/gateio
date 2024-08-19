import pandas as pd
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, QTimer
from utils.logging_config import configure_logging
from api.api_get_balances import ApiHandler

# Konfigurasi logging
logger = configure_logging('panda_account_data', 'logs/panda_account_data.log')

class PandaAccountData(QAbstractTableModel):
    def __init__(self, update_interval=10000):
        super(PandaAccountData, self).__init__()
        self.api_handler = ApiHandler()
        self.sort_column = None
        self.sort_order = Qt.AscendingOrder
        self.update_data()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(update_interval)

    def update_data(self):
        try:
            data = self.api_handler.get_balances_data()
            logger.info(f"Data akun yang diterima: {data}")
            if not data or data == [["-", 0, 0]]:
                logger.warning("Data tidak valid atau kosong, menggunakan data default.")
                self.df = pd.DataFrame([["-", 0, 0]], columns=["Asset", "Available", "Locked"])
            else:
                self.df = pd.DataFrame(data, columns=["Asset", "Available", "Locked"])

            if self.sort_column is not None:
                self.sort_data(self.sort_column, self.sort_order)
            else:
                self.layoutChanged.emit()
        except Exception as e:
            logger.error(f"Gagal memperbarui data: {e}")
            self.df = pd.DataFrame([["-", 0, 0]], columns=["Asset", "Available", "Locked"])
            self.layoutChanged.emit()

    def sort_data(self, column, order):
        self.sort_column = column
        self.sort_order = order
        ascending = True if order == Qt.AscendingOrder else False
        column_name = self.df.columns[column]
        try:
            self.df.sort_values(by=column_name, ascending=ascending, inplace=True, ignore_index=True)
            self.layoutChanged.emit()
        except Exception as e:
            logger.error(f"Gagal mengurutkan data: {e}")

    def rowCount(self, parent=QModelIndex()):
        return len(self.df)

    def columnCount(self, parent=QModelIndex()):
        return len(self.df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return str(self.df.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        headers = ["Asset", "Available", "Locked"]
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return headers[section]
        return None
