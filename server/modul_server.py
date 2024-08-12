import asyncio
import threading
import sys
import psycopg2
from PyQt5.QtWidgets import QApplication, QMainWindow
from datetime import datetime
from logging_config import configure_logging
from gateio import GateIOWebSocket

logger = configure_logging('main_server', 'logs/main_server.log')

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.db_connection = self.connect_to_db()
        self.start_websocket()

    def connect_to_db(self):
        try:
            connection = psycopg2.connect(
                database="gateio",
                user="postgres",
                password="Wongk3r3n!",
                host="192.168.1.9",
                port="5432"
            )
            logger.info("Connected to the PostgreSQL database successfully.")
            return connection
        except Exception as e:
            logger.critical(f"Failed to connect to the database: {e}")
            sys.exit(1)

    def epoch_to_local_time(self, epoch_time):
        try:
            if epoch_time is None:
                logger.error("Received None as epoch time, returning None.")
                return None
            epoch_time = float(epoch_time)
            local_time = datetime.fromtimestamp(epoch_time).strftime('%Y-%m-%d %H:%M:%S')
            return local_time
        except (TypeError, ValueError) as e:
            logger.error(f"Error converting epoch time: {e}")
            return None

    def insert_data_to_db(self, data):
        try:
            cursor = self.db_connection.cursor()
            query = """
                INSERT INTO candlestick_data (
                    timestamp, open, high, low, close, total_volume, subscription_name, 
                    base_currency_amount, window_close
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            local_timestamp = self.epoch_to_local_time(data.get('t'))
            
            if local_timestamp is None:
                logger.warning("Skipping insertion due to invalid timestamp.")
                return
            cursor.execute(query, (
                local_timestamp,
                data.get('o'),
                data.get('h'),
                data.get('l'),
                data.get('c'),
                data.get('v'),
                data.get('n'),
                data.get('a'),
                data.get('w')
            ))
            self.db_connection.commit()
            cursor.close()
            logger.info("Data inserted into the database successfully.")
        except Exception as e:
            logger.error(f"Failed to insert data into the database: {e}")

    def start_websocket(self):
        def run_websocket():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            websocket_instance = GateIOWebSocket(
                message_callback=self.insert_data_to_db
            )
            loop.run_until_complete(websocket_instance.run())
        threading.Thread(target=run_websocket, daemon=True).start()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"An error occurred in main: {e}")
        input("Press Enter to exit...")
