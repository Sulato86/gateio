import logging
import pandas as pd
from PyQt5.QtCore import QAbstractTableModel, Qt

# Konfigurasi logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Handler untuk logging ke file
file_handler = logging.FileHandler('pandas.log')
file_handler.setLevel(logging.DEBUG)

# Handler untuk logging ke console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Format logging
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Menambahkan handler ke logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super(PandasModel, self).__init__()
        self._data = data
        logger.debug("PandasModel initialized with data")

    def rowCount(self, parent=None):
        count = len(self._data)
        logger.debug(f"Row count requested: {count}")
        return count

    def columnCount(self, parent=None):
        count = len(self._data.columns)
        logger.debug(f"Column count requested: {count}")
        return count

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        
        if role == Qt.DisplayRole:
            value = str(self._data.iloc[index.row(), index.column()])
            logger.debug(f"Data requested at ({index.row()}, {index.column()}): {value}")
            return value
        return None

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            header = self._data.columns[section]
            logger.debug(f"Header data requested for column {section}: {header}")
            return header
        if orientation == Qt.Vertical:
            header = self._data.index[section]
            logger.debug(f"Header data requested for row {section}: {header}")
            return header
        return None

    def update_data(self, data):
        self.beginResetModel()  # Notifikasi dimulai
        self._data = data
        self.endResetModel()  # Notifikasi selesai
        logger.debug("Data updated")

