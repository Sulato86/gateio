import pandas as pd
from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, QTimer
from control.api_handler import ApiHandler

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
        data = self.api_handler.get_balances_data()
        self.df = pd.DataFrame(data, columns=["Asset", "Available", "Locked"])
        if self.sort_column is not None:
            self.sort_data(self.sort_column, self.sort_order)
        else:
            self.layoutChanged.emit()

    def sort_data(self, column, order):
        self.sort_column = column
        self.sort_order = order
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
