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
        self.pairs = []
        self.deleted_pairs = set()
        self.gateio_ws = GateIOWebSocket(self.on_message, pairs=self.pairs)
        self.loop = asyncio.get_event_loop()
        asyncio.ensure_future(self.gateio_ws.run())
        logger.debug("WebSocketHandler berhasil diinisialisasi dengan pairs: %s", self.pairs)

    def run_asyncio_loop(self):
        """
        Menjalankan loop asyncio.
        """
        logger.debug("Menjalankan run_asyncio_loop")
        try:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.loop.run_forever()
            logger.debug("Asyncio loop berjalan")
        except Exception as e:
            logger.error(f"Error saat menjalankan asyncio loop: {e}")

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
            currency_pair = result['currency_pair']
            if currency_pair in self.deleted_pairs:
                logger.debug(f"Pasangan {currency_pair} dihapus, tidak diperbarui")
                return

            market_entry = [
                time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(data['time'])),
                currency_pair,
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
            self.deleted_pairs.discard(pair)
            self.pairs.append(pair)
            asyncio.run_coroutine_threadsafe(self.gateio_ws.subscribe_to_pair(pair), self.loop)
            logger.debug(f"Pair {pair} berhasil ditambahkan")
        except Exception as e:
            logger.error(f"Error saat menambahkan pair {pair}: {e}")

    def remove_pair(self, pair):
        """
        Menghapus pasangan mata uang dari WebSocket.

        Args:
            pair (str): Pasangan mata uang yang akan dihapus.
        """
        logger.debug(f"Menghapus pair: {pair}")
        if pair in self.pairs:
            try:
                asyncio.run_coroutine_threadsafe(self.gateio_ws.unsubscribe_from_pair(pair), self.loop)
                self.deleted_pairs.add(pair)
                self.pairs.remove(pair)
                logger.debug(f"Pair {pair} berhasil dihapus. Pairs: {self.pairs}, Deleted pairs: {self.deleted_pairs}")
            except Exception as e:
                logger.error(f"Error saat menghapus pair {pair}: {e}")
        else:
            logger.warning(f"Pair {pair} tidak ditemukan dalam pairs. Pairs: {self.pairs}")

    def remove_pair_from_market_data(self, pair):
        """
        Menghapus pasangan mata uang dari data market.

        Args:
            pair (str): Pasangan mata uang yang akan dihapus.
        """
        logger.debug(f"Menghapus pair {pair} dari market data")
        self.market_data = [entry for entry in self.market_data if entry[1] != pair]
        self.on_data_received(self.market_data)
        logger.info(f"Pair {pair} berhasil dihapus dari data market. Market data: {self.market_data}")

    def delete_selected_rows(self, pairs):
        """
        Menghapus pasangan mata uang yang dipilih dari data market dan WebSocket.

        Args:
            pairs (list): Daftar pasangan mata uang yang dipilih.
        """
        logger.debug(f"Menghapus selected rows: {pairs}")
        for pair in pairs:
            self.remove_pair(pair)
            self.remove_pair_from_market_data(pair)
