import pandas as pd
import asyncio
from PyQt5.QtCore import QAbstractTableModel, Qt, pyqtSignal, QModelIndex, QThread, pyqtSlot
from PyQt5.QtGui import QColor, QBrush, QFont
from utils.logging_config import configure_logging
from control.websocket_handler import WebSocketHandler
from threading import Lock

logger = configure_logging('panda_market_data', 'logs/panda_market_data.log')

class ImportCSVThread(QThread):
    result = pyqtSignal(bool)
    data_changed = pyqtSignal()

    def __init__(self, file_name, model):
        super().__init__()
        self.file_name = file_name
        self.model = model

    def run(self):
        try:
            logger.info(f"Memulai impor data dari file: {self.file_name}")
            imported_data = pd.read_csv(self.file_name)
            
            pairs_to_add = []
            current_pairs = set(self.model._data['PAIR'].values)

            batch_size = 100
            for i in range(0, len(imported_data), batch_size):
                batch = imported_data.iloc[i:i+batch_size]
                for _, row in batch.iterrows():
                    pair = row['PAIR']
                    if pair in current_pairs:
                        self.model.update_data([row.values])
                    else:
                        self.model._data = pd.concat([self.model._data, pd.DataFrame([row], columns=self.model._headers)], ignore_index=True)
                        pairs_to_add.append(pair)
                        current_pairs.add(pair)

            for pair in pairs_to_add:
                logger.info(f"Menambahkan pair baru ke WebSocket: {pair}")
                self.model.add_pair(pair)

            self.data_changed.emit()  # Emit sinyal untuk memperbarui data
            logger.info("Data berhasil diimpor dan model diperbarui.")
            self.result.emit(True)
        except Exception as e:
            logger.error(f"Gagal mengimpor data dari CSV: {e}")
            self.result.emit(False)

