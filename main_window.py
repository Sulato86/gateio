import sys
import os
import asyncio
import pandas as pd
import logging
import qasync
from dotenv import load_dotenv
from PyQt5.QtWidgets import QApplication, QMainWindow, QHeaderView
from PyQt5.QtCore import QAbstractTableModel, Qt, QSortFilterProxyModel, QTimer, QThread, pyqtSignal
from aiohttp import ClientSession
from api.api_gateio import GateioAPI
from ui.ui_main_window import Ui_MainWindow
from datetime import datetime

# Memuat variabel lingkungan dari file .env
load_dotenv()

# Konfigurasi logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class QThreadWorker(QThread):
    result_ready = pyqtSignal(pd.DataFrame)

    def __init__(self, pairs, api):
        super(QThreadWorker, self).__init__()
        self.pairs = pairs
        self.api = api
        self._is_running = True

    def run(self):
        asyncio.run(self.fetch_data())

    async def fetch_data(self):
        try:
            rows = []
            async with ClientSession() as session:
                for pair in self.pairs:
                    if not self._is_running:
                        break
                    data = await self.api.async_get_ticker_info(pair, session)
                    if data:
                        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        row_data = {
                            "TIME": current_time,
                            "PAIR": pair,
                            "24H %": data['24h_change'],
                            "PRICE": data['last_price'],
                            "VOLUME": data['volume']
                        }
                        rows.append(row_data)
                        logger.debug(f"Fetched data for {pair}: {row_data}")
            if rows:
                data_frame = pd.DataFrame(rows)
                self.result_ready.emit(data_frame)
                logger.debug("Data fetched and emitted")
        except Exception as e:
            logger.error(f"Error fetching data: {e}")

    def stop(self):
        self._is_running = False

class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super(PandasModel, self).__init__()
        self._data = data
        logger.debug("PandasModel initialized with data")

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                value = self._data.iloc[index.row(), index.column()]
                if self._data.columns[index.column()] == "VOLUME":
                    try:
                        return f"{float(value):.2f}" if value is not None else "N/A"
                    except ValueError:
                        return value
                return str(value) if value is not None else "N/A"
            elif role == Qt.TextAlignmentRole:
                return Qt.AlignCenter
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._data.columns[section]
            elif orientation == Qt.Vertical:
                return self._data.index[section]
        return None

    def sort(self, column, order):
        col_name = self._data.columns[column]
        self.layoutAboutToBeChanged.emit()
        self._data = self._data.sort_values(by=col_name, ascending=(order == Qt.AscendingOrder)).reset_index(drop=True)
        self.layoutChanged.emit()
        logger.debug(f"Data sorted by {col_name} in {'ascending' if order == Qt.AscendingOrder else 'descending'} order")

    def update_data(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()
        logger.debug("Model data updated")

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Inisialisasi API Gate.io
        self.api = GateioAPI()
        logger.debug("GateioAPI initialized")
        
        # Inisialisasi DataFrame dan model untuk tableView_marketdata
        self.data = pd.DataFrame(columns=["TIME", "PAIR", "24H %", "PRICE", "VOLUME"])
        self.model = PandasModel(self.data)
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        self.tableView_marketdata.setModel(self.proxy)
        self.tableView_marketdata.setSortingEnabled(True)
        self.tableView_marketdata.horizontalHeader().setSortIndicatorShown(True)
        self.tableView_marketdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableView_marketdata.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tableView_accountdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableView_accountdata.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.lineEdit_addpair.setPlaceholderText("e.g. BTC_USDT")
        logger.debug("TableView configured")

        # Inisialisasi pasangan default
        self.pairs = ['BTC_USDT', 'ETH_USDT', 'SEAT_USDT','SHIB_USDT']
        logger.debug(f"Pairs set: {self.pairs}")

        # Timer untuk pembaruan data
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.schedule_update)
        self.timer.start(15000)
        logger.debug("Timer started for data updates every 15 seconds")

        # Hubungkan sinyal returnPressed dari lineEdit_addpair ke metode add_pair
        self.lineEdit_addpair.returnPressed.connect(self.add_pair)
        self.worker = None
        self.show()

    def closeEvent(self, event):
        if self.worker is not None:
            self.worker.stop()
            self.worker.quit()
            self.worker.wait()
        event.accept()

    def update_model(self, data_frame):
        self.model.update_data(data_frame)

    def schedule_update(self):
        logger.debug("Scheduling data update")
        if self.worker is not None:
            self.worker.stop()
            self.worker.quit()
            self.worker.wait()
        self.worker = QThreadWorker(self.pairs, self.api)
        self.worker.result_ready.connect(self.update_model)
        self.worker.start()

    def add_pair(self):
        pair = self.lineEdit_addpair.text().strip().upper()
        if pair and pair not in self.pairs:  # Pastikan pasangan tidak kosong dan belum ada di daftar
            # Tambahkan pasangan baru ke daftar pasangan
            self.pairs.append(pair)
            # Perbarui DataFrame dengan pasangan baru
            new_row = pd.DataFrame([[pd.Timestamp.now(), pair, None, None, None]], columns=self.data.columns)
            self.data = pd.concat([self.data, new_row], ignore_index=True)
            self.update_model(self.data)  # Perbarui model dengan data terbaru
            self.lineEdit_addpair.clear()
            logger.debug(f"Pair added: {pair}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        sys.exit(app.exec_())
