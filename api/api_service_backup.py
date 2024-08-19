import os
import requests
from dotenv import load_dotenv
from gate_api import Configuration, ApiClient, SpotApi, ApiException
from tenacity import retry, stop_after_attempt, wait_fixed
from cachetools import cached, TTLCache
from utils.logging_config import configure_logging

# Load environment variables
load_dotenv()
logger = configure_logging('api_service', 'logs/api_service.log')

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
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def place_order(self, currency_pair, amount, price, side):
        try:
            order = self.spot_api.create_order(
                currency_pair=currency_pair,
                amount=str(amount),
                price=str(price),
                side=side
            )
            return order
        except ApiException as e:
            raise
        except Exception as e:
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get_order_status(self, currency_pair, order_id):
        try:
            order_status = self.spot_api.get_order(currency_pair, order_id)
            return order_status
        except ApiException as e:
            raise
        except Exception as e:
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get_trade_history(self, currency_pair):
        try:
            trade_history = self.spot_api.list_trades(currency_pair=currency_pair)
            return trade_history
        except ApiException as e:
            raise
        except Exception as e:
            raise
    
    def check_rate_limit(self, response, api_type='private'):
        rate_limit_remaining = int(response.headers.get('X-Rate-Limit-Remaining', 0))
        rate_limit_reset = int(response.headers.get('X-Rate-Limit-Reset', 0))
        if api_type == 'private':
            rate_limit_threshold = 10
        else:
            rate_limit_threshold = 100
        if rate_limit_remaining < rate_limit_threshold * 0.1:
            logger.warning(f"Mendekati batas rate limit API. Sisa: {rate_limit_remaining}. Akan direset pada: {rate_limit_reset}.")

class ApiHandler:
    def __init__(self):
        self.api = GateIOAPI(api_client)

    def load_balances(self):
        try:
            balances = self.api.get_balances()
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

    def get_balances_data(self):
        return self.load_balances()

    def get_order_history(self, currency_pair):
        try:
            return self.api.get_order_history(currency_pair)
        except Exception as e:
            logger.error(f"Gagal memuat riwayat order: {e}")
            return []

    def cancel_order(self, currency_pair, order_id):
        try:
            return self.api.cancel_order(currency_pair, order_id)
        except Exception as e:
            logger.error(f"Gagal membatalkan order: {e}")
            return {"error": "Gagal membatalkan order"}

    def place_order(self, currency_pair, amount, price, side):
        try:
            return self.api.place_order(currency_pair, amount, price, side)
        except Exception as e:
            logger.error(f"Gagal membuat order: {e}")
            return {"error": "Gagal membuat order"}

    def get_order_status(self, currency_pair, order_id):
        try:
            return self.api.get_order_status(currency_pair, order_id)
        except Exception as e:
            logger.error(f"Gagal memuat status order: {e}")
            return {}

    def get_trade_history(self, currency_pair):
        try:
            return self.api.get_trade_history(currency_pair)
        except Exception as e:
            logger.error(f"Gagal memuat riwayat perdagangan: {e}")
            return []
