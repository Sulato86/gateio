import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from utils.logging_config import configure_logging
from api.websocket_gateio import GateIOWebSocket

logger = configure_logging('websocket_handler', 'logs/websocket_handler.log')
executor = ThreadPoolExecutor()

class WebSocketHandler:
    def __init__(self, on_data_received):
        logger.debug("Inisialisasi WebSocketHandler")
        self.on_data_received = on_data_received
        self.market_data = []
        self.pairs = set()
        self.deleted_pairs = set()
        self.data_queue = asyncio.Queue()
        self.gateio_ws = GateIOWebSocket(self.on_message, pairs=list(self.pairs))
        self.loop = asyncio.get_event_loop()
        asyncio.ensure_future(self.gateio_ws.run())
        asyncio.ensure_future(self.process_queue())
        logger.debug("WebSocketHandler berhasil diinisialisasi dengan pairs: %s", self.pairs)

    def run_asyncio_loop(self):
        logger.debug("Menjalankan run_asyncio_loop")
        try:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.loop.run_forever()
            logger.debug("Asyncio loop berjalan")
        except Exception as e:
            logger.error(f"Error saat menjalankan asyncio loop: {e}")

    async def process_queue(self):
        while True:
            data = await self.data_queue.get()
            if data:
                self.process_message(data)

    async def on_message(self, data):
        await self.data_queue.put(data)

    def process_message(self, data):
        logger.debug("Menerima data market dari WebSocket")
        logger.debug(f"Data diterima: {data}")
        try:
            result = data.get('result')
            if not result:
                logger.warning("Data result tidak ditemukan dalam payload")
                return

            currency_pair = result.get('currency_pair')
            if not currency_pair:
                logger.warning("currency_pair tidak ditemukan dalam result")
                return

            if currency_pair in self.deleted_pairs:
                logger.debug(f"Pasangan {currency_pair} dihapus, tidak diperbarui")
                return

            market_entry = [
                time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(data['time'])),
                currency_pair,
                result.get('change_percentage', 0.0),
                result.get('last', 0.0),
                result.get('base_volume', 0.0)
            ]
            logger.debug(f"Market entry yang diterima: {market_entry}")

            for i, entry in enumerate(self.market_data):
                if entry[1] == market_entry[1]:
                    self.market_data[i] = market_entry
                    break
            else:
                self.market_data.append(market_entry)

            logger.debug(f"Market data yang diperbarui: {self.market_data}")
            self.on_data_received(self.market_data)
            logger.info("Data market berhasil dimuat dan ditampilkan di tabel")
        except KeyError as e:
            logger.error(f"Error saat memuat data market: KeyError - {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    async def add_pair(self, pair):
        """
        Menambahkan pair baru ke WebSocketHandler.

        Args:
            pair (str): Pasangan mata uang yang akan ditambahkan.
        """
        logger.debug(f"Menambahkan pair baru: {pair}")
        if not pair:
            logger.warning("Pair tidak valid atau kosong")
            return False

        if pair in self.pairs:
            logger.warning(f"Pair {pair} sudah ada dalam pairs")
            return False

        is_valid = await self.gateio_ws.is_valid_pair(pair)
        if not is_valid:
            logger.warning(f"Pair {pair} tidak valid di gate.io")
            return False

        try:
            self.deleted_pairs.discard(pair)
            self.pairs.add(pair)
            await self.gateio_ws.subscribe_to_pair(pair)
            logger.debug(f"Pair {pair} berhasil ditambahkan")
            return True
        except Exception as e:
            logger.error(f"Error saat menambahkan pair {pair}: {e}")
            return False

    def remove_pair(self, pair):
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
        logger.debug(f"Menghapus pair {pair} dari market data")
        self.market_data = [entry for entry in self.market_data if entry[1] != pair]
        self.on_data_received(self.market_data)
        logger.info(f"Pair {pair} berhasil dihapus dari data market. Market data: {self.market_data}")

    def delete_selected_rows(self, pairs):
        logger.debug(f"Menghapus selected rows: {pairs}")
        for pair in pairs:
            self.remove_pair(pair)
            self.remove_pair_from_market_data(pair)

    async def run_blocking_operation(self):
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, self.blocking_operation)
        logger.debug(f"Blocking operation result: {result}")

    def blocking_operation(self):
        # Simulasi operasi yang memakan waktu
        time.sleep(2)
        return "Hasil operasi blocking"
