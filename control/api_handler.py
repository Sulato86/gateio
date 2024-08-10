from PyQt5.QtCore import QAbstractTableModel, Qt
from api.api_gateio import GateIOAPI, api_client
from utils.logging_config import configure_logging
from typing import List, Union

logger = configure_logging('api_handler', 'logs/api_handler.log')
api = GateIOAPI(api_client)

class ApiHandler(QAbstractTableModel):
    def __init__(self):
        super(ApiHandler, self).__init__()
        self._data = self.load_balances()

    def load_balances(self) -> List[Union[str, float]]:
        try:
            balances = api.get_balances()
            if not balances or 'spot' not in balances:
                return [["-", 0, 0]]
            spot_balances = balances['spot']
            if not isinstance(spot_balances, list):
                return [["-", 0, 0]]
            table_data = []
            for balance in spot_balances:
                asset = balance.currency
                available = float(balance.available)
                locked = float(balance.locked)
                if available >= 1 or locked >= 1:
                    table_data.append([asset, available, locked])
            if not table_data:
                table_data = [["-", 0, 0]]
            return table_data
        except KeyError:
            return [["-", 0, 0]]
        except Exception as e:
            logger.error(f"Gagal memuat saldo: {e}")
            return [["-", 0, 0]]

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self._data[index.row()][index.column()]
            if index.column() in [1, 2]:
                value = round(value, 2)
            return value

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0]) if self._data else 0

    def headerData(self, section, orientation, role):
        headers = ["Asset", "Available", "Locked"]
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return headers[section]
            if orientation == Qt.Vertical:
                return section + 1
