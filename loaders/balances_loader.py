from api.api_gateio import GateIOAPI, api_client
from utils.logging_config import configure_logging
from typing import List, Union

logger = configure_logging('balances_loader', 'logs/balances_loader.log')
api = GateIOAPI(api_client)

def load_balances() -> List[Union[str, float]]:
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
    except Exception:
        return [["-", 0, 0]]