class PandaMarketData(QAbstractTableModel):
    data_changed = pyqtSignal()

    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self._headers = ["TIME", "PAIR", "24%", "PRICE", "BVOLUME", "QVOLUME"]
        self._data = pd.DataFrame(data, columns=self._headers) if data else pd.DataFrame(columns=self._headers)
        self.data_lock = Lock()
        self.websocket_handler = WebSocketHandler(self)
        self.websocket_handler.start()

    def rowCount(self, index=None) -> int:
        return self._data.shape[0]

    def columnCount(self, index=None) -> int:
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        try:
            value = self._data.iat[index.row(), index.column()]
            if role == Qt.DisplayRole:
                if index.column() == 3:
                    return self.format_price(value)
                if index.column() in [2, 4, 5]:
                    return self.format_percentage_or_volume(value)
                return value
            if role in [Qt.BackgroundRole, Qt.ForegroundRole] and index.column() == 2:
                return self.get_brush(value, role)
        except (IndexError, ValueError):
            logger.error(f"Error accessing data at row {index.row()}, column {index.column()}: {Exception}")
            return None
        return None

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        if role == Qt.FontRole and orientation == Qt.Horizontal:
            font = QFont()
            font.setBold(True)
            return font
        return None

    def update_data(self, new_data):
        with self.data_lock:
            try:
                updated_rows = []
                for new_row in new_data:
                    existing_index = self._data.index[self._data["PAIR"] == new_row[1]].tolist()
                    if existing_index:
                        row = existing_index[0]
                        self._data.iloc[row] = new_row
                        updated_rows.append(row)
                    else:
                        new_row_df = pd.DataFrame([new_row], columns=self._headers)
                        if not new_row_df.isna().all().all():
                            self._data = pd.concat([self._data, new_row_df], ignore_index=True)
                            self._data.drop_duplicates(subset=["PAIR"], keep="last", inplace=True)

                if updated_rows:
                    # Emit sinyal untuk pembaruan baris tertentu saja
                    for row in updated_rows:
                        self.dataChanged.emit(self.index(row, 0), self.index(row, self.columnCount() - 1))
                self.layoutChanged.emit()  # Emit sinyal untuk pembaruan tata letak
                self.data_changed.emit()
            except Exception as e:
                logger.error(f"Gagal memperbarui data: {e}")

    def add_pair(self, pair):
        if not pair:
            return False
        try:
            future = asyncio.run_coroutine_threadsafe(
                self.websocket_handler.add_pair(pair),
                self.websocket_handler.loop
            )
            is_added = future.result()
            return is_added
        except Exception as e:
            logger.error(f"Gagal menambahkan pasangan: {e}")
            return False

    def delete_pair(self, pair):
        try:
            with self.data_lock:
                self.websocket_handler.remove_pair(pair)
                existing_index = self._data.index[self._data["PAIR"] == pair].tolist()
                if existing_index:
                    row = existing_index[0]
                    self.beginRemoveRows(QModelIndex(), row, row)
                    self._data.drop(row, inplace=True)
                    self.endRemoveRows()
        except Exception as e:
            logger.error(f"Gagal menghapus pasangan: {e}")

    def delete_selected_rows(self, selected_rows):
        try:
            with self.data_lock:
                selected_rows.sort(reverse=True)
                for row in selected_rows:
                    pair = self._data.iloc[row]["PAIR"]
                    self.websocket_handler.remove_pair(pair)
                    self.beginRemoveRows(QModelIndex(), row, row)
                    self._data.drop(index=row, inplace=True)
                    self.endRemoveRows()
                self._data.reset_index(drop=True, inplace=True)
                self.layoutChanged.emit()
        except Exception as e:
            logger.error(f"Gagal menghapus baris yang dipilih: {e}")

    def sort(self, column: int, order: Qt.SortOrder):
        try:
            with self.data_lock:
                if column < 0 or column >= len(self._headers):
                    raise ValueError(f"Invalid column index: {column}")
                col_name = self._headers[column]
                ascending = (order == Qt.AscendingOrder)
                if col_name in ["24%", "PRICE", "BVOLUME", "QVOLUME"]:
                    self._data[col_name] = pd.to_numeric(self._data[col_name], errors='coerce')
                self._data.sort_values(by=col_name, ascending=ascending, inplace=True)
                self._data.reset_index(drop=True, inplace=True)
                self.layoutChanged.emit()
        except Exception as e:
            logger.error(f"Gagal mengurutkan data: {e}")

    def export_market_data(self, file_name):
        with self.data_lock:
            try:
                logger.info(f"Menjalankan ekspor data ke file: {file_name}")
                self._data.to_csv(file_name, index=False)
                logger.info("Data berhasil diekspor.")
            except Exception as e:
                logger.error(f"Gagal mengekspor data ke file: {file_name}, error: {e}")
                raise e

    def import_csv(self, file_name):
        self.thread = ImportCSVThread(file_name, self)
        self.thread.data_changed.connect(self.handle_data_changed)
        self.thread.result.connect(self.handle_import_result)
        self.thread.start()

    @pyqtSlot()
    def handle_data_changed(self):
        self.layoutChanged.emit()

    @pyqtSlot(bool)
    def handle_import_result(self, success):
        if success:
            logger.info("Impor data selesai.")
        else:
            logger.error("Impor data gagal.")

    def format_price(self, value):
        try:
            return f"{float(value)}"
        except ValueError:
            logger.error(f"Format harga tidak valid: {value}")
            return value

    def format_percentage_or_volume(self, value):
        try:
            return f"{float(value):.2f}"
        except ValueError:
            logger.error(f"Format persentase atau volume tidak valid: {value}")
            return value

    def get_brush(self, value, role):
        try:
            change_percentage = float(value)
            if role == Qt.BackgroundRole:
                if change_percentage < 0:
                    return QBrush(QColor('red'))
                elif change_percentage > 0:
                    return QBrush(QColor('green'))
            elif role == Qt.ForegroundRole:
                if change_percentage < 0 or change_percentage > 0:
                    return QBrush(QColor('white'))
        except ValueError:
            logger.error(f"Format brush tidak valid untuk nilai: {value}")
            return None
