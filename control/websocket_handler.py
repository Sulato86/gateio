import asyncio
import time
from utils.logging_config import configure_logging
from api.websocket_gateio import GateIOWebSocket

logger = configure_logging('websocket_handler', 'logs/websocket_handler.log')

class WebSocketHandler:
    def __init__(self, on_data_received):
        logger.debug("Inisialisasi WebSocketHandler")
        self.on_data_received = on_data_received
        self.market_data = []
        self.pairs = ["BTC_USDT", "ETH_USDT"]
        self.gateio_ws = GateIOWebSocket(self.on_message, pairs=self.pairs)
        self.loop = asyncio.get_event_loop()
        asyncio.ensure_future(self.gateio_ws.run())
        logger.debug("WebSocketHandler berhasil diinisialisasi dengan pairs: %s", self.pairs)

    def run_asyncio_loop(self):
        """
        Menjalankan loop asyncio.
        """
        logger.debug("Menjalankan run_asyncio_loop")
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.loop.run_forever()
        logger.debug("Asyncio loop berjalan")

    def on_message(self, data):
        """
        Memproses data yang diterima dari WebSocket.

        Args:
            data (dict): Data dari WebSocket.
        """
        logger.debug("Menerima data market dari WebSocket")
        logger.debug(f"Data diterima: {data}")
        try:
            result = data['result']
            market_entry = [
                time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data['time'])),
                result['currency_pair'],
                result['change_percentage'],
                result['last'],
                result['base_volume']
            ]
            logger.debug(f"Market entry yang diterima: {market_entry}")
            updated = False
            for i, entry in enumerate(self.market_data):
                if entry[1] == market_entry[1]:
                    self.market_data[i] = market_entry
                    updated = True
                    break
            if not updated:
                self.market_data.append(market_entry)
            logger.debug(f"Market data yang diperbarui: {self.market_data}")
            self.on_data_received(self.market_data)
            logger.info("Data market berhasil dimuat dan ditampilkan di tabel")
        except KeyError as e:
            logger.error(f"Error saat memuat data market: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    def add_pair(self, pair):
        """
        Menambahkan pasangan mata uang baru ke WebSocket.

        Args:
            pair (str): Pasangan mata uang baru.
        """
        logger.debug(f"Menambahkan pair baru: {pair}")
        try:
            asyncio.run_coroutine_threadsafe(self.gateio_ws.subscribe_to_pair(pair), self.loop)
            logger.debug(f"Pair {pair} berhasil ditambahkan")
        except Exception as e:
            logger.error(f"Error saat menambahkan pair {pair}: {e}")
