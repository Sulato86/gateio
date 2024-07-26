import csv
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import pandas as pd
from control.logging_config import setup_logging  # Import setup_logging

# Konfigurasi logging
logger = setup_logging('csv_handler.log')

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
                logger.debug(f"CSV header written: {header}")
                
                for row in range(self.model.rowCount()):
                    rowData = [self.model.index(row, column).data() for column in range(self.model.columnCount())]
                    writer.writerow(rowData)
                    progress_value = int((row + 1) / self.model.rowCount() * 100)
                    self.progress.emit(progress_value)
                    logger.debug(f"CSV row {row + 1} written: {rowData}")
            self.finished.emit(f"Data berhasil diekspor ke {self.filePath}")
            logger.info(f"Data successfully exported to {self.filePath}")
        except Exception as e:
            error_message = f"Ekspor gagal: {str(e)}"
            self.finished.emit(error_message)
            logger.error(error_message)

def import_pairs_from_csv(file_path):
    try:
        # Baca file CSV
        df = pd.read_csv(file_path)
        
        # Cek apakah kolom 'PAIR' ada
        if 'PAIR' in df.columns:
            imported_pairs = df['PAIR'].tolist()
            logger.debug(f"Imported pairs: {imported_pairs}")
            return imported_pairs
        else:
            # Jika kolom 'PAIR' tidak ada, tampilkan pesan error
            raise ValueError("CSV file does not contain a 'PAIR' column.")
    except Exception as e:
        logger.error(f"Error importing pairs from CSV: {e}")
        raise e
