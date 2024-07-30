import os
import logging
from dotenv import load_dotenv
from gate_api import Configuration, ApiClient, SpotApi

# Load environment variables from .env file
load_dotenv()

# Inisialisasi logger
logger = logging.getLogger('api_gateio')
logger.setLevel(logging.DEBUG)

# Handler untuk file logging
file_handler = logging.FileHandler('api_gateio.log')
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Handler untuk console logging
console_handler = logging.StreamHandler()
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# Menambahkan handler ke logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Mendapatkan API key dan API secret dari environment variables
api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')

if not api_key or not api_secret:
    logger.critical("API_KEY dan API_SECRET harus disetel dalam environment variables")
    raise ValueError("API_KEY dan API_SECRET harus disetel dalam environment variables")

# Konfigurasi API
configuration = Configuration(key=api_key, secret=api_secret)
api_client = ApiClient(configuration=configuration)

class GateIOAPI:
    def __init__(self, api_client):
        logger.debug("Inisialisasi GateIOAPI")
        self.api_client = api_client
        self.spot_api = SpotApi(api_client)

    def get_balances(self):
        logger.debug("Memanggil get_balances")
        try:
            balances = self.spot_api.list_spot_accounts()
            logger.info(f"Balances retrieved: {balances}")
            return balances
        except Exception as e:
            logger.error(f"Error getting balances: {e}")
            return None

    def get_order_history(self, currency_pair):
        logger.debug(f"Memanggil get_order_history untuk pasangan mata uang {currency_pair}")
        try:
            orders = self.spot_api.list_orders(currency_pair=currency_pair, status='finished')
            logger.info(f"Order history retrieved: {orders}")
            return orders
        except Exception as e:
            logger.error(f"Error getting order history: {e}")
            return None

    def cancel_order(self, currency_pair, order_id):
        logger.debug(f"Membatalkan order dengan currency_pair: {currency_pair}, order_id: {order_id}")
        try:
            response = self.spot_api.cancel_order(currency_pair, order_id)
            logger.info(f"Order canceled: {response}")
            return response
        except Exception as e:
            logger.error(f"Error canceling order: {e}")
            return None

if __name__ == "__main__":
    logger.debug("Menjalankan script api_gateio.py")

    api = GateIOAPI(api_client)
    
    # Contoh menjalankan fungsi get_balances
    balances = api.get_balances()
    if balances:
        logger.info(f"Balances: {balances}")
    else:
        logger.warning("Balances tidak ditemukan atau gagal diambil")
    
    """# Contoh menjalankan fungsi get_order_history
    orders = api.get_order_history("BTC_USDT")
    if orders:
        logger.info(f"Order history: {orders}")
    else:
        logger.warning("Order history tidak ditemukan atau gagal diambil")"""