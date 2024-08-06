import asyncio
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from utils.logging_config import configure_logging
from api.websocket_gateio import GateIOWebSocket
from PyQt5.QtCore import QObject, pyqtSignal

logger = configure_logging('websocket_handler', 'logs/websocket_handler.log')
executor = ThreadPoolExecutor()

class WebSocketHandler(QObject):
    market_data_updated = pyqtSignal(list)

    def __init__(self, on_data_received):
        super().__init__()
        self.on_data_received = on_data_received
        self.market_data = []
        self.pairs = set()
        self.deleted_pairs = set()
        self.data_queue = asyncio.Queue()
        self.gateio_ws = GateIOWebSocket(self.on_message, pairs=list(self.pairs))
        self.loop = asyncio.new_event_loop()

    def start(self):
        threading.Thread(target=self.run_loop, daemon=True).start()

    def run_loop(self):
        asyncio.set_event_loop(self.loop)
        asyncio.run_coroutine_threadsafe(self.gateio_ws.run(), self.loop)
        asyncio.run_coroutine_threadsafe(self.process_queue(), self.loop)
        self.loop.run_forever()

    async def process_queue(self):
        while True:
            data = await self.data_queue.get()
            if data:
                self.process_message(data)

    async def on_message(self, data):
        await self.data_queue.put(data)

    def process_message(self, data):
        try:
            result = data.get('result')
            if not result:
                return

            currency_pair = result.get('currency_pair')
            if not currency_pair:
                return

            timestamp = data.get('time')
            if not timestamp:
                return

            market_entry = [
                time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(timestamp)),
                currency_pair,
                result.get('change_percentage', 0.0),
                result.get('last', 0.0),
                result.get('base_volume', 0.0)
            ]

            for i, entry in enumerate(self.market_data):
                if entry[1] == market_entry[1]:
                    self.market_data[i] = market_entry
                    break
            else:
                self.market_data.append(market_entry)

            self.market_data_updated.emit(self.market_data)
            if self.on_data_received:
                self.on_data_received(self.market_data)
        except KeyError as e:
            pass
        except Exception as e:
            pass

    async def add_pair(self, pair):
        if not pair:
            return False

        if pair in self.pairs:
            return False

        is_valid = await self.gateio_ws.is_valid_pair(pair)
        if not is_valid:
            return False

        try:
            self.deleted_pairs.discard(pair)
            self.pairs.add(pair)
            await self.gateio_ws.subscribe_to_pair(pair)
            return True
        except Exception as e:
            return False

    async def add_pairs_from_csv(self, pairs):
        for pair in pairs:
            await self.add_pair(pair)

    def remove_pair(self, pair):
        if pair in self.pairs:
            try:
                future = asyncio.run_coroutine_threadsafe(self.gateio_ws.unsubscribe_from_pair(pair), self.loop)
                future.result()
                self.deleted_pairs.add(pair)
                self.pairs.remove(pair)
            except Exception as e:
                pass

    def remove_pair_from_market_data(self, pair):
        self.market_data = [entry for entry in self.market_data if entry[1] != pair]
        self.market_data_updated.emit(self.market_data)
        if self.on_data_received:
            self.on_data_received(self.market_data)

    def delete_selected_rows(self, pairs):
        for pair in pairs:
            self.remove_pair(pair)
            self.remove_pair_from_market_data(pair)

    async def run_blocking_operation(self):
        result = await self.loop.run_in_executor(executor, self.blocking_operation)

    def blocking_operation(self):
        time.sleep(2)
        return "Hasil operasi blocking"
