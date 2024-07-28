import os
import pandas as pd
from PyQt5.QtCore import Qt
from control.pandas_handler import PandasModel, CustomSortFilterProxyModel
from control.worker import QThreadWorker, BalanceWorker
from control.csv_handler import handle_import_csv
from control.logging_config import setup_logging

logger = setup_logging('data_handler.log')

def init_market_data_model():
    data_market = pd.DataFrame(columns=["TIME", "PAIR", "24H %", "PRICE", "VOLUME"])
    proxy_model_market = CustomSortFilterProxyModel()
    proxy_model_market.setSourceModel(PandasModel(data_market))
    proxy_model_market.setSortRole(Qt.DisplayRole)
    return data_market, proxy_model_market

def init_account_data_model():
    data_account = pd.DataFrame(columns=["CURRENCY", "AVAILABLE"])
    proxy_model_account = CustomSortFilterProxyModel()
    proxy_model_account.setSourceModel(PandasModel(data_account))
    proxy_model_account.setSortRole(Qt.DisplayRole)
    return data_account, proxy_model_account

def init_workers(pairs, api_key, api_secret):
    worker = QThreadWorker(pairs, api_key, api_secret)
    balance_worker = BalanceWorker(api_key, api_secret)
    return worker, balance_worker

def update_model_market(data_frame, data_market, proxy_model_market):
    logger.debug("Updating market model with new data")
    for column in ["24H %", "PRICE", "VOLUME"]:
        data_frame[column] = data_frame[column].astype(float)
    data_market = data_frame
    proxy_model_market.setSourceModel(PandasModel(data_market))
    return data_market

def update_model_account(data_frame, data_account, proxy_model_account):
    logger.debug("Updating account model with new data")
    logger.debug(f"Account DataFrame:\n{data_frame}")
    data_account = data_frame
    proxy_model_account.setSourceModel(PandasModel(data_account))
    logger.debug("Account model updated.")
    return data_account

def update_balance(balance, data_account, proxy_model_account):
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
    if pair and pair not in pairs:
        logger.debug(f"Adding new pair: {pair}")
        pairs.append(pair)
        new_row = pd.DataFrame([[pd.Timestamp.now(), pair, None, None, None]], columns=data_market.columns)
        data_market = pd.concat([data_market, new_row], ignore_index=True)
        proxy_model_market.setSourceModel(PandasModel(data_market))
        logger.debug(f"Pair added: {pair}")
    return pairs, data_market

def update_market_data_with_new_pairs(pairs, data_market, proxy_model_market):
    data_market = pd.DataFrame(columns=["TIME", "PAIR", "24H %", "PRICE", "VOLUME"])
    for pair in pairs:
        new_row = pd.DataFrame([[pd.Timestamp.now(), pair, None, None, None]], columns=data_market.columns)
        data_market = pd.concat([data_market, new_row], ignore_index=True)
    proxy_model_market.setSourceModel(PandasModel(data_market))
    logger.debug("Market data updated with new pairs")
    return data_market

def restart_worker(worker, pairs, api_key, api_secret, update_model_market):
    if worker.isRunning():
        worker.stop()
        worker.wait()

    worker = QThreadWorker(pairs, api_key, api_secret)
    worker.result_ready.connect(update_model_market)
    worker.start()
    logger.debug("Worker restarted with updated pairs")
    return worker

def close_event(worker, balance_worker):
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

def delete_market_rows(indices, data_market, proxy_model_market):
    logger.debug(f"Deleting rows at indices: {indices}")
    proxy_model_market.layoutAboutToBeChanged.emit()
    data_market.drop(data_market.index[indices], inplace=True)
    logger.debug(f"Data market after deletion:\n{data_market}")
    data_market.reset_index(drop=True, inplace=True)
    proxy_model_market.setSourceModel(PandasModel(data_market))
    proxy_model_market.layoutChanged.emit()
    logger.debug("Market rows deleted")
    print(data_market)  # Tambahkan cetak DataFrame untuk verifikasi
    return data_market


def delete_account_rows(indices, data_account, proxy_model_account):
    logger.debug(f"Deleting rows at indices: {indices}")
    proxy_model_account.layoutAboutToBeChanged.emit()
    data_account.drop(data_account.index[indices], inplace=True)
    logger.debug(f"Data account after deletion:\n{data_account}")
    data_account.reset_index(drop=True, inplace=True)
    proxy_model_account.setSourceModel(PandasModel(data_account))
    proxy_model_account.layoutChanged.emit()
    logger.debug("Account rows deleted")
    return data_account
