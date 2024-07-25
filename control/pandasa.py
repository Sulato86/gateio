import logging
import pandas as pd
from PyQt5.QtCore import QAbstractTableModel, Qt

# Konfigurasi logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Handler untuk logging ke file
file_handler = logging.FileHandler('pandasa.log')
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
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._data.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            if pd.isnull(value):
                return ""
            return str(value)
        return None

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self._data.columns[section]
        if orientation == Qt.Vertical:
            return self._data.index[section]

    def sort(self, column, order):
        colname = self._data.columns[column]
        logger.debug(f"Sorting column {colname} in {'ascending' if order == Qt.AscendingOrder else 'descending'} order")
        logger.debug(f"Before sorting: {self._data[[colname]].head(10)}")  # Menampilkan 10 baris pertama sebelum sorting
        self.layoutAboutToBeChanged.emit()
        self._data.sort_values(by=[colname], ascending=(order == Qt.AscendingOrder), inplace=True)
        self.layoutChanged.emit()
        logger.debug(f"After sorting: {self._data[[colname]].head(10)}")  # Menampilkan 10 baris pertama setelah sorting

    def update_data(self, data):
        logger.debug(f"Updating PandasModel data with {data.dtypes}")
        self.layoutAboutToBeChanged.emit()
        self._data = data
        self.layoutChanged.emit()
        logger.debug(f"PandasModel data updated to {self._data.dtypes}")
