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
        self.message_callback = message_callback

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            logger.info(f"Received message: {data}")
            
            if 'channel' in data and 'event' in data and 'result' in data:
                self.message_callback(data)
            else:
                logger.error(f"Unexpected data format: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")

    def on_error(self, ws, error):
        logger.error(f"Error: {error}")
        time.sleep(5)  # Tambahkan delay sebelum mencoba reconnect
        self.run()  # Coba reconnect

    def on_close(self, ws, close_status_code, close_msg):
        logger.info("### closed ###")
        time.sleep(5)  # Tambahkan delay sebelum mencoba reconnect
        self.run()  # Coba reconnect

    def on_open(self, ws):
        logger.info("WebSocket is open")
        self.subscribe(ws, "spot.tickers", ["BTC_USDT", "ETH_USDT", "LTC_USDT"])
        self.subscribe(ws, "spot.balances", [])
        self.subscribe(ws, "spot.order_book", ["BTC_USDT", "20"])
        self.subscribe(ws, "spot.candlesticks", ["BTC_USDT", "1m"])
        logger.info("Subscribed to multiple channels")

    def subscribe(self, ws, channel, payload):
        message = {
            "time": int(time.time()),
            "channel": channel,
            "event": "subscribe",
            "payload": payload
        }
        ws.send(json.dumps(message))

    def run(self):
        websocket.enableTrace(True)
        ws = websocket.WebSocketApp(ws_url,
                                    on_open=self.on_open,
                                    on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close)
        ws.run_forever()

if __name__ == "__main__":
    def print_message(message):
        print("Received message in main:", message)
    gateio_ws = GateIOWebSocket(print_message)
    gateio_ws.run()
