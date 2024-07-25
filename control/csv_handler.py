# controller/csv_handler.py

import csv
import logging
from PyQt5.QtCore import QThread, pyqtSignal, Qt

# Konfigurasi logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Handler untuk logging ke file
file_handler = logging.FileHandler('csv_handler.log')
file_handler.setLevel(logging.DEBUG)

# Handler untuk logging ke console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Format logging
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Menambahkan handler ke logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

class ExportWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    
    def __init__(self, model, filePath):
        super().__init__()
        self.model = model
        self.filePath = filePath

    def run(self):
        try:
            with open(self.filePath, 'w', newline='') as file:
                writer = csv.writer(file)
                header = [self.model.headerData(column, Qt.Horizontal) for column in range(self.model.columnCount())]
                writer.writerow(header)
                logger.debug(f"Header ditulis: {header}")
                
                for row in range(self.model.rowCount()):
                    rowData = [self.model.index(row, column).data() for column in range(self.model.columnCount())]
                    writer.writerow(rowData)
                    logger.debug(f"Baris {row} ditulis: {rowData}")
                    self.progress.emit(int((row + 1) / self.model.rowCount() * 100))
            self.finished.emit(f"Data berhasil diekspor ke {self.filePath}")
            logger.info(f"Ekspor selesai: {self.filePath}")
        except Exception as e:
            self.finished.emit(f"Ekspor gagal: {str(e)}")
            logger.error(f"Ekspor gagal: {str(e)}")
