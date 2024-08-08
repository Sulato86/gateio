import pandas as pd
from PyQt5.QtCore import QAbstractTableModel, Qt
from PyQt5.QtGui import QColor, QBrush, QFont
from utils.logging_config import configure_logging

logger = configure_logging('panda_market_data', 'logs/panda_market_data.log')

class PandaMarketData(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._headers = ["TIME", "PAIR", "24%", "PRICE", "VOLUME"]
        self._data = pd.DataFrame(data, columns=self._headers) if data else pd.DataFrame(columns=self._headers)
        self._sort_column = -1
        self._sort_order = Qt.AscendingOrder
        self.sort(self._sort_column, self._sort_order)

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
                if index.column() in [2, 4]:
                    return self.format_percentage_or_volume(value)
                return value

            if role == Qt.BackgroundRole and index.column() == 2:
                return self.get_background_brush(value)

            if role == Qt.ForegroundRole and index.column() == 2:
                return self.get_foreground_brush(value)

        except IndexError:
            return None
        except Exception as e:
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
                if self._sort_column >= 0:
                    self.sort(self._sort_column, self._sort_order)
                self.endResetModel()
        except Exception as e:
            logger.error(f"Error updating data: {e}")

    def import_data(self, headers, new_data):
        try:
            existing_data = self._data.set_index("PAIR").to_dict('index')

            for row in new_data:
                pair = row[1]
                existing_data[pair] = dict(zip(headers, row))

            self._data = pd.DataFrame.from_dict(existing_data, orient='index').reset_index()

            self.beginResetModel()
            if self._sort_column >= 0:
                self.sort(self._sort_column, self._sort_order)
            self.endResetModel()
        except Exception as e:
            logger.error(f"Error importing data: {e}")

    def get_data(self, row: int, column: int):
        if row < 0 or row >= self._data.shape[0] or column < 0 or column >= self._data.shape[1]:
            return None
        return self._data.iat[row, column]

    def sort(self, column: int, order: Qt.SortOrder):
        try:
            if column < 0 or column >= len(self._headers):
                raise ValueError(f"Invalid column index: {column}")
            
            col_name = self._headers[column]
            ascending = (order == Qt.AscendingOrder)
            
            self._sort_column = column
            self._sort_order = order
            
            if col_name in ["24%", "PRICE", "VOLUME"]:
                self._data[col_name] = pd.to_numeric(self._data[col_name], errors='coerce')
            
            self._data.sort_values(by=col_name, ascending=ascending, inplace=True)
            self.beginResetModel()
            self.endResetModel()
        except Exception as e:
            logger.error(f"Error sorting data: {e}")

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

    def get_background_brush(self, value):
        try:
            change_percentage = float(value)
            if change_percentage < 0:
                return QBrush(QColor('red'))
            elif change_percentage > 0:
                return QBrush(QColor('green'))
        except ValueError:
            return None

    def get_foreground_brush(self, value):
        try:
            change_percentage = float(value)
            if change_percentage < 0 or change_percentage > 0:
                return QBrush(QColor('white'))
        except ValueError:
            return None
