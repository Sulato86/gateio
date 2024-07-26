import os
import asyncio
import time
from aiohttp import ClientSession, ClientError
from dotenv import load_dotenv
from gate_api import SpotApi, Configuration, ApiClient
from gate_api.exceptions import ApiException

load_dotenv()

class GateioAPI:
    def __init__(self, api_key=None, secret_key=None, rate_limit=10):
        self.api_key = api_key or os.getenv('API_KEY')
        self.secret_key = secret_key or os.getenv('SECRET_KEY')
        self.configuration = Configuration(key=self.api_key, secret=self.secret_key)
        self.api_client = ApiClient(self.configuration)
        self.spot_api = SpotApi(self.api_client)
        self.rate_limit = rate_limit
        self.requests_made = 0
        self.last_request_time = time.time()

    def get_all_symbols(self) -> list:
        try:
            markets = self.spot_api.list_currency_pairs()
            return [market.id for market in markets]
        except ApiException:
            return []

    async def rate_limited_fetch(self, url, session):
        current_time = time.time()
        if self.requests_made >= self.rate_limit and (current_time - self.last_request_time) < 1:
            await asyncio.sleep(1 - (current_time - self.last_request_time))
            self.requests_made = 0
            self.last_request_time = time.time()
        self.requests_made += 1
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()

    async def async_get_ticker_info(self, symbol: str, session: ClientSession) -> dict:
        try:
            data = await self.rate_limited_fetch(f'https://api.gateio.ws/api/v4/spot/tickers?currency_pair={symbol}', session)
            if data:
                return data[0]
            return {}
        except ClientError:
            return {}

    def get_account_balance(self) -> dict:
        try:
            accounts = self.spot_api.list_spot_accounts()
            return {account.currency: account.available for account in accounts}
        except ApiException:
            return {}

    def get_open_orders(self, symbol: str) -> list:
        try:
            open_orders = self.spot_api.list_orders(currency_pair=symbol, status='open')
            return [order.to_dict() for order in open_orders]
        except ApiException:
            return []

    def get_closed_orders(self, symbol: str) -> list:
        try:
            closed_orders = self.spot_api.list_orders(currency_pair=symbol, status='finished')
            return [order.to_dict() for order in closed_orders]
        except ApiException:
            return []

    def get_server_time(self) -> dict:
        try:
            server_time = self.spot_api.get_system_time()
            return server_time.to_dict()
        except ApiException:
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
        except ApiException:
            return {}

    def cancel_order(self, symbol: str, order_id: str) -> dict:
        try:
            cancel_result = self.spot_api.cancel_order(order_id, symbol)
            return cancel_result.to_dict()
        except ApiException:
            return {}

    def get_trade_history(self, symbol: str) -> list:
        try:
            trade_history = self.spot_api.list_my_trades(currency_pair=symbol)
            return [trade.to_dict() for trade in trade_history]
        except ApiException:
            return []

    async def fetch_tickers_for_symbols(self, symbols: list) -> dict:
        async with ClientSession() as session:
            tasks = [self.async_get_ticker_info(symbol, session) for symbol in symbols]
            return await asyncio.gather(*tasks)
