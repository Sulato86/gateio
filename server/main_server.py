import asyncio
import threading
import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow
from datetime import datetime
from logging_config import configure_logging
from gateio import GateIOWebSocket
from server_control import Ui_MainWindow

# Konfigurasi logger
logger = configure_logging('main_server', 'logs/main_server.log')

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        # Mengatur tabel dengan kolom dan baris
        self.tableWidget.setColumnCount(9)
        self.tableWidget.setHorizontalHeaderLabels([
            'Timestamp', 'Open', 'High', 'Low', 'Close', 
            'Total Volume', 'Subscription Name', 
            'Base Currency Amount', 'Window Close'
        ])

        # Mengatur ukuran kolom agar sesuai dengan konten
        self.tableWidget.resizeColumnsToContents()

        # Menambahkan garis antar baris
        self.tableWidget.setShowGrid(True)

        # Mengaktifkan warna baris bergantian
        self.tableWidget.setAlternatingRowColors(True)

        # Menambahkan header yang bisa diklik untuk sorting
        self.tableWidget.setSortingEnabled(True)

        # Memulai WebSocket dalam thread terpisah
        self.start_websocket()

    def epoch_to_local_time(self, epoch_time):
        """Konversi nilai epoch Unix ke waktu lokal tanpa milidetik"""
        try:
            logger.info(f"Converting epoch time: {epoch_time}")
            local_time = datetime.fromtimestamp(epoch_time).strftime('%Y-%m-%d %H:%M:%S')
            return local_time
        except (TypeError, ValueError) as e:
            logger.error(f"Error converting epoch time: {e}")
            return "Invalid Time"

    def insert_data_into_table(self, result):
        try:
            if isinstance(result, dict):
                # Ambil nilai timestamp dan konversi ke waktu lokal
                timestamp = result.get('t')
                if timestamp is not None:
                    try:
                        timestamp = float(timestamp)  # Pastikan timestamp adalah float atau int
                        timestamp = self.epoch_to_local_time(timestamp)
                    except ValueError:
                        logger.error(f"Invalid timestamp value: {timestamp}")
                        return  # Jangan tambahkan baris jika timestamp tidak valid
                else:
                    logger.error("Timestamp is None, skipping this entry.")
                    return  # Jangan tambahkan baris jika timestamp adalah None
                
                # Ambil nilai lainnya langsung dari result
                total_volume = result.get('v', 0)
                close_price = result.get('c', 0)
                highest_price = result.get('h', 0)
                lowest_price = result.get('l', 0)
                open_price = result.get('o', 0)
                subscription_name = result.get('n', "")
                base_currency_amount = result.get('a', 0)
                window_close = result.get('w', "")

                # Menambahkan baris baru ke dalam tabel
                row_position = self.tableWidget.rowCount()
                self.tableWidget.insertRow(row_position)

                # Memasukkan data ke dalam kolom yang sesuai
                self.tableWidget.setItem(row_position, 0, QtWidgets.QTableWidgetItem(str(timestamp)))
                self.tableWidget.setItem(row_position, 1, QtWidgets.QTableWidgetItem(str(open_price)))
                self.tableWidget.setItem(row_position, 2, QtWidgets.QTableWidgetItem(str(highest_price)))
                self.tableWidget.setItem(row_position, 3, QtWidgets.QTableWidgetItem(str(lowest_price)))
                self.tableWidget.setItem(row_position, 4, QtWidgets.QTableWidgetItem(str(close_price)))
                self.tableWidget.setItem(row_position, 5, QtWidgets.QTableWidgetItem(str(total_volume)))
                self.tableWidget.setItem(row_position, 6, QtWidgets.QTableWidgetItem(str(subscription_name)))
                self.tableWidget.setItem(row_position, 7, QtWidgets.QTableWidgetItem(str(base_currency_amount)))
                self.tableWidget.setItem(row_position, 8, QtWidgets.QTableWidgetItem(str(window_close)))

                logger.info("Data berhasil dimasukkan ke dalam tabel.")

                # Menyesuaikan lebar kolom secara otomatis setelah memasukkan data
                self.tableWidget.resizeColumnsToContents()
            else:
                logger.error("Result yang diterima bukan dictionary.")
        except Exception as e:
            logger.error(f"Error inserting data into table: {e}")

    def start_websocket(self):
        def run_websocket():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            websocket_instance = GateIOWebSocket(
                message_callback=self.handle_websocket_message
            )
            logger.info("WebSocket dimulai di thread terpisah.")
            loop.run_until_complete(websocket_instance.run())

        threading.Thread(target=run_websocket, daemon=True).start()

    def handle_websocket_message(self, data):
        try:
            if isinstance(data, dict) and 'result' in data:
                result = data['result']
                if isinstance(result, dict):
                    self.insert_data_into_table(result)
                    logger.info("Pesan WebSocket diterima dan diproses.")
                else:
                    logger.error("'result' bukan dictionary: {}".format(result))
            else:
                logger.error("Data yang diterima dari WebSocket tidak valid atau tidak memiliki kunci 'result'.")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    logger.info("Aplikasi GUI dimulai.")
    sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"An error occurred in main: {e}")
        input("Press Enter to exit...")
