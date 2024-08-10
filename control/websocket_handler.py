import asyncio
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from utils.logging_config import configure_logging
from api.websocket_gateio import GateIOWebSocket
from PyQt5.QtCore import QObject

logger = configure_logging('websocket_handler', 'logs/websocket_handler.log')
executor = ThreadPoolExecutor()

class WebSocketHandler(QObject):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.pairs = set()
        self.deleted_pairs = set()
        self.data_queue = asyncio.Queue()
        self.gateio_ws = GateIOWebSocket(self.on_message, pairs=list(self.pairs))
        self.loop = asyncio.new_event_loop()

    def start(self):
        threading.Thread(target=self.run_loop, daemon=True).start()

    def run_loop(self):
        asyncio.set_event_loop(self.loop)
        try:
            asyncio.run_coroutine_threadsafe(self.gateio_ws.run(), self.loop)
            asyncio.run_coroutine_threadsafe(self.process_queue(), self.loop)
            self.loop.run_forever()
        except Exception:
            pass

    async def process_queue(self):
        while True:
            try:
                data = await self.data_queue.get()
                if data:
                    self.process_message(data)
            except Exception:
                pass

    async def on_message(self, data):
        try:
            await self.data_queue.put(data)
        except Exception:
            pass

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
                float(result.get('change_percentage', 0.0)),
                float(result.get('last', 0.0)),
                float(result.get('base_volume', 0.0)),
                float(result.get('quote_volume', 0.0))
            ]
            market_data = self.model._data.values.tolist()
            for i, entry in enumerate(market_data):
                if entry[1] == market_entry[1]:
                    market_data[i] = market_entry
                    break
            else:
                market_data.append(market_entry)
            self.model.update_data(market_data)
        except (KeyError, ValueError):
            pass

    async def add_pair(self, pair):
        if not pair:
            return False
        if pair in self.pairs:
            return False
        try:
            is_valid = await self.gateio_ws.is_valid_pair(pair)
            if not is_valid:
                return False
            self.deleted_pairs.discard(pair)
            self.pairs.add(pair)
            await self.gateio_ws.subscribe_to_pair(pair)
            return True
        except Exception:
            return False

    def remove_pair(self, pair):
        if pair in self.pairs:
            try:
                future = asyncio.run_coroutine_threadsafe(self.gateio_ws.unsubscribe_from_pair(pair), self.loop)
                future.result()
                self.deleted_pairs.add(pair)
                self.pairs.remove(pair)
            except Exception:
                pass

    def remove_pair_from_market_data(self, pair):
        try:
            market_data = self.model._data.values.tolist()
            self.model.update_data([entry for entry in market_data if entry[1] != pair])
        except Exception:
            pass

    def delete_selected_rows(self, pairs):
        for pair in pairs:
            self.remove_pair(pair)
            self.remove_pair_from_market_data(pair)
