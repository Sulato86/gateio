import os
import pandas as pd
from PyQt5.QtCore import Qt
from control.pandas_handler import PandasModel, CustomSortFilterProxyModel
from control.worker_bkp import QThreadWorker, BalanceWorker
from control.csv_handler import handle_import_csv
from control.logging_config import setup_logging

logger = setup_logging('data_handler.log')

def init_market_data_model():
    """
    Inisialisasi model data pasar dengan DataFrame kosong dan proxy model untuk sorting dan filtering.

    :return: Tuple yang berisi DataFrame data pasar dan proxy model.
    """
    data_market = pd.DataFrame(columns=["TIME", "PAIR", "24H %", "PRICE", "VOLUME"])
    proxy_model_market = CustomSortFilterProxyModel()
    proxy_model_market.setSourceModel(PandasModel(data_market))
    proxy_model_market.setSortRole(Qt.DisplayRole)
    return data_market, proxy_model_market

def init_account_data_model():
    """
    Inisialisasi model data akun dengan DataFrame kosong dan proxy model untuk sorting dan filtering.

    :return: Tuple yang berisi DataFrame data akun dan proxy model.
    """
    data_account = pd.DataFrame(columns=["CURRENCY", "AVAILABLE"])
    proxy_model_account = CustomSortFilterProxyModel()
    proxy_model_account.setSourceModel(PandasModel(data_account))
    proxy_model_account.setSortRole(Qt.DisplayRole)
    return data_account, proxy_model_account

def init_workers(pairs, api_key, api_secret):
    """
    Inisialisasi worker thread untuk pengambilan data pasar dan saldo akun.

    :param pairs: Daftar pasangan mata uang.
    :param api_key: Kunci API Gate.io.
    :param api_secret: Kunci rahasia API Gate.io.
    :return: Tuple yang berisi instance QThreadWorker dan BalanceWorker.
    """
    worker = QThreadWorker(pairs, api_key, api_secret)
    balance_worker = BalanceWorker(api_key, api_secret)
    return worker, balance_worker

def update_model_market(data_frame, data_market, proxy_model_market):
    """
    Memperbarui model data pasar dengan data baru.

    :param data_frame: DataFrame yang berisi data pasar terbaru.
    :param data_market: DataFrame data pasar saat ini.
    :param proxy_model_market: Proxy model untuk data pasar.
    :return: DataFrame data pasar yang diperbarui.
    """
    logger.debug("Updating market model with new data")
    for column in ["24H %", "PRICE", "VOLUME"]:
        data_frame[column] = data_frame[column].astype(float)
    data_market = data_frame
    proxy_model_market.setSourceModel(PandasModel(data_market))
    return data_market

def update_model_account(data_frame, data_account, proxy_model_account):
    """
    Memperbarui model data akun dengan data baru.

    :param data_frame: DataFrame yang berisi data akun terbaru.
    :param data_account: DataFrame data akun saat ini.
    :param proxy_model_account: Proxy model untuk data akun.
    :return: DataFrame data akun yang diperbarui.
    """
    logger.debug("Updating account model with new data")
    logger.debug(f"Account DataFrame:\n{data_frame}")
    data_account = data_frame
    proxy_model_account.setSourceModel(PandasModel(data_account))
    logger.debug("Account model updated.")
    return data_account

def update_balance(balance, data_account, proxy_model_account):
    """
    Memperbarui saldo akun dengan data baru.

    :param balance: Dictionary yang berisi saldo akun.
    :param data_account: DataFrame data akun saat ini.
    :param proxy_model_account: Proxy model untuk data akun.
    :return: DataFrame data akun yang diperbarui.
    """
    logger.debug("Update balance called.")
    if 'error' in balance:
        logger.error(f"Error: {balance['message']}")
    else:
        data = [{"CURRENCY": currency, "AVAILABLE": available} for currency, available in balance.items()]
        df = pd.DataFrame(data)
        logger.debug(f"Balance DataFrame:\n{df}")
        data_account = update_model_account(df, data_account, proxy_model_account)
        logger.debug("Account balance updated")
    return data_account

def add_pair(pair, pairs, data_market, proxy_model_market):
    """
    Menambahkan pasangan mata uang baru ke daftar dan memperbarui model data pasar.

    :param pair: Pasangan mata uang baru yang akan ditambahkan.
    :param pairs: Daftar pasangan mata uang saat ini.
    :param data_market: DataFrame data pasar saat ini.
    :param proxy_model_market: Proxy model untuk data pasar.
    :return: Tuple yang berisi daftar pasangan mata uang yang diperbarui dan DataFrame data pasar yang diperbarui.
    """
    if pair and pair not in pairs:
        logger.debug(f"Adding new pair: {pair}")
        pairs.append(pair)
        new_row = pd.DataFrame([[pd.Timestamp.now(), pair, None, None, None]], columns=data_market.columns)
        data_market = pd.concat([data_market, new_row], ignore_index=True)
        proxy_model_market.setSourceModel(PandasModel(data_market))
        logger.debug(f"Pair added: {pair}")
    return pairs, data_market

def update_market_data_with_new_pairs(pairs, data_market, proxy_model_market):
    """
    Memperbarui model data pasar dengan pasangan mata uang baru.

    :param pairs: Daftar pasangan mata uang.
    :param data_market: DataFrame data pasar saat ini.
    :param proxy_model_market: Proxy model untuk data pasar.
    :return: DataFrame data pasar yang diperbarui.
    """
    data_market = pd.DataFrame(columns=["TIME", "PAIR", "24H %", "PRICE", "VOLUME"])
    for pair in pairs:
        new_row = pd.DataFrame([[pd.Timestamp.now(), pair, None, None, None]], columns=data_market.columns)
        data_market = pd.concat([data_market, new_row], ignore_index=True)
    proxy_model_market.setSourceModel(PandasModel(data_market))
    logger.debug("Market data updated with new pairs")
    return data_market

def restart_worker(worker, pairs, api_key, api_secret, update_model_market):
    """
    Memulai ulang worker thread dengan pasangan mata uang yang diperbarui.

    :param worker: Instance QThreadWorker yang saat ini berjalan.
    :param pairs: Daftar pasangan mata uang baru.
    :param api_key: Kunci API Gate.io.
    :param api_secret: Kunci rahasia API Gate.io.
    :param update_model_market: Fungsi untuk memperbarui model data pasar.
    :return: Instance QThreadWorker yang baru.
    """
    if worker.isRunning():
        worker.stop()
        worker.wait()

    worker = QThreadWorker(pairs, api_key, api_secret)
    worker.result_ready.connect(update_model_market)
    worker.start()
    logger.debug("Worker restarted with updated pairs")
    return worker

def close_event(worker, balance_worker):
    """
    Menangani event penutupan aplikasi dengan menghentikan worker thread.

    :param worker: Instance QThreadWorker yang saat ini berjalan.
    :param balance_worker: Instance BalanceWorker yang saat ini berjalan.
    :return: Boolean yang menunjukkan apakah proses penutupan berhasil.
    """
    try:
        logger.debug("closeEvent triggered")
        if worker:
            logger.debug("Stopping QThreadWorker")
            worker.stop()
            if not worker.wait(5000):
                logger.debug("QThreadWorker not stopping, terminating")
                worker.terminate()
        
        if balance_worker:
            logger.debug("Stopping BalanceWorker")
            balance_worker.stop()
            if not balance_worker.wait(5000):
                logger.debug("BalanceWorker not stopping, terminating")
                balance_worker.terminate()

        logger.debug("Closing application")
        return True
    except Exception as e:
        logger.error(f"Error during closeEvent: {e}")
        return False
