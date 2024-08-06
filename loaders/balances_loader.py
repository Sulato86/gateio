from api.api_gateio import GateIOAPI, api_client
from utils.logging_config import configure_logging
from typing import List, Union

logger = configure_logging('balances_loader', 'logs/balances_loader.log')
api = GateIOAPI(api_client)

def load_balances() -> List[Union[str, float]]:
    logger.debug("Memuat saldo akun di balances_loader")
    try:
        balances = api.get_balances()
        logger.debug(f"Balances received: {balances}")
        
        if not balances or 'spot' not in balances:
            logger.error("Balances data tidak ditemukan atau tidak valid")
            return [["-", 0, 0]]
        
        spot_balances = balances['spot']
        
        if not isinstance(spot_balances, list):
            logger.error(f"Spot balances is not a list. Received: {type(spot_balances)}")
            return [["-", 0, 0]]

        table_data = []

        for balance in spot_balances:
            logger.debug(f"Processing balance: {balance}")
            asset = balance.currency
            available = float(balance.available)
            locked = float(balance.locked)
            if available >= 1 or locked >= 1:
                table_data.append([asset, available, locked])

        if not table_data:
            logger.warning("Tidak ada saldo yang memenuhi kriteria untuk ditampilkan.")
            table_data = [["-", 0, 0]]

        logger.info("Saldo akun berhasil dimuat")
        return table_data
    except KeyError as e:
        logger.error(f"KeyError saat memuat saldo akun: {e}")
        return [["-", 0, 0]]
    except Exception as e:
        logger.error(f"Error tidak terduga saat memuat saldo akun: {e}")
        return [["-", 0, 0]]
