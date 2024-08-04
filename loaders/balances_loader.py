from api.api_gateio import GateIOAPI, api_client
from utils.logging_config import configure_logging

logger = configure_logging('balances_loader', 'logs/balances_loader.log')

# Inisialisasi objek API
api = GateIOAPI(api_client)

def load_balances():
    """
    Memuat saldo akun dari API Gate.io.

    Returns:
        list: Data saldo dalam bentuk list yang siap ditampilkan di tabel.
    """
    logger.debug("Memuat saldo akun di balances_loader")
    try:
        balances = api.get_balances()
        logger.debug(f"Balances received: {balances}")
        spot_balances = balances.get('spot', [])
        
        if isinstance(spot_balances, list):
            logger.debug(f"Spot balances is a list dengan {len(spot_balances)} items.")
        else:
            logger.error(f"Spot balances is not a list. Received: {type(spot_balances)}")

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
    except Exception as e:
        logger.error(f"Error saat memuat saldo akun: {e}")
        return [["-", 0, 0]]
