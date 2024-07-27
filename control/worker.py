import asyncio
import pandas as pd
from aiohttp import ClientSession
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
from api.api_gateio import GateioAPI
from control.logging_config import setup_logging

# Konfigurasi logging
logger = setup_logging('workers.log')

class QThreadWorker(QThread):
    result_ready = pyqtSignal(pd.DataFrame)
    price_check_signal = pyqtSignal(dict)
    export_complete_signal = pyqtSignal()
    import_complete_signal = pyqtSignal(pd.DataFrame)

    def __init__(self, pairs, api_key, api_secret):
        super().__init__()
        self.pairs = pairs
        self.api = GateioAPI(api_key, api_secret)
        self._is_running = True
        logger.debug("QThreadWorker initialized with pairs: %s", pairs)

    def run(self):
        logger.debug("QThreadWorker started")
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.run_fetch_data())
        finally:
            self.loop.close()
            logger.debug("QThreadWorker run method completed")

    async def run_fetch_data(self):
        while self._is_running:
            await self.fetch_data()
            for _ in range(10):  # Cek setiap detik untuk lebih responsif
                if not self._is_running:
                    return
                await asyncio.sleep(1)

    async def fetch_data(self):
        try:
            rows = []
            async with ClientSession() as session:
                for pair in self.pairs:
                    if not self._is_running:
                        logger.debug("QThreadWorker stopped")
                        break
                    try:
                        data = await asyncio.wait_for(self.api.async_get_ticker_info(pair, session), timeout=5)
                        logger.debug(f"Received data for {pair}: {data}")
                        if data:
                            current_time = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
                            rows.append({
                                "TIME": current_time,
                                "PAIR": pair,
                                "24H %": data['change_percentage'],
                                "PRICE": data['last'],
                                "VOLUME": data['base_volume']
                            })
                    except asyncio.TimeoutError:
                        logger.debug(f"Timeout fetching data for {pair}")
            if rows:
                df = pd.DataFrame(rows)
                self.result_ready.emit(df)
        except Exception as e:
            logger.error(f"Error in fetch_data: {e}")

    def stop(self):
        self._is_running = False
        logger.debug("QThreadWorker stopping")
        self.quit()
        if not self.wait(5000):  # Tunggu maksimal 5 detik
            logger.debug("QThreadWorker not stopping, terminating")
            self.terminate()

    def export_data(self, data_frame, file_path):
        try:
            data_frame.to_csv(file_path, index=False)
            logger.debug(f"Data successfully exported to {file_path}")
            self.export_complete_signal.emit()
        except Exception as e:
            logger.error(f"Error exporting data: {e}")

    def import_data(self, file_path):
        try:
            data_frame = pd.read_csv(file_path)
            logger.debug(f"Data successfully imported from {file_path}")
            self.import_complete_signal.emit(data_frame)
        except Exception as e:
            logger.error(f"Error importing data: {e}")

class BalanceWorker(QThread):
    balance_signal = pyqtSignal(dict)

    def __init__(self, api_key, api_secret):
        super().__init__()
        self.api = GateioAPI(api_key, api_secret)
        self._is_running = True
        logger.debug("BalanceWorker initialized")

    def run(self):
        logger.debug("BalanceWorker started")
        while self._is_running:
            try:
                balance = self.api.get_account_balance()
                self.balance_signal.emit(balance)
                logger.debug("Balance fetched and signal emitted")
                for _ in range(60):
                    if not self._is_running:
                        logger.debug("BalanceWorker stopping in loop")
                        return
                    QThread.sleep(1)
            except Exception as e:
                logger.error(f"Error fetching balance: {e}")
                self._is_running = False
        logger.debug("BalanceWorker run method completed")

    def stop(self):
        self._is_running = False
        logger.debug("BalanceWorker stopping")
        self.quit()
        if not self.wait(5000):  # Tunggu maksimal 5 detik
            logger.debug("BalanceWorker not stopping, terminating")
            self.terminate()
