from PyQt5.QtCore import QAbstractTableModel, Qt
from PyQt5.QtGui import QColor, QBrush, QFont
from utils.logging_config import configure_logging

logger = configure_logging('market_data_table_model', 'logs/market_data_table_model.log')

class MarketDataTableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        self._headers = ["TIME", "PAIR", "24%", "PRICE", "VOLUME"]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        try:
            value = self._data[index.row()][index.column()]

            if role == Qt.DisplayRole:
                if index.column() in [2, 4]:
                    try:
                        return f"{float(value):.2f}"
                    except ValueError:
                        return value
                return value

            if role == Qt.BackgroundRole and index.column() == 2:
                try:
                    change_percentage = float(value)
                    if change_percentage < 0:
                        return QBrush(QColor('red'))
                    elif change_percentage > 0:
                        return QBrush(QColor('green'))
                except ValueError:
                    return None

            if role == Qt.ForegroundRole and index.column() == 2:
                try:
                    change_percentage = float(value)
                    if change_percentage < 0 or change_percentage > 0:
                        return QBrush(QColor('white'))
                except ValueError:
                    return None

        except IndexError:
            return None
        except Exception:
            return None

        return None

    def update_data(self, new_data):
        try:
            self.beginResetModel()
            self._data = new_data
            self.endResetModel()
        except Exception:
            pass

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._headers)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        if role == Qt.FontRole and orientation == Qt.Horizontal:
            font = QFont()
            font.setBold(True)
            return font
        return None

    def import_data(self, headers, new_data):
        try:
            existing_data = {row[1]: row for row in self._data}

            for row in new_data:
                pair = row[1]
                existing_data[pair] = row

            self._data = list(existing_data.values())

            self.beginResetModel()
            self.endResetModel()
        except Exception:
            pass

    def remove_rows(self, rows):
        try:
            self.beginResetModel()
            self._data = [row for i, row in enumerate(self._data) if i not in rows]
            self.endResetModel()
        except Exception:
            pass

    def get_data(self, row, column):
        if row < 0 or row >= len(self._data) or column < 0 or column >= len(self._headers):
            return None
        return self._data[row][column]

    def find_row_by_pair(self, pair):
        for row in range(len(self._data)):
            if self._data[row][1] == pair:
                return row
        return -1
