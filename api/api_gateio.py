import os
from utils.logging_config import configure_logging
from dotenv import load_dotenv
from gate_api import Configuration, ApiClient, SpotApi, ApiException
from tenacity import retry, stop_after_attempt, wait_fixed
from cachetools import cached, TTLCache

load_dotenv()
logger = configure_logging('api_gateio', 'logs/api_gateio.log')

def get_api_credentials():
    api_key = os.getenv('API_KEY')
    api_secret = os.getenv('API_SECRET')
    if not api_key or not api_secret:
        logger.critical("API_KEY dan API_SECRET harus disetel dalam environment variables")
        raise ValueError("API_KEY dan API_SECRET harus disetel dalam environment variables")
    return api_key, api_secret

api_key, api_secret = get_api_credentials()
configuration = Configuration(key=api_key, secret=api_secret)
api_client = ApiClient(configuration=configuration)
cache = TTLCache(maxsize=10, ttl=5)

class GateIOAPI:
    def __init__(self, api_client):
        logger.debug("Inisialisasi GateIOAPI")
        self.api_client = api_client
        self.spot_api = SpotApi(api_client)

    @cached(cache)
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get_balances(self):
        logger.debug("Memanggil get_balances")
        try:
            spot_balances = self.spot_api.list_spot_accounts()
            logger.info("Balances retrieved successfully")
            return {'spot': spot_balances}
        except ApiException as e:
            logger.error(f"API exception saat mendapatkan balances: {e}")
            raise
        except Exception as e:
            logger.error(f"Error saat mendapatkan balances: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get_order_history(self, currency_pair):
        logger.debug(f"Memanggil get_order_history untuk pasangan mata uang {currency_pair}")
        try:
            orders = self.spot_api.list_orders(currency_pair=currency_pair, status='finished')
            logger.info(f"Order history retrieved: {orders}")
            return orders
        except ApiException as e:
            logger.error(f"API exception saat mendapatkan riwayat order: {e}")
            raise
        except Exception as e:
            logger.error(f"Error saat mendapatkan riwayat order: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def cancel_order(self, currency_pair, order_id):
        logger.debug(f"Membatalkan order dengan currency_pair: {currency_pair}, order_id: {order_id}")
        try:
            response = self.spot_api.cancel_order(currency_pair, order_id)
            logger.info(f"Order canceled: {response}")
            return response
        except ApiException as e:
            logger.error(f"API exception saat membatalkan order: {e}")
            raise
        except Exception as e:
            logger.error(f"Error saat membatalkan order: {e}")
            raise

