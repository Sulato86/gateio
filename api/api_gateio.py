import websocket
import json
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from control.logging_config import setup_logging

logger = setup_logging('api_gateio.log')

ws_url = "wss://api.gateio.ws/ws/v4/"

class GateIOWebSocket:
    def __init__(self, message_callback):
        # Inisialisasi kelas GateIOWebSocket.
        self.message_callback = message_callback

    def on_message(self, ws, message):
        # Fungsi yang dipanggil ketika menerima pesan dari websocket.
        try:
            data = json.loads(message)
            logger.info(f"Received message: {data}")
            
            # Verifikasi bahwa data memiliki kunci yang diharapkan
            if 'channel' in data and 'event' in data and 'result' in data:
                self.message_callback(data)
            else:
                logger.error(f"Unexpected data format: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")

    def on_error(self, ws, error):
        # Fungsi yang dipanggil ketika terjadi kesalahan pada websocket.
        logger.error(f"Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        # Fungsi yang dipanggil ketika koneksi websocket ditutup.
        logger.info("### closed ###")

    def on_open(self, ws):
        # Fungsi yang dipanggil ketika koneksi websocket terbuka.
        logger.info("WebSocket is open")
        
        # Subscribe ke spot.tickers
        tickers = ["BTC_USDT", "ETH_USDT", "LTC_USDT"]
        subscribe_tickers_message = {
            "time": int(time.time()),  # Waktu sekarang dalam epoch time
            "channel": "spot.tickers",
            "event": "subscribe",
            "payload": tickers
        }
        ws.send(json.dumps(subscribe_tickers_message))
        
        # Subscribe ke spot.balances
        subscribe_balances_message = {
            "time": int(time.time()),  # Waktu sekarang dalam epoch time
            "channel": "spot.balances",
            "event": "subscribe",
            "payload": []
        }
        ws.send(json.dumps(subscribe_balances_message))

        # Subscribe ke spot.order_book
        subscribe_order_book_message = {
            "time": int(time.time()),  # Waktu sekarang dalam epoch time
            "channel": "spot.order_book",
            "event": "subscribe",
            "payload": ["BTC_USDT", "20"]
        }
        ws.send(json.dumps(subscribe_order_book_message))
        
        # Subscribe ke spot.trades
        #subscribe_trades_message = {
        #    "time": int(time.time()),  # Waktu sekarang dalam epoch time
        #    "channel": "spot.trades",
        #    "event": "subscribe",
        #    "payload": ["BTC_USDT", "ETH_USDT"]
        #}
        #ws.send(json.dumps(subscribe_trades_message))
        
        # Subscribe ke spot.candlesticks
        subscribe_candlesticks_message = {
            "time": int(time.time()),  # Waktu sekarang dalam epoch time
            "channel": "spot.candlesticks",
            "event": "subscribe",
            "payload": ["BTC_USDT", "1m"]
        }
        ws.send(json.dumps(subscribe_candlesticks_message))

        logger.info("Subscribed to multiple channels")

    def run(self):
        # Memulai koneksi websocket dan menjalankannya.
        websocket.enableTrace(True)
        ws = websocket.WebSocketApp(ws_url,
                                    on_open=self.on_open,
                                    on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close)
        ws.run_forever()

if __name__ == "__main__":
    def print_message(message):
        # Fungsi contoh callback untuk mencetak pesan yang diterima.
        print("Received message in main:", message)
    gateio_ws = GateIOWebSocket(print_message)
    gateio_ws.run()
