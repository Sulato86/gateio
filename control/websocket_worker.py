import logging
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QStandardItem
from api.api_gateio import GateIOWebSocket
from datetime import datetime
import pytz

# Inisialisasi logger
logger = logging.getLogger('websocket_worker')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('websocket_worker.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class WebSocketWorker(QThread):
    message_received = pyqtSignal(dict)

    def run(self):
        # Menjalankan koneksi websocket di thread terpisah dan mengirim pesan ke UI.
        def send_message_to_ui(message):
            logger.debug(f"Emitting message to UI: {message}")
            channel = message.get('channel')

            if channel == 'spot.tickers':
                result = message.get('result')
                if isinstance(result, dict) and 'currency_pair' in result and 'last' in result and 'change_percentage' in result:
                    # Periksa dan log jika time atau volume tidak ada
                    if 'time' not in message or 'base_volume' not in result:
                        logger.warning(f"Message missing 'time' or 'base_volume': {result}")
                    self.message_received.emit(message)
                else:
                    logger.error(f"Message missing expected keys: {message}")

        gateio_ws = GateIOWebSocket(send_message_to_ui)
        logger.info("Starting WebSocket connection")
        gateio_ws.run()

class TickerTableUpdater:
    def __init__(self, model, row_mapping):
        self.model = model
        self.row_mapping = row_mapping

    def update_ticker_table(self, message):
        # Memperbarui tabel ticker dengan data baru dari websocket.
        logger.debug(f"Received message for ticker update: {message}")
        ticker_data = message.get('result', {})

        if 'currency_pair' in ticker_data and 'last' in ticker_data and 'change_percentage' in ticker_data:
            # Menggunakan base_volume sebagai volume dan time dari message
            epoch_time = message.get('time', 0)  # Menggunakan message time
            singapore_tz = pytz.timezone('Asia/Singapore')
            time = datetime.fromtimestamp(epoch_time, singapore_tz).strftime('%d-%m-%Y %H:%M:%S')

            currency_pair = ticker_data['currency_pair']
            change_percentage = float(ticker_data['change_percentage'])
            last_price = float(ticker_data['last'])
            volume = float(ticker_data.get('base_volume', 'N/A'))  # Menggunakan base_volume sebagai volume

            # Format desimal
            change_percentage = f"{change_percentage:.1f}"  # 1 digit desimal
            last_price = f"{last_price:.2f}"  # 2 digit desimal
            volume = f"{volume:.2f}"  # 2 digit desimal

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
