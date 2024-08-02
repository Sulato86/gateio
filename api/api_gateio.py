import os
import logging
from dotenv import load_dotenv
from gate_api import Configuration, ApiClient, SpotApi, MarginApi
from tenacity import retry, stop_after_attempt, wait_fixed
from cachetools import cached, TTLCache

load_dotenv()

logger = logging.getLogger('api_gateio')
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('api_gateio.log')
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

console_handler = logging.StreamHandler()
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')

if not api_key or not api_secret:
    logger.critical("API_KEY dan API_SECRET harus disetel dalam environment variables")
    raise ValueError("API_KEY dan API_SECRET harus disetel dalam environment variables")

configuration = Configuration(key=api_key, secret=api_secret)
api_client = ApiClient(configuration=configuration)

cache = TTLCache(maxsize=10, ttl=5)

class GateIOAPI:
    """
    Kelas untuk berinteraksi dengan API Gate.io.
    """

    def __init__(self, api_client):
        """
        Inisialisasi kelas GateIOAPI.
        
        Args:
            api_client (ApiClient): Klien API yang sudah dikonfigurasi.
        """
        logger.debug("Inisialisasi GateIOAPI")
        self.api_client = api_client
        self.spot_api = SpotApi(api_client)
        self.margin_api = MarginApi(api_client)

    @cached(cache)
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get_balances(self):
        """
        Mendapatkan saldo akun spot dari API Gate.io.
        
        Returns:
            dict: Saldo akun spot.
        """
        logger.debug("Memanggil get_balances")
        try:
            spot_balances = self.spot_api.list_spot_accounts()
            logger.info("Balances retrieved successfully")
            return {
                'spot': spot_balances,
            }
        except Exception as e:
            logger.error(f"Error getting balances: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get_order_history(self, currency_pair):
        """
        Mendapatkan riwayat order untuk pasangan mata uang tertentu.
        
        Args:
            currency_pair (str): Pasangan mata uang.
        
        Returns:
            list: Riwayat order.
        """
        logger.debug(f"Memanggil get_order_history untuk pasangan mata uang {currency_pair}")
        try:
            orders = self.spot_api.list_orders(currency_pair=currency_pair, status='finished')
            logger.info(f"Order history retrieved: {orders}")
            return orders
        except Exception as e:
            logger.error(f"Error getting order history: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def cancel_order(self, currency_pair, order_id):
        """
        Membatalkan order tertentu berdasarkan pasangan mata uang dan ID order.
        
        Args:
            currency_pair (str): Pasangan mata uang.
            order_id (str): ID order.
        
        Returns:
            dict: Respons pembatalan order.
        """
        logger.debug(f"Membatalkan order dengan currency_pair: {currency_pair}, order_id: {order_id}")
        try:
            response = self.spot_api.cancel_order(currency_pair, order_id)
            logger.info(f"Order canceled: {response}")
            return response
        except Exception as e:
            logger.error(f"Error canceling order: {e}")
            raise

if __name__ == "__main__":
    logger.debug("Menjalankan script api_gateio.py")

    api = GateIOAPI(api_client)
    
    try:
        balances = api.get_balances()
        if balances:
            logger.info(f"Balances: {balances}")
        else:
            logger.warning("Balances tidak ditemukan atau gagal diambil")
    except Exception as e:
        logger.error(f"Gagal mendapatkan balances: {e}")
