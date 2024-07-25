import asyncio
import pandas as pd
import logging
from aiohttp import ClientSession
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
from api.api_gateio import GateioAPI  # Memastikan import kelas GateioAPI benar

# Konfigurasi logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Handler untuk logging ke file
file_handler = logging.FileHandler('workers.log')
file_handler.setLevel(logging.DEBUG)

# Handler untuk logging ke console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Format logging
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Menambahkan handler ke logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

class QThreadWorker(QThread):
    result_ready = pyqtSignal(pd.DataFrame)

    def __init__(self, pairs, api_key, api_secret):
        super(QThreadWorker, self).__init__()
        self.pairs = pairs
        self.api = GateioAPI(api_key, api_secret)
        self._is_running = True
        logger.debug("QThreadWorker initialized with pairs: %s", pairs)

    def run(self):
        logger.debug("QThreadWorker started")
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.fetch_data())
        self.loop.close()
        logger.debug("QThreadWorker run method completed")

    async def fetch_data(self):
        try:
            rows = []
            async with ClientSession() as session:
                for pair in self.pairs:
                    if not self._is_running:
                        logger.debug("QThreadWorker stopped")
                        break
                    try:
                        data = await self.api.async_get_ticker_info(pair, session)
                        logger.debug(f"Received data for {pair}: {data}")
                        if data:
                            current_time = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
                            change_percentage = pd.to_numeric(data.get('change_percentage', 'N/A'), errors='coerce')
                            logger.debug(f"Change percentage for {pair}: {change_percentage} (type: {type(change_percentage)})")
                            row_data = {
                                "TIME": current_time,
                                "PAIR": pair,
                                "24H %": change_percentage,
                                "PRICE": data['last'],
                                "VOLUME": data['base_volume']
                            }
                            rows.append(row_data)
                            logger.debug(f"Fetched data for {pair}: {row_data}")
                    except Exception as e:
                        logger.error(f"Error fetching data for {pair}: {e}")
            if rows:
                data_frame = pd.DataFrame(rows)
                self.result_ready.emit(data_frame)
                logger.debug("Data frame emitted")
        except Exception as e:
            logger.error(f"Error in fetch_data: {e}")

    def stop(self):
        self._is_running = False
        logger.debug("QThreadWorker stopping")

class BalanceWorker(QThread):
    balance_signal = pyqtSignal(dict)

    def __init__(self, api_key, api_secret):
        super(BalanceWorker, self).__init__()
        self.api = GateioAPI(api_key, api_secret)

    def run(self):
        try:
            balance = self.api.get_account_balance()
            self.balance_signal.emit(balance)
            logger.debug("Balance fetched and signal emitted")
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
