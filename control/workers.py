import asyncio
import pandas as pd
from aiohttp import ClientSession
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
from api.api_gateio import GateioAPI

class QThreadWorker(QThread):
    result_ready = pyqtSignal(pd.DataFrame)

    def __init__(self, pairs, api_key, api_secret):
        super(QThreadWorker, self).__init__()
        self.pairs = pairs
        self.api = GateioAPI(api_key, api_secret)
        self._is_running = True

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.run_fetch_data())
        self.loop.close()

    async def run_fetch_data(self):
        while self._is_running:
            await self.fetch_data()
            await asyncio.sleep(10)

    async def fetch_data(self):
        try:
            rows = []
            async with ClientSession() as session:
                for pair in self.pairs:
                    if not self._is_running:
                        break
                    try:
                        data = await self.api.async_get_ticker_info(pair, session)
                        if data:
                            current_time = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
                            change_percentage = pd.to_numeric(data.get('change_percentage', 'N/A'), errors='coerce')
                            row_data = {
                                "TIME": current_time,
                                "PAIR": pair,
                                "24H %": change_percentage,
                                "PRICE": data['last'],
                                "VOLUME": data['base_volume']
                            }
                            rows.append(row_data)
                    except Exception as e:
                        pass
            if rows:
                data_frame = pd.DataFrame(rows)
                self.result_ready.emit(data_frame)
        except Exception as e:
            pass

    def stop(self):
        self._is_running = False

class BalanceWorker(QThread):
    balance_signal = pyqtSignal(dict)

    def __init__(self, api_key, api_secret):
        super(BalanceWorker, self).__init__()
        self.api = GateioAPI(api_key, api_secret)

    def run(self):
        try:
            balance = self.api.get_account_balance()
            self.balance_signal.emit(balance)
        except Exception as e:
            pass
