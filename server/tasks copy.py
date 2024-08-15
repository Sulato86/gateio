import time
from celery import Celery
from logging_config import configure_logging
from data_handler import DataHandler

# Konfigurasikan logger dengan menggunakan logging_config.py
logger = configure_logging('celery_worker', 'logs/celery_worker.log')

app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task
def create_higher_timeframe_candlesticks(pair, timeframe):
    try:
        # Log inisialisasi tugas
        logger.info(f"Starting task to create {timeframe} candlestick for {pair}.")

        # Impor DataHandler hanya di sini, di dalam fungsi ini, untuk menghindari circular import
        from data_handler import DataHandler
        data_handler = DataHandler()

        # Log setelah DataHandler berhasil diinisialisasi
        logger.info("DataHandler initialized successfully.")

        # Menghitung jumlah candlestick yang diperlukan
        factor = int(timeframe[:-1])
        logger.info(f"Calculated factor for {timeframe}: {factor}.")

        # Fetch data candlestick
        logger.info(f"Fetching {factor} candlesticks for pair {pair} with timeframe 1m.")
        one_minute_data = data_handler.fetch_candlestick_data(pair, period=factor, timeframe='1m', limit=factor)

        if len(one_minute_data) == factor:
            logger.info(f"Successfully fetched {factor} 1m candlesticks for {pair}. Now aggregating for {timeframe}.")

            # Aggregate data
            aggregated_candlestick = aggregate_to_higher_timeframe(one_minute_data, pair, timeframe)
            
            # Log setelah data berhasil diaggregate
            logger.info(f"Aggregation completed. Inserting {timeframe} candlestick into database.")
            
            data_handler.insert_data_to_db(aggregated_candlestick, window_close=True)
            
            # Log setelah data berhasil disimpan
            logger.info(f"Created and saved {timeframe} candlestick for {pair}.")
        else:
            logger.warning(f"Insufficient data: expected {factor} 1m candlesticks, but got {len(one_minute_data)} for {pair}.")
    except Exception as e:
        logger.error(f"Failed to create higher timeframe candlestick for {pair} on {timeframe}: {e}")

def aggregate_to_higher_timeframe(data, pair, timeframe):
    try:
        logger.info(f"Starting aggregation for {timeframe} candlestick.")
        
        open_price = data[0]
        close_price = data[-1]
        high_price = max(data)
        low_price = min(data)
        volume = sum(data)  # Sesuaikan dengan volume atau data lain yang relevan
        
        # Log hasil dari aggregation
        logger.debug(f"Aggregation result - Open: {open_price}, Close: {close_price}, High: {high_price}, Low: {low_price}, Volume: {volume}")
        
        logger.info("Candlestick aggregation completed.")
        
        return {
            't': time.time(),  # Waktu saat ini untuk timestamp
            'o': open_price,
            'h': high_price,
            'l': low_price,
            'c': close_price,
            'v': volume,
            'n': f'{timeframe}_{pair}',  # Pastikan subscription_name dibentuk dengan benar
            'a': volume  # Atur sesuai dengan data yang relevan
        }
    except Exception as e:
        logger.error(f"Error in aggregating candlestick data for {pair} on {timeframe}: {e}")
        raise
