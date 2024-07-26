import pandas as pd
from PyQt5.QtCore import QAbstractTableModel, QSortFilterProxyModel, Qt
from control.logging_config import setup_logging  # Import setup_logging

# Konfigurasi logging
logger = setup_logging('pandasa.log')

class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super(PandasModel, self).__init__()
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
        self.layoutAboutToBeChanged.emit()
        self._data.sort_values(by=[colname], ascending=(order == Qt.AscendingOrder), inplace=True)
        self.layoutChanged.emit()
        logger.debug(f"Data sorted by {colname} in {'ascending' if order == Qt.AscendingOrder else 'descending'} order")

    def update_data(self, data):
        self.layoutAboutToBeChanged.emit()
        self._data = data
        self.layoutChanged.emit()
        logger.debug("Data model updated")

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
        # You can implement custom filtering logic here if needed
        return super().filterAcceptsRow(source_row, source_parent)
