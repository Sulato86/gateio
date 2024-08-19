import os
from dotenv import load_dotenv
from gate_api import Configuration, ApiClient, SpotApi, ApiException
from tenacity import retry, stop_after_attempt, wait_fixed
from cachetools import cached, TTLCache
from utils.logging_config import configure_logging

# Load environment variables
load_dotenv()
logger = configure_logging('api_get_balances', 'logs/api_get_balances.log')

def get_api_credentials():
    """
    Mengambil API_KEY dan API_SECRET dari environment variables.
    Jika tidak ditemukan, akan melempar ValueError.
    """
    api_key = os.getenv('API_KEY')
    api_secret = os.getenv('API_SECRET')
    if not api_key or not api_secret:
        raise ValueError("API_KEY dan API_SECRET harus disetel dalam environment variables")
    return api_key, api_secret

# Mendapatkan kredensial API
api_key, api_secret = get_api_credentials()

# Konfigurasi API client
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
        """
        Mengambil saldo akun spot dari API Gate.io.
        Menggunakan caching dan retry otomatis jika terjadi kesalahan.
        """
        try:
            spot_balances = self.spot_api.list_spot_accounts()
            return {'spot': spot_balances}
        except ApiException as e:
            raise
        except Exception as e:
            raise

    def check_rate_limit(self, response, api_type='private'):
        """
        Memeriksa sisa rate limit dari respon API.
        Jika mendekati batas limit, fungsi ini akan mencatat peringatan di logger.
        """
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
        """
        Inisialisasi ApiHandler dengan menggunakan GateIOAPI.
        """
        self.api = GateIOAPI(api_client)

    def get_balances_data(self):
        """
        Mengambil data saldo akun spot dan mengubahnya menjadi format yang lebih mudah dibaca.
        """
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

