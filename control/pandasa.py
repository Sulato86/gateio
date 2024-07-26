import pandas as pd
from PyQt5.QtCore import QAbstractTableModel, Qt

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

    def update_data(self, data):
        self.layoutAboutToBeChanged.emit()
        self._data = data
        self.layoutChanged.emit()
