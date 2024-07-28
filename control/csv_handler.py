import csv
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QProgressDialog
import pandas as pd
from control.logging_config import setup_logging

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
                header = [self.model.headerData(column, Qt.Horizontal, Qt.DisplayRole) for column in range(self.model.columnCount())]
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

class ExportNotifPriceWorker(QThread):
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
                header = [self.model.headerData(column, Qt.Horizontal, Qt.DisplayRole) for column in range(self.model.columnCount())]
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
        df = pd.read_csv(file_path)
        if 'PAIR' in df.columns:
            imported_pairs = df['PAIR'].tolist()
            logger.debug(f"Imported pairs: {imported_pairs}")
            return imported_pairs
        else:
            raise ValueError("CSV file does not contain a 'PAIR' column.")
    except Exception as e:
        logger.error(f"Error importing pairs from CSV: {e}")
        raise e

def import_notifprice_from_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        if 'PAIR' in df.columns and 'PRICE' in df.columns:
            imported_data = dict(zip(df['PAIR'], df['PRICE']))
            logger.debug(f"Imported notification prices: {imported_data}")
            return imported_data
        else:
            raise ValueError("CSV file does not contain required columns 'PAIR' and 'PRICE'.")
    except Exception as e:
        logger.error(f"Error importing notification prices from CSV: {e}")
        raise e

def export_marketdata_to_csv(tableView_marketdata):
    options = QFileDialog.Options()
    filePath, _ = QFileDialog.getSaveFileName(None, "Save CSV", "", "CSV Files (*.csv);;All Files (*)", options=options)
    if filePath:
        progress_dialog = QProgressDialog("Mengekspor data...", "Batal", 0, 100, None)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setMinimumDuration(0)
        
        export_worker = ExportWorker(tableView_marketdata.model(), filePath)
        export_worker.progress.connect(progress_dialog.setValue)
        export_worker.finished.connect(lambda message: QMessageBox.information(None, "Ekspor Selesai", message))
        export_worker.start()
        progress_dialog.exec_()

def handle_import_csv():
    options = QFileDialog.Options()
    filePath, _ = QFileDialog.getOpenFileName(None, "Import CSV", "", "CSV Files (*.csv);;All Files (*)", options=options)
    if filePath:
        try:
            imported_pairs = import_pairs_from_csv(filePath)
            return imported_pairs
        except Exception as e:
            logger.error(f"Error importing pairs from CSV: {e}")
            QMessageBox.critical(None, "Import Error", str(e))
            return None

def handle_import_notifprice_csv():
    options = QFileDialog.Options()
    filePath, _ = QFileDialog.getOpenFileName(None, "Import CSV", "", "CSV Files (*.csv);;All Files (*)", options=options)
    if filePath:
        try:
            imported_data = import_notifprice_from_csv(filePath)
            return imported_data
        except Exception as e:
            logger.error(f"Error importing notification prices from CSV: {e}")
            QMessageBox.critical(None, "Import Error", str(e))
            return None
