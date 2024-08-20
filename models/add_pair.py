import sys
import requests
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from main_window import Ui_MainWindow  # Import hasil konversi dari file .ui
from utils.logging_config import configure_logging  # Import konfigurasi logging

# Konfigurasi logging
logger = configure_logging('main_py', 'logs/main_py.log')

class PairManager(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # Inisialisasi UI dari file .py yang dihasilkan oleh pyuic5
        
        # Hubungkan tombol dengan fungsi
        self.addPairButton.clicked.connect(self.add_pair)
        self.removePairButton.clicked.connect(self.remove_pair)
        
        # Log inisialisasi
        logger.info("UI PairManager telah diinisialisasi")

        # Load existing pairs from the server
        self.load_pairs()

    def load_pairs(self):
        # Mengambil daftar pasangan pair dari server Flask
        try:
            response = requests.get('http://154.26.128.195:5000/pairs')  # Menyesuaikan endpoint
            pairs = response.json().get('pairs', [])
            self.pairListWidget.addItems(pairs)
            logger.info("Berhasil memuat pasangan pair dari server")
        except Exception as e:
            logger.error(f"Failed to load pairs: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load pairs: {e}")

    def add_pair(self):
        # Menambahkan pasangan pair baru melalui server Flask
        new_pair = self.pairLineEdit.text().strip().upper()  # Mengubah input menjadi huruf besar
        if new_pair:
            try:
                # Log data yang akan dikirim
                logger.info(f"Sending POST request to add pair: {new_pair}")
                
                # Kirim permintaan ke server Flask
                response = requests.post('http://154.26.128.195:5000/pairs', json={'pair': new_pair})
                
                # Log respons yang diterima dari server
                logger.info(f"Received response: {response.status_code} - {response.text}")
                
                result = response.json()
                if result['status'] == 'success':
                    self.pairListWidget.addItem(new_pair)
                    self.pairLineEdit.clear()
                    logger.info(f"Berhasil menambahkan pasangan pair: {new_pair}")
                    QMessageBox.information(self, "Success", "Pair added successfully!")
                else:
                    logger.warning(f"Gagal menambahkan pasangan pair: {result.get('message', 'Unknown error')}")
                    QMessageBox.warning(self, "Warning", result.get('message', 'Unknown error'))
            except Exception as e:
                logger.error(f"Failed to add pair: {e}")
                QMessageBox.critical(self, "Error", f"Failed to add pair: {e}")
        else:
            logger.warning("Input pasangan pair kosong")
            QMessageBox.warning(self, "Warning", "Please enter a pair.")

    def remove_pair(self):
        # Menghapus pasangan pair melalui server Flask
        selected_items = self.pairListWidget.selectedItems()
        if selected_items:
            pair = selected_items[0].text().upper()  # Mengubah input menjadi huruf besar
            try:
                response = requests.delete('http://154.26.128.195:5000/pairs', json={'pair': pair})
                logger.info(f"Received response: {response.status_code} - {response.text}")  # Log respons dari server
                
                result = response.json()
                
                # Pastikan respons memiliki kunci 'status'
                if 'status' in result:
                    if result['status'] == 'success':
                        self.pairListWidget.takeItem(self.pairListWidget.row(selected_items[0]))
                        logger.info(f"Berhasil menghapus pasangan pair: {pair}")
                        QMessageBox.information(self, "Success", "Pair removed successfully!")
                    else:
                        logger.warning(f"Gagal menghapus pasangan pair: {result['message']}")
                        QMessageBox.warning(self, "Warning", result['message'])
                else:
                    logger.error(f"Unexpected response format: {result}")
                    QMessageBox.critical(self, "Error", f"Unexpected response format: {result}")
            except Exception as e:
                logger.error(f"Failed to remove pair: {e}")
                QMessageBox.critical(self, "Error", f"Failed to remove pair: {e}")
        else:
            logger.warning("Tidak ada pasangan pair yang dipilih untuk dihapus")
            QMessageBox.warning(self, "Warning", "Please select a pair to remove.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PairManager()
    window.show()
    logger.info("Aplikasi UI PairManager telah dijalankan")
    sys.exit(app.exec_())
