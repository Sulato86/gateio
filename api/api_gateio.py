import os
import asyncio
import logging
from aiohttp import ClientSession, ClientError
from dotenv import load_dotenv
from gate_api import SpotApi, Configuration, ApiClient
from gate_api.exceptions import ApiException
import time

# Memuat variabel lingkungan dari file .env
load_dotenv()

# Konfigurasi logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Handler untuk logging ke file
file_handler = logging.FileHandler('api_gateio.log')
file_handler.setLevel(logging.DEBUG)

# Handler untuk logging ke console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Format logging
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Menambahkan handler ke logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

class GateioAPI:
    def __init__(self, api_key=None, secret_key=None, rate_limit=10):
        self.api_key = api_key or os.getenv('API_KEY')
        self.secret_key = secret_key or os.getenv('SECRET_KEY')
        self.configuration = Configuration(
            key=self.api_key,
            secret=self.secret_key
        )
        self.api_client = ApiClient(self.configuration)
        self.spot_api = SpotApi(self.api_client)
        self.rate_limit = rate_limit  # Max requests per second
        logger.debug("GateioAPI instance created with rate_limit: %d", rate_limit)

    def get_all_symbols(self) -> list:
        try:
            markets = self.spot_api.list_currency_pairs()
            return [market.id for market in markets]
        except ApiException as e:
            logger.error(f"Error getting all symbols: {e}")
            return []

    async def async_get_ticker_info(self, symbol: str, session: ClientSession) -> dict:
        try:
            async with session.get(f'https://api.gateio.ws/api/v4/spot/tickers?currency_pair={symbol}') as response:
                if response.status == 200:
                    ticker = await response.json()
                    return ticker[0]
                else:
                    logger.error(f"Error: Received status code {response.status} for symbol {symbol}")
                    return {}
        except asyncio.TimeoutError:
            logger.error(f"Request timed out for {symbol}")
        except ClientError as e:
            logger.error(f"Client error: {e}")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
        return {}

    def get_account_balance(self) -> dict:
        try:
            accounts = self.spot_api.list_spot_accounts()
            return {account.currency: account.available for account in accounts}
        except ApiException as e:
            logger.error(f"Error getting account balance: {e}")
            return {}

    def get_open_orders(self, symbol: str) -> list:
        try:
            open_orders = self.spot_api.list_orders(currency_pair=symbol, status='open')
            return [order.to_dict() for order in open_orders]
        except ApiException as e:
            logger.error(f"Error getting open orders for {symbol}: {e}")
            return []

    def get_closed_orders(self, symbol: str) -> list:
        try:
            closed_orders = self.spot_api.list_orders(currency_pair=symbol, status='finished')
            return [order.to_dict() for order in closed_orders]
        except ApiException as e:
            logger.error(f"Error getting closed orders for {symbol}: {e}")
            return []

    def get_server_time(self) -> dict:
        try:
            server_time = self.spot_api.get_system_time()
            return server_time.to_dict()
        except ApiException as e:
            logger.error(f"Error getting server time: {e}")
            return {}

    def create_order(self, symbol: str, side: str, amount: float, price: float) -> dict:
        order = {
            "currency_pair": symbol,
            "type": "limit",
            "side": side,
            "amount": str(amount),
            "price": str(price)
        }
        try:
            order_result = self.spot_api.create_order(order)
            return order_result.to_dict()
        except ApiException as e:
            logger.error(f"Error creating order for {symbol}: {e}")
            return {}

    def cancel_order(self, symbol: str, order_id: str) -> dict:
        try:
            cancel_result = self.spot_api.cancel_order(order_id, symbol)
            return cancel_result.to_dict()
        except ApiException as e:
            logger.error(f"Error canceling order {order_id} for {symbol}: {e}")
            return {}

    def get_trade_history(self, symbol: str) -> list:
        try:
            trade_history = self.spot_api.list_my_trades(currency_pair=symbol)
            return [trade.to_dict() for trade in trade_history]
        except ApiException as e:
            logger.error(f"Error getting trade history for {symbol}: {e}")
            return []

    async def rate_limited_fetch(self, url, symbol, session):
        while True:
            start_time = time.time()
            data = await self.async_get_ticker_info(symbol, session)
            end_time = time.time()
            elapsed_time = end_time - start_time
            if elapsed_time < 1 / self.rate_limit:
                await asyncio.sleep(1 / self.rate_limit - elapsed_time)
            return data

    async def fetch_tickers_for_symbols(self, symbols: list) -> dict:
        async with ClientSession() as session:
            tasks = [self.rate_limited_fetch(f'https://api.gateio.ws/api/v4/spot/tickers?currency_pair={symbol}', symbol, session) for symbol in symbols]
            return await asyncio.gather(*tasks)
