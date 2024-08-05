from PyQt5.QtCore import QAbstractTableModel, Qt
from utils.logging_config import configure_logging

logger = configure_logging('balances_table_model', 'logs/balances_table_model.log')

class BalancesTableModel(QAbstractTableModel):
    
    def __init__(self, data):
        super(BalancesTableModel, self).__init__()
        logger.debug("Inisialisasi BalancesTableModel")
        self._data = data if data else []
        logger.debug(f"Data model inisialisasi dengan {len(self._data)} baris.")

    def data(self, index, role):
        
        if role == Qt.DisplayRole:
            value = self._data[index.row()][index.column()]
            if index.column() in [1, 2]:
                value = round(value, 2)
            return value

    def rowCount(self, index):
        
        return len(self._data)

    def columnCount(self, index):
        
        return len(self._data[0]) if self._data else 0

    def headerData(self, section, orientation, role):
    
        headers = ["Asset", "Available", "Locked"]
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return headers[section]
            if orientation == Qt.Vertical:
                return section + 1
