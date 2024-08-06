from PyQt5.QtCore import QAbstractTableModel, Qt
from PyQt5.QtGui import QColor, QBrush, QFont
from utils.logging_config import configure_logging

logger = configure_logging('market_data_table_model', 'logs/market_data_table_model.log')

class MarketDataTableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        self._headers = ["TIME", "PAIR", "24%", "PRICE", "VOLUME"]
        logger.debug("MarketDataTableModel diinisialisasi dengan data awal: %s", data)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        value = self._data[index.row()][index.column()]
        logger.debug("Mengambil data untuk index (%d, %d): %s", index.row(), index.column(), value)

        if role == Qt.DisplayRole:
            if index.column() in [2, 4]:
                try:
                    return f"{float(value):.2f}"
                except ValueError:
                    return value
            return value

        if role == Qt.BackgroundRole:
            if index.column() == 2:
                try:
                    change_percentage = float(value)
                    if change_percentage < 0:
                        return QBrush(QColor('red'))
                    elif change_percentage > 0:
                        return QBrush(QColor('green'))
                except ValueError:
                    logger.warning("Gagal memparse persentase perubahan: %s", value)
                    return None

        if role == Qt.ForegroundRole:
            if index.column() == 2:
                try:
                    change_percentage = float(value)
                    if change_percentage < 0 or change_percentage > 0:
                        return QBrush(QColor('white'))
                except ValueError:
                    logger.warning("Gagal memparse persentase perubahan: %s", value)
                    return None

        return None

    def rowCount(self, index):
        count = len(self._data)
        logger.debug("Jumlah baris: %d", count)
        return count

    def columnCount(self, index):
        count = len(self._headers)
        logger.debug("Jumlah kolom: %d", count)
        return count

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                header = self._headers[section]
                logger.debug("Header data untuk kolom %d: %s", section, header)
                return header
        if role == Qt.FontRole and orientation == Qt.Horizontal:
            font = QFont()
            font.setBold(True)
            logger.debug("Font untuk header kolom %d diatur menjadi bold", section)
            return font
        return None

    def update_data(self, new_data):
        logger.debug("Memperbarui data tabel dengan data baru: %s", new_data)
        try:
            self.beginResetModel()
            self._data = new_data
            self.endResetModel()
            logger.info("Data tabel berhasil diperbarui")
        except Exception as e:
            logger.error(f"Gagal memperbarui data tabel: {e}")

    def import_data(self, headers, new_data):
        logger.debug("Mengimpor data baru: %s", new_data)
        try:
            existing_data = {row[1]: row for row in self._data}

            for row in new_data:
                pair = row[1]
                if pair in existing_data:
                    existing_data[pair] = row
                else:
                    existing_data[pair] = row

            self._data = list(existing_data.values())

            self.beginResetModel()
            self.endResetModel()
            logger.info("Data tabel berhasil diimpor dan diperbarui")
        except Exception as e:
            logger.error(f"Gagal mengimpor data tabel: {e}")

    def remove_rows(self, rows):
        logger.debug("Menghapus baris: %s", rows)
        try:
            self.beginResetModel()
            self._data = [row for i, row in enumerate(self._data) if i not in rows]
            self.endResetModel()
            logger.info("Baris berhasil dihapus")
        except Exception as e:
            logger.error(f"Gagal menghapus baris: {e}")

    def get_data(self, row, column):
        if row < 0 or row >= len(self._data) or column < 0 or column >= len(self._headers):
            return None
        return self._data[row][column]

    def find_row_by_pair(self, pair):
        for row in range(len(self._data)):
            if self._data[row][1] == pair:
                return row
        return -1
