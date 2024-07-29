import logging
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QStandardItem
from api.api_gateio import GateIOWebSocket

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
                    self.message_received.emit(message)
                else:
                    logger.error(f"Message missing expected keys: {message}")
            else:
                logger.debug(f"Ignoring message from channel: {channel}")

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
            currency_pair = ticker_data['currency_pair']
            last_price = ticker_data['last']
            change_percentage = ticker_data['change_percentage']

            if currency_pair in self.row_mapping:
                row_index = self.row_mapping[currency_pair]
                self.model.setItem(row_index, 1, QStandardItem(str(last_price)))
                self.model.setItem(row_index, 2, QStandardItem(str(change_percentage)))
            else:
                row_index = self.model.rowCount()
                self.row_mapping[currency_pair] = row_index
                currency_pair_item = QStandardItem(currency_pair)
                last_price_item = QStandardItem(str(last_price))
                change_percentage_item = QStandardItem(str(change_percentage))
                self.model.appendRow([currency_pair_item, last_price_item, change_percentage_item])
        else:
            logger.error(f"Missing expected keys in data: {ticker_data}")
