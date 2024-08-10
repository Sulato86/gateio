from api.api_gateio import GateIOAPI, api_client
from utils.logging_config import configure_logging
from typing import List, Union

logger = configure_logging('api_handler', 'logs/api_handler.log')
api = GateIOAPI(api_client)

class ApiHandler:
    def __init__(self):
        self._data = self.load_balances()

    def load_balances(self) -> List[Union[str, float]]:
        try:
            balances = api.get_balances()
            if not balances or 'spot' not in balances:
                return [["-", 0, 0]]
            spot_balances = balances['spot']
            table_data = [
                [balance.currency, float(balance.available), float(balance.locked)]
                for balance in spot_balances
            ]
            return table_data if table_data else [["-", 0, 0]]
        except KeyError:
            return [["-", 0, 0]]
        except Exception as e:
            logger.error(f"Gagal memuat saldo: {e}")
            return [["-", 0, 0]]

    def get_balances_data(self) -> List[Union[str, float]]:
        return self._data
