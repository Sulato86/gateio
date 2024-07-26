import sys
import os
import asyncio
import pandas as pd
import qasync
from dotenv import load_dotenv
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QHeaderView, QFileDialog, QProgressDialog, QMessageBox
from PyQt5.QtCore import QSortFilterProxyModel, Qt
from api.api_gateio import GateioAPI
from control.pandasa import PandasModel
from control.workers import QThreadWorker, BalanceWorker
from control.csv_handler import ExportWorker
from ui.ui_main_window import Ui_MainWindow

load_dotenv()

class CustomSortFilterProxyModel(QSortFilterProxyModel):
    def lessThan(self, left, right):
        left_data = self.sourceModel().data(left, Qt.DisplayRole)
        right_data = self.sourceModel().data(right, Qt.DisplayRole)
        
        column = left.column()
        pair_column_index = 1
        
        if column == pair_column_index:
            return left_data < right_data
        else:
            try:
                left_data = float(left_data)
                right_data = float(right_data)
            except ValueError:
                return left_data < right_data
            
            return left_data < right_data

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.api_key = os.getenv('API_KEY')
        self.api_secret = os.getenv('SECRET_KEY')
        self.api = GateioAPI(self.api_key, self.api_secret)
        self.pairs = ["BTC_USDT", "ETH_USDT", "LTC_USDT", "XRP_USDT", "BCH_USDT", "EOS_USDT", "TRX_USDT", "ADA_USDT", "XLM_USDT", "LINK_USDT"]
        self.data_market = pd.DataFrame(columns=["TIME", "PAIR", "24H %", "PRICE", "VOLUME"])
        self.proxy_model_market = CustomSortFilterProxyModel(self)
        self.proxy_model_market.setSourceModel(PandasModel(self.data_market))
        self.proxy_model_market.setSortRole(Qt.DisplayRole)
        self.tableView_marketdata.setModel(self.proxy_model_market)
        self.tableView_marketdata.setSortingEnabled(True)
        self.tableView_marketdata.horizontalHeader().setSortIndicatorShown(True)
        self.tableView_marketdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.data_account = pd.DataFrame(columns=["CURRENCY", "AVAILABLE"])
        self.proxy_model_account = CustomSortFilterProxyModel(self)
        self.proxy_model_account.setSourceModel(PandasModel(self.data_account))
        self.proxy_model_account.setSortRole(Qt.DisplayRole)
        self.tableView_accountdata.setModel(self.proxy_model_account)
        self.tableView_accountdata.setSortingEnabled(True)
        self.tableView_accountdata.horizontalHeader().setSortIndicatorShown(True)
        self.tableView_accountdata.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.worker = QThreadWorker(self.pairs, self.api_key, self.api_secret)
        self.worker.result_ready.connect(self.update_model_market)
        self.worker.start()
        self.balance_worker = BalanceWorker(self.api_key, self.api_secret)
        self.balance_worker.balance_signal.connect(self.update_balance)
        self.balance_worker.start()
        self.lineEdit_addpair.returnPressed.connect(self.add_pair)
        self.pushButton_export.clicked.connect(self.export_marketdata_to_csv)

    def update_model_market(self, data_frame):
        for column in ["24H %", "PRICE", "VOLUME"]:
            data_frame[column] = data_frame[column].astype(float)
        self.data_market = data_frame
        self.proxy_model_market.setSourceModel(PandasModel(self.data_market))

    def update_model_account(self, data_frame):
        self.data_account = data_frame
        self.proxy_model_account.setSourceModel(PandasModel(self.data_account))

    def update_balance(self, balance):
        if 'error' in balance:
            pass
        else:
            data = [{"CURRENCY": currency, "AVAILABLE": available} for currency, available in balance.items()]
            df = pd.DataFrame(data)
            self.update_model_account(df)

    def add_pair(self):
        pair = self.lineEdit_addpair.text().strip().upper()
        if pair and pair not in self.pairs:
            self.pairs.append(pair)
            new_row = pd.DataFrame([[pd.Timestamp.now(), pair, None, None, None]], columns=self.data_market.columns)
            self.data_market = pd.concat([self.data_market, new_row], ignore_index=True)
            self.proxy_model_market.setSourceModel(PandasModel(self.data_market))
            self.lineEdit_addpair.clear()

    def export_marketdata_to_csv(self):
        model = self.tableView_marketdata.model()
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if filePath:
            self.progress_dialog = QProgressDialog("Mengekspor data...", "Batal", 0, 100, self)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setMinimumDuration(0)
            self.export_worker = ExportWorker(model, filePath)
            self.export_worker.progress.connect(self.progress_dialog.setValue)
            self.export_worker.finished.connect(self.on_export_finished)
            self.export_worker.start()
            self.progress_dialog.exec_()

    def on_export_finished(self, message):
        self.progress_dialog.cancel()
        QMessageBox.information(self, "Ekspor Selesai", message)

    def closeEvent(self, event):
        self.worker.stop()
        self.worker.wait()
        self.balance_worker.quit()
        self.balance_worker.wait()
        event.accept()

if __name__ == "__main__":
    app = qasync.QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = MainWindow()
    window.show()
    with loop:
        loop.run_forever()
