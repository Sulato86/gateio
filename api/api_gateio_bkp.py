import os
import asyncio
import time
from aiohttp import ClientSession, ClientError
from dotenv import load_dotenv
from gate_api import SpotApi, Configuration, ApiClient
from gate_api.exceptions import ApiException
from control.logging_config import setup_logging

# Memuat variabel lingkungan dari file .env
load_dotenv()

# Konfigurasi logging
logger = setup_logging('api_gateio.log')

class GateioAPI:
    def __init__(self, api_key=None, secret_key=None, rate_limit=10):
        """
        Inisialisasi instance GateioAPI dengan konfigurasi yang diberikan atau dari variabel lingkungan.
        
        :param api_key: Kunci API Gate.io.
        :param secret_key: Kunci rahasia API Gate.io.
        :param rate_limit: Batas kecepatan permintaan API per detik.
        """
        self.api_key = api_key or os.getenv('API_KEY')
        self.secret_key = secret_key or os.getenv('SECRET_KEY')
        self.configuration = Configuration(key=self.api_key, secret=self.secret_key)
        self.api_client = ApiClient(self.configuration)
        self.spot_api = SpotApi(self.api_client)
        self.rate_limit = rate_limit
        self.requests_made = 0
        self.last_request_time = time.time()
        logger.debug("GateioAPI instance created with rate_limit: %d", rate_limit)

    def get_all_symbols(self) -> list:
        """
        Mendapatkan semua simbol pasar yang tersedia dari Gate.io.

        :return: Daftar semua simbol pasar.
        """
        try:
            markets = self.spot_api.list_currency_pairs()
            return [market.id for market in markets]
        except ApiException as e:
            logger.error(f"Error getting all symbols: {e}")
            return []

    async def rate_limited_fetch(self, url, session):
        """
        Mengambil data dari URL dengan membatasi kecepatan permintaan sesuai dengan rate limit yang ditentukan.

        :param url: URL untuk mengambil data.
        :param session: Sesi klien aiohttp.
        :return: Data JSON dari respons.
        """
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
        """
        Mendapatkan informasi ticker untuk simbol tertentu secara asinkron.

        :param symbol: Simbol pasar yang diinginkan.
        :param session: Sesi klien aiohttp.
        :return: Data ticker dalam bentuk dictionary.
        """
        try:
            data = await self.rate_limited_fetch(f'https://api.gateio.ws/api/v4/spot/tickers?currency_pair={symbol}', session)
            logger.debug(f"Data received for {symbol}: {data}")
            if data:
                return data[0]
            return {}
        except ClientError as e:
            logger.error(f"Error getting ticker info for {symbol}: {e}")
        return {}

    def get_account_balance(self) -> dict:
        """
        Mendapatkan saldo akun spot pengguna.

        :return: Saldo akun dalam bentuk dictionary dengan mata uang sebagai kunci.
        """
        try:
            accounts = self.spot_api.list_spot_accounts()
            return {account.currency: account.available for account in accounts}
        except ApiException as e:
            logger.error(f"Error getting account balance: {e}")
            return {}

    def get_open_orders(self, symbol: str) -> list:
        """
        Mendapatkan daftar pesanan terbuka untuk simbol tertentu.

        :param symbol: Simbol pasar yang diinginkan.
        :return: Daftar pesanan terbuka dalam bentuk dictionary.
        """
        try:
            open_orders = self.spot_api.list_orders(currency_pair=symbol, status='open')
            return [order.to_dict() for order in open_orders]
        except ApiException as e:
            logger.error(f"Error getting open orders for {symbol}: {e}")
            return []

    def get_closed_orders(self, symbol: str) -> list:
        """
        Mendapatkan daftar pesanan yang sudah selesai untuk simbol tertentu.

        :param symbol: Simbol pasar yang diinginkan.
        :return: Daftar pesanan selesai dalam bentuk dictionary.
        """
        try:
            closed_orders = self.spot_api.list_orders(currency_pair=symbol, status='finished')
            return [order.to_dict() for order in closed_orders]
        except ApiException as e:
            logger.error(f"Error getting closed orders for {symbol}: {e}")
            return []

    def get_server_time(self) -> dict:
        """
        Mendapatkan waktu server dari Gate.io.

        :return: Waktu server dalam bentuk dictionary.
        """
        try:
            server_time = self.spot_api.get_system_time()
            return server_time.to_dict()
        except ApiException as e:
            logger.error(f"Error getting server time: {e}")
            return {}

    def create_order(self, symbol: str, side: str, amount: float, price: float) -> dict:
        """
        Membuat pesanan beli/jual untuk simbol tertentu.

        :param symbol: Simbol pasar yang diinginkan.
        :param side: Sisi pesanan, 'buy' atau 'sell'.
        :param amount: Jumlah yang ingin dibeli/dijual.
        :param price: Harga yang diinginkan.
        :return: Hasil pesanan dalam bentuk dictionary.
        """
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
        """
        Membatalkan pesanan untuk simbol tertentu.

        :param symbol: Simbol pasar yang diinginkan.
        :param order_id: ID pesanan yang ingin dibatalkan.
        :return: Hasil pembatalan dalam bentuk dictionary.
        """
        try:
            cancel_result = self.spot_api.cancel_order(order_id, symbol)
            return cancel_result.to_dict()
        except ApiException as e:
            logger.error(f"Error canceling order {order_id} for {symbol}: {e}")
            return {}

    def get_trade_history(self, symbol: str) -> list:
        """
        Mendapatkan riwayat perdagangan untuk simbol tertentu.

        :param symbol: Simbol pasar yang diinginkan.
        :return: Daftar riwayat perdagangan dalam bentuk dictionary.
        """
        try:
            trade_history = self.spot_api.list_my_trades(currency_pair=symbol)
            return [trade.to_dict() for trade in trade_history]
        except ApiException as e:
            logger.error(f"Error getting trade history for {symbol}: {e}")
            return []

    async def fetch_tickers_for_symbols(self, symbols: list) -> dict:
        """
        Mengambil data ticker untuk daftar simbol secara asinkron.

        :param symbols: Daftar simbol pasar.
        :return: Data ticker untuk semua simbol dalam bentuk dictionary.
        """
        async with ClientSession() as session:
            tasks = [self.async_get_ticker_info(symbol, session) for symbol in symbols]
            return await asyncio.gather(*tasks)
