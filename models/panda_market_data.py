import pandas as pd
import asyncio
from PyQt5.QtCore import QAbstractTableModel, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QBrush, QFont
from utils.logging_config import configure_logging
from control.websocket_handler import WebSocketHandler

logger = configure_logging('panda_market_data', 'logs/panda_market_data.log')


class PandaMarketData(QAbstractTableModel):
    data_changed = pyqtSignal()

    def __init__(self, data):
        super().__init__()
        self._headers = ["TIME", "PAIR", "24%", "PRICE", "BVOLUME", "QVOLUME"]
        self._data = pd.DataFrame(data, columns=self._headers) if data else pd.DataFrame(columns=self._headers)
        self._sort_column = -1
        self._sort_order = Qt.AscendingOrder
        self.websocket_handler = WebSocketHandler(self)
        self.websocket_handler.start()

    def rowCount(self, index=None) -> int:
        return self._data.shape[0]

    def columnCount(self, index=None) -> int:
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        try:
            value = self._data.iat[index.row(), index.column()]
            if role == Qt.DisplayRole:
                if index.column() == 3:
                    return self.format_price(value)
                if index.column() in [2, 4, 5]:
                    return self.format_percentage_or_volume(value)
                return value
            if role in [Qt.BackgroundRole, Qt.ForegroundRole] and index.column() == 2:
                return self.get_brush(value, role)
        except (IndexError, ValueError):
            return None
        return None

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        if role == Qt.FontRole and orientation == Qt.Horizontal:
            font = QFont()
            font.setBold(True)
            return font
        return None

    def update_data(self, new_data):
        try:
            new_df = pd.DataFrame(new_data, columns=self._headers)
            if not new_df.equals(self._data):
                self.beginResetModel()
                self._data = new_df
                self.endResetModel()
                self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount()-1, self.columnCount()-1))
                self.data_changed.emit()
        except Exception:
            pass

    def add_pair(self, pair):
        if not pair:
            return False
        try:
            future = asyncio.run_coroutine_threadsafe(
                self.websocket_handler.add_pair(pair),
                self.websocket_handler.loop
            )
            is_added = future.result()
            return is_added
        except Exception:
            return False

    def get_data(self, row: int, column: int):
        try:
            if row < 0 or row >= self._data.shape[0] or column < 0 or column >= self._data.shape[1]:
                return None
            return self._data.iat[row, column]
        except Exception:
            return None

    def sort(self, column: int, order: Qt.SortOrder):
        try:
            if column < 0 or column >= len(self._headers):
                raise ValueError(f"Invalid column index: {column}")
            col_name = self._headers[column]
            ascending = (order == Qt.AscendingOrder)
            self._sort_column = column
            self._sort_order = order
            if col_name in ["24%", "PRICE", "BVOLUME", "QVOLUME"]:
                self._data[col_name] = pd.to_numeric(self._data[col_name], errors='coerce')
            self._data.sort_values(by=col_name, ascending=ascending, inplace=True)
            self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount()-1, self.columnCount()-1))
        except Exception:
            pass

    def format_price(self, value):
        try:
            return f"{float(value)}"
        except ValueError:
            return value

    def format_percentage_or_volume(self, value):
        try:
            return f"{float(value):.2f}"
        except ValueError:
            return value

    def get_brush(self, value, role):
        try:
            change_percentage = float(value)
            if role == Qt.BackgroundRole:
                if change_percentage < 0:
                    return QBrush(QColor('red'))
                elif change_percentage > 0:
                    return QBrush(QColor('green'))
            elif role == Qt.ForegroundRole:
                if change_percentage < 0 or change_percentage > 0:
                    return QBrush(QColor('white'))
        except ValueError:
            return None
