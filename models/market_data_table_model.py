from PyQt5.QtCore import QAbstractTableModel, Qt
from PyQt5.QtGui import QColor, QBrush, QFont
from utils.logging_config import configure_logging

# Konfigurasi logger untuk MarketDataTableModel
logger = configure_logging('market_data_table_model', 'logs/market_data_table_model.log')

class MarketDataTableModel(QAbstractTableModel):
    def __init__(self, data):
        """
        Inisialisasi MarketDataTableModel.

        Args:
            data (list): Data awal untuk model tabel.
        """
        super().__init__()
        self._data = data
        self._headers = ["TIME", "PAIR", "24%", "PRICE", "VOLUME"]
        logger.debug("MarketDataTableModel diinisialisasi dengan data awal: %s", data)

    def data(self, index, role):
        """
        Mengembalikan data untuk tampilan tabel.

        Args:
            index (QModelIndex): Indeks model.
            role (int): Peran tampilan.

        Returns:
            Any: Data untuk tampilan.
        """
        if not index.isValid():
            return None

        value = self._data[index.row()][index.column()]
        logger.debug("Mengambil data untuk index (%d, %d): %s", index.row(), index.column(), value)

        if role == Qt.DisplayRole:
            if index.column() in [2, 4]:  # Kolom untuk persentase perubahan dan volume
                try:
                    return f"{float(value):.2f}"
                except ValueError:
                    return value
            return value

        if role == Qt.BackgroundRole:
            if index.column() == 2:  # Kolom untuk persentase perubahan
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
            if index.column() == 2:  # Kolom untuk persentase perubahan
                try:
                    change_percentage = float(value)
                    if change_percentage < 0 or change_percentage > 0:
                        return QBrush(QColor('white'))
                except ValueError:
                    logger.warning("Gagal memparse persentase perubahan: %s", value)
                    return None

        return None

    def rowCount(self, index):
        """
        Mengembalikan jumlah baris dalam model.

        Args:
            index (QModelIndex): Indeks model.

        Returns:
            int: Jumlah baris.
        """
        count = len(self._data)
        logger.debug("Jumlah baris: %d", count)
        return count

    def columnCount(self, index):
        """
        Mengembalikan jumlah kolom dalam model.

        Args:
            index (QModelIndex): Indeks model.

        Returns:
            int: Jumlah kolom.
        """
        count = len(self._headers)
        logger.debug("Jumlah kolom: %d", count)
        return count

    def headerData(self, section, orientation, role):
        """
        Mengembalikan data header untuk tampilan tabel.

        Args:
            section (int): Seksi header.
            orientation (Qt.Orientation): Orientasi header.
            role (int): Peran tampilan.

        Returns:
            Any: Data untuk header.
        """
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
        """
        Memperbarui data dalam model tabel.

        Args:
            new_data (list): Data baru untuk memperbarui model.
        """
        logger.debug("Memperbarui data tabel dengan data baru: %s", new_data)
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()
        logger.info("Data tabel berhasil diperbarui")
