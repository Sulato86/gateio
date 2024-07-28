import pandas as pd
from PyQt5.QtCore import QAbstractTableModel, QSortFilterProxyModel, Qt
from control.logging_config import setup_logging

# Konfigurasi logging
logger = setup_logging('pandas_handler.py.log')

class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

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
            # Mengembalikan data dalam format string dengan 2 digit desimal untuk kolom "VOLUME"
            if self._data.columns[index.column()] == "VOLUME":
                return f"{value:.2f}"
            return str(value)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self._data.columns[section]
        if orientation == Qt.Vertical:
            return self._data.index[section]
        return None

    def sort(self, column, order):
        colname = self._data.columns[column]
        self.layoutAboutToBeChanged.emit()
        self._data.sort_values(by=[colname], ascending=(order == Qt.AscendingOrder), inplace=True)
        self.layoutChanged.emit()
        logger.debug(f"Data sorted by {colname} in {'ascending' if order == Qt.AscendingOrder else 'descending'} order")

    def update_data(self, data):
        self.layoutAboutToBeChanged.emit()
        self._data = data
        self.layoutChanged.emit()
        logger.debug("Data model updated")

    def removeRows(self, row, count, parent=None):
        self.layoutAboutToBeChanged.emit()
        indices = list(range(row, row + count))
        self._data.drop(self._data.index[indices], inplace=True)
        self._data.reset_index(drop=True, inplace=True)
        self.layoutChanged.emit()
        logger.debug(f"Rows {indices} removed")

    def hapus_baris_pertama_kedua(self):
        if self.rowCount() > 1:
            self.removeRows(0, 2)
            logger.debug("Baris pertama dan kedua dihapus")

class CustomSortFilterProxyModel(QSortFilterProxyModel):
    def lessThan(self, left, right):
        left_data = self.sourceModel().data(left, Qt.DisplayRole)
        right_data = self.sourceModel().data(right, Qt.DisplayRole)
        column = left.column()
        pair_column_index = 1
        
        if column == pair_column_index:
            result = left_data < right_data
            logger.debug(f"Comparing pairs: {left_data} < {right_data}: {result}")
            return result
        else:
            try:
                left_data = float(left_data)
                right_data = float(right_data)
                result = left_data < right_data
                logger.debug(f"Comparing numerical data: {left_data} < {right_data}: {result}")
                return result
            except ValueError:
                result = left_data < right_data
                logger.debug(f"Comparing string data: {left_data} < {right_data}: {result}")
                return result

    def filterAcceptsRow(self, source_row, source_parent):
        return super().filterAcceptsRow(source_row, source_parent)

# Fungsi inisialisasi DataFrame dan model
def init_market_data_model():
    data_market = pd.DataFrame(columns=['TIME', 'PAIR', '24H %', 'PRICE', 'VOLUME'])
    proxy_model_market = CustomSortFilterProxyModel()
    proxy_model_market.setSourceModel(PandasModel(data_market))
    return data_market, proxy_model_market

def init_account_data_model():
    data_account = pd.DataFrame(columns=['CURRENCY', 'AVAILABLE', 'LOCKED', 'TOTAL'])
    proxy_model_account = CustomSortFilterProxyModel()
    proxy_model_account.setSourceModel(AccountDataModel(data_account))
    return data_account, proxy_model_account

# Fungsi untuk manipulasi data
def delete_market_rows(indices, data_market, proxy_model_market):
    data_market = data_market.drop(indices).reset_index(drop=True)
    proxy_model_market.update_data(data_market)
    return data_market

def delete_account_rows(indices, data_account, proxy_model_account):
    data_account = data_account.drop(indices).reset_index(drop=True)
    proxy_model_account.update_data(data_account)
    return data_account

class AccountDataModel(PandasModel):
    def __init__(self, data):
        super().__init__(data)

    def data(self, index, role=Qt.DisplayRole):
        value = super().data(index, role)
        if role == Qt.DisplayRole and index.column() in [1, 2, 3]:
            # Format nilai saldo dengan 2 desimal untuk kolom "AVAILABLE", "LOCKED", dan "TOTAL"
            return f"{float(value):.2f}"
        return value
