from PyQt5.QtWidgets import QMessageBox, QFileDialog
from PyQt5.QtCore import Qt, QModelIndex
import csv
from utils.logging_config import configure_logging

logger = configure_logging('csv_handler', 'logs/csv_handler.log')

def get_marketdata(tableView):
    logger.debug("Mengambil data dari tableView_marketdata")
    data = []
    model = tableView.model()
    for row in range(model.rowCount(QModelIndex())):
        row_data = []
        for column in range(model.columnCount(QModelIndex())):
            index = model.index(row, column)
            row_data.append(model.data(index, Qt.DisplayRole))
        data.append(row_data)
    logger.debug(f"Data yang diambil: {data}")
    return data

def export_csv(tableView):
    options = QFileDialog.Options()
    file_path, _ = QFileDialog.getSaveFileName(tableView, "Save CSV", "", "CSV Files (*.csv);;All Files (*)", options=options)
    if file_path:
        try:
            data = get_marketdata(tableView)
            model = tableView.model()  # Dapatkan model dari tableView
            headers = [model.headerData(i, Qt.Horizontal, Qt.DisplayRole) for i in range(model.columnCount(QModelIndex()))]

            logger.debug(f"Mengekspor data ke file: {file_path}")
            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(headers)
                writer.writerows(data)
            logger.info("Data berhasil diekspor ke file CSV.")
            QMessageBox.information(tableView, "Success", "Data berhasil diekspor ke file CSV.")
        except Exception as e:
            logger.error(f"Gagal mengekspor data ke file CSV: {e}")
            QMessageBox.critical(tableView, "Error", f"Gagal mengekspor data ke file CSV: {e}")

def import_csv(tableView):
    options = QFileDialog.Options()
    file_path, _ = QFileDialog.getOpenFileName(tableView, "Open CSV", "", "CSV Files (*.csv);;All Files (*)", options=options)
    if file_path:
        try:
            data = []
            with open(file_path, mode='r') as file:
                reader = csv.reader(file)
                headers = next(reader)  # Assuming the first row is the header
                for row in reader:
                    data.append(row)
            logger.debug(f"Data yang diimpor dari file: {file_path} adalah: {data}")
            return headers, data
        except Exception as e:
            logger.error(f"Gagal mengimpor data dari file CSV: {e}")
            QMessageBox.critical(tableView, "Error", f"Gagal mengimpor data dari file CSV: {e}")
            return None, None
