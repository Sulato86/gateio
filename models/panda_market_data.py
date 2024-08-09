import pandas as pd
import asyncio
from PyQt5.QtCore import QAbstractTableModel, Qt, pyqtSignal, QModelIndex
from PyQt5.QtGui import QColor, QBrush, QFont
from utils.logging_config import configure_logging
from control.websocket_handler import WebSocketHandler

logger = configure_logging('panda_market_data', 'logs/panda_market_data.log')

class PandaMarketData(QAbstractTableModel):
    data_changed = pyqtSignal()

    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self._headers = ["TIME", "PAIR", "24%", "PRICE", "BVOLUME", "QVOLUME"]
        self._data = pd.DataFrame(data, columns=self._headers) if data else pd.DataFrame(columns=self._headers)
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
            for new_row in new_data:
                existing_index = self._data.index[self._data["PAIR"] == new_row[1]].tolist()
                if existing_index:
                    row = existing_index[0]
                    self._data.iloc[row] = new_row
                    self.dataChanged.emit(self.index(row, 0), self.index(row, self.columnCount() - 1))
                else:
                    new_row_df = pd.DataFrame([new_row], columns=self._headers)
                    if not new_row_df.isna().all().all():
                        self._data = pd.concat([self._data, new_row_df], ignore_index=True)
                        self._data.drop_duplicates(subset=["PAIR"], keep="last", inplace=True)
                        self.layoutChanged.emit()
            self.data_changed.emit()
        except Exception as e:
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
        except Exception as e:
            return False

    def delete_pair(self, pair):
        try:
            self.websocket_handler.remove_pair(pair)
            existing_index = self._data.index[self._data["PAIR"] == pair].tolist()
            if existing_index:
                row = existing_index[0]
                self.beginRemoveRows(QModelIndex(), row, row)
                self._data.drop(row, inplace=True)
                self.endRemoveRows()
        except Exception as e:
            pass

    def delete_selected_rows(self, selected_rows):
        try:
            selected_rows.sort(reverse=True)
            for row in selected_rows:
                pair = self._data.iloc[row]["PAIR"]
                self.websocket_handler.remove_pair(pair)
                self.beginRemoveRows(QModelIndex(), row, row)
                self._data.drop(index=row, inplace=True)
                self.endRemoveRows()
            self._data.reset_index(drop=True, inplace=True)
            self.layoutChanged.emit()
        except Exception as e:
            pass

    def sort(self, column: int, order: Qt.SortOrder):
        try:
            if column < 0 or column >= len(self._headers):
                raise ValueError(f"Invalid column index: {column}")
            col_name = self._headers[column]
            ascending = (order == Qt.AscendingOrder)
            if col_name in ["24%", "PRICE", "BVOLUME", "QVOLUME"]:
                self._data[col_name] = pd.to_numeric(self._data[col_name], errors='coerce')
            self._data.sort_values(by=col_name, ascending=ascending, inplace=True)
            self._data.reset_index(drop=True, inplace=True)
            self.layoutChanged.emit()
        except Exception as e:
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
