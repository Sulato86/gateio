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

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        try:
            value = self._data.iat[index.row(), index.column()]

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
            self._data = pd.DataFrame(new_data, columns=self._headers)
            self.endResetModel()
        except Exception:
            pass

    def rowCount(self, index):
        return self._data.shape[0]

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
            existing_data = self._data.set_index("PAIR").to_dict('index')

            for row in new_data:
                pair = row[1]
                existing_data[pair] = dict(zip(headers, row))

            self._data = pd.DataFrame.from_dict(existing_data, orient='index').reset_index()

            self.beginResetModel()
            self.endResetModel()
        except Exception:
            pass

    def get_data(self, row, column):
        if row < 0 or row >= self._data.shape[0] or column < 0 or column >= self._data.shape[1]:
            return None
        return self._data.iat[row, column]
