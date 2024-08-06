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
        raise ValueError("API_KEY dan API_SECRET harus disetel dalam environment variables")
    return api_key, api_secret

api_key, api_secret = get_api_credentials()
configuration = Configuration(key=api_key, secret=api_secret)
api_client = ApiClient(configuration=configuration)
cache = TTLCache(maxsize=10, ttl=5)

class GateIOAPI:
    def __init__(self, api_client):
        self.api_client = api_client
        self.spot_api = SpotApi(api_client)

    @cached(cache)
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get_balances(self):
        try:
            spot_balances = self.spot_api.list_spot_accounts()
            return {'spot': spot_balances}
        except ApiException as e:
            raise
        except Exception as e:
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get_order_history(self, currency_pair):
        try:
            orders = self.spot_api.list_orders(currency_pair=currency_pair, status='finished')
            return orders
        except ApiException as e:
            raise
        except Exception as e:
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def cancel_order(self, currency_pair, order_id):
        try:
            response = self.spot_api.cancel_order(currency_pair, order_id)
            return response
        except ApiException as e:
            raise
        except Exception as e:
            raise
