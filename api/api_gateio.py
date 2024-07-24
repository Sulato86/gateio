import os
import asyncio
from dotenv import load_dotenv
import requests
from aiohttp import ClientSession
from tenacity import retry, wait_fixed, stop_after_attempt

# Memuat variabel lingkungan dari file .env
load_dotenv()

class GateioAPI:
    def __init__(self):
        self.api_key = os.getenv('API_KEY')
        self.secret_key = os.getenv('SECRET_KEY')
        self.base_url = 'https://api.gateio.ws/api/v4'
        self.headers = {
            'Content-Type': 'application/json'
        }
        self.auth_headers = {
            'Content-Type': 'application/json',
            'KEY': self.api_key,
            'SIGN': self.secret_key
        }

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(5))
    def get_all_symbols(self) -> list:
        url = f"{self.base_url}/spot/currency_pairs"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            markets = response.json()
            return [market['id'] for market in markets]
        except requests.exceptions.RequestException as e:
            return []

    async def async_get_ticker_info(self, symbol: str, session: ClientSession) -> dict:
        url = f"{self.base_url}/spot/tickers?currency_pair={symbol}"
        try:
            async with session.get(url, headers=self.headers) as response:
                response.raise_for_status()
                ticker = await response.json()
                if ticker:
                    ticker = ticker[0]
                    return {
                        'last_price': ticker['last'],
                        '24h_change': ticker['change_percentage'],
                        'volume': ticker['base_volume']
                    }
                return None
        except Exception as e:
            return None

    async def async_get_order_book(self, symbol: str, session: ClientSession, limit: int = 10) -> dict:
        url = f"{self.base_url}/spot/order_book?currency_pair={symbol}&limit={limit}"
        try:
            async with session.get(url, headers=self.headers) as response:
                response.raise_for_status()
                order_book = await response.json()
                return order_book
        except Exception as e:
            return None

    def get_account_balance(self) -> dict:
        url = f"{self.base_url}/spot/accounts"
        try:
            response = requests.get(url, headers=self.auth_headers)
            response.raise_for_status()
            balance = response.json()
            return balance
        except requests.exceptions.RequestException as e:
            return None

    def get_open_orders(self, symbols: list) -> dict:
        all_open_orders = {}
        for symbol in symbols:
            url = f"{self.base_url}/spot/open_orders?currency_pair={symbol}"
            try:
                response = requests.get(url, headers=self.auth_headers)
                response.raise_for_status()
                open_orders = response.json()
                all_open_orders[symbol] = open_orders
            except requests.exceptions.RequestException as e:
                pass
        return all_open_orders

    def get_closed_orders(self, symbols: list) -> dict:
        all_closed_orders = {}
        for symbol in symbols:
            url = f"{self.base_url}/spot/closed_orders?currency_pair={symbol}"
            try:
                response = requests.get(url, headers=self.auth_headers)
                response.raise_for_status()
                closed_orders = response.json()
                all_closed_orders[symbol] = closed_orders
            except requests.exceptions.RequestException as e:
                pass
        return all_closed_orders

    def get_server_time(self) -> dict:
        url = f"{self.base_url}/spot/time"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            server_time = response.json()
            return server_time
        except requests.exceptions.RequestException as e:
            return None

    def create_order(self, symbol: str, side: str, amount: float, price: float) -> dict:
        url = f"{self.base_url}/spot/orders"
        data = {
            "currency_pair": symbol,
            "type": "limit",
            "side": side,
            "amount": str(amount),
            "price": str(price)
        }
        try:
            response = requests.post(url, headers=self.auth_headers, json=data)
            response.raise_for_status()
            order = response.json()
            return order
        except requests.exceptions.RequestException as e:
            return None

    def cancel_order(self, symbol: str, order_id: str) -> dict:
        url = f"{self.base_url}/spot/orders/{order_id}"
        try:
            response = requests.delete(url, headers=self.auth_headers)
            response.raise_for_status()
            cancel_result = response.json()
            return cancel_result
        except requests.exceptions.RequestException as e:
            return None

    def get_trade_history(self, symbol: str) -> list:
        url = f"{self.base_url}/spot/my_trades?currency_pair={symbol}"
        try:
            response = requests.get(url, headers=self.auth_headers)
            response.raise_for_status()
            trade_history = response.json()
            return trade_history
        except requests.exceptions.RequestException as e:
            return []

async def fetch_data_every_15_seconds(api, symbol):
    async with ClientSession() as session:
        while True:
            ticker_info = await api.async_get_ticker_info(symbol, session)
            print(f"Ticker info for {symbol}: {ticker_info}")
            await asyncio.sleep(15)
