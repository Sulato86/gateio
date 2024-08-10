import pandas as pd
from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex
from control.api_handler import ApiHandler

class PandaAccountData(QAbstractTableModel):
    def __init__(self):
        super(PandaAccountData, self).__init__()
        self.api_handler = ApiHandler()
        self.update_data()

    def update_data(self):
        data = self.api_handler.get_balances_data()
        self.df = pd.DataFrame(data, columns=["Asset", "Available", "Locked"])
        self.layoutChanged.emit()

    def sort_data(self, column, order):
        ascending = True if order == Qt.AscendingOrder else False
        column_name = self.df.columns[column]
        self.df.sort_values(by=column_name, ascending=ascending, inplace=True, ignore_index=True)
        self.layoutChanged.emit()

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
