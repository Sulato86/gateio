import logging
import asyncio
import pytz
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QStandardItem
from api.api_gateio import GateIOWebSocket
from datetime import datetime

# Inisialisasi logger
logger = logging.getLogger('worker')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('worker.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class WebSocketWorker(QThread):
    message_received = pyqtSignal(dict)
    balance_received = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.gateio_ws = GateIOWebSocket(self.send_message_to_ui)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.connect())

    async def connect(self):
        while True:
            try:
                logger.info("Starting WebSocket connection")
                await self.gateio_ws.run()
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
                await asyncio.sleep(5)

    def send_message_to_ui(self, message):
        logger.debug(f"Emitting message to UI: {message}")
        channel = message.get('channel')

        if channel == 'spot.tickers':
            result = message.get('result', {})
            required_keys = ['currency_pair', 'last', 'change_percentage', 'base_volume']
            if all(key in result for key in required_keys):
                if 'time' not in message:
                    logger.warning(f"Message missing 'time': {result}")
                self.message_received.emit(message)
            else:
                logger.error(f"Message missing expected keys: {message}")
                logger.error(f"Complete message: {message}")

class TickerTableUpdater:
    def __init__(self, model, row_mapping):
        self.model = model
        self.row_mapping = row_mapping

    def update_ticker_table(self, message):
        logger.debug(f"Received message for ticker update: {message}")
        ticker_data = message.get('result', {})
        required_keys = ['currency_pair', 'change_percentage', 'last', 'base_volume']
        
        if all(key in ticker_data for key in required_keys):
            epoch_time = message.get('time', 0)
            singapore_tz = pytz.timezone('Asia/Singapore')
            time = datetime.fromtimestamp(epoch_time, singapore_tz).strftime('%d-%m-%Y %H:%M:%S')

            currency_pair = ticker_data['currency_pair']
            change_percentage = float(ticker_data['change_percentage'])
            last_price = float(ticker_data['last'])
            volume = ticker_data.get('base_volume', 0.0)
            volume = float(volume) if volume is not None else 0.0

            change_percentage = f"{change_percentage:.1f}"
            last_price = f"{last_price:.2f}"
            volume = f"{volume:.2f}"

            if currency_pair in self.row_mapping:
                row_index = self.row_mapping[currency_pair]
                self.model.setItem(row_index, 0, QStandardItem(str(time)))
                self.model.setItem(row_index, 1, QStandardItem(currency_pair))
                self.model.setItem(row_index, 2, QStandardItem(change_percentage))
                self.model.setItem(row_index, 3, QStandardItem(last_price))
                self.model.setItem(row_index, 4, QStandardItem(volume))
            else:
                row_index = self.model.rowCount()
                self.row_mapping[currency_pair] = row_index
                time_item = QStandardItem(str(time))
                currency_pair_item = QStandardItem(currency_pair)
                change_percentage_item = QStandardItem(change_percentage)
                last_price_item = QStandardItem(last_price)
                volume_item = QStandardItem(volume)
                self.model.appendRow([time_item, currency_pair_item, change_percentage_item, last_price_item, volume_item])
        else:
            logger.error(f"Missing expected keys in data: {ticker_data}")

