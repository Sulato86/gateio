import time
from celery import Celery
from logging_config import configure_logging
from data_handler import DataHandler

logger = configure_logging('celery_worker', 'logs/celery_worker.log')

app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def create_higher_timeframe_candlesticks(self, pair, timeframe):
    try:
        from data_handler import DataHandler
        data_handler = DataHandler()

        factor = int(timeframe[:-1])

        one_minute_data = data_handler.fetch_candlestick_data(pair, period=factor, timeframe='1m', limit=factor)

        if len(one_minute_data) == factor:
            aggregated_candlestick = aggregate_to_higher_timeframe(one_minute_data, pair, timeframe)
            data_handler.insert_data_to_db(aggregated_candlestick, window_close=True)
        else:
            logger.warning(f"Insufficient data: expected {factor} 1m candlesticks, but got {len(one_minute_data)} for {pair}.")
    except Exception as e:
        logger.error(f"Failed to create higher timeframe candlestick for {pair} on {timeframe}: {e}")
        raise self.retry(exc=e)

def aggregate_to_higher_timeframe(data, pair, timeframe):
    try:
        open_price = data[0]
        close_price = data[-1]
        high_price = max(data)
        low_price = min(data)
        volume = sum(data)

        return {
            't': time.time(),
            'o': open_price,
            'h': high_price,
            'l': low_price,
            'c': close_price,
            'v': volume,
            'n': f'{timeframe}_{pair}',
            'a': volume
        }
    except Exception as e:
        logger.error(f"Error in aggregating candlestick data for {pair} on {timeframe}: {e}")
        raise
