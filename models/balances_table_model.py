from PyQt5.QtCore import QAbstractTableModel, Qt
from logging_config import configure_logging

# Konfigurasi logging untuk balances_table_model
logger = configure_logging('balances_table_model', 'logs/balances_table_model.log')

class BalancesTableModel(QAbstractTableModel):
    """
    Model tabel untuk menampilkan saldo akun.

    Attributes:
        _data (list): Data saldo yang akan ditampilkan di tabel.
    """
    def __init__(self, data):
        logger.debug("Inisialisasi BalancesTableModel")
        super(BalancesTableModel, self).__init__()
        self._data = data if data else [[]]  # Inisialisasi dengan data atau list kosong jika tidak ada data
        logger.debug(f"Data model inisialisasi dengan {len(self._data)} baris.")

    def data(self, index, role):
        """
        Mengambil data untuk sel tertentu.

        Args:
            index (QModelIndex): Index dari sel yang diminta datanya.
            role (int): Peran untuk data yang diminta.

        Returns:
            Any: Data untuk sel yang diminta.
        """
        if role == Qt.DisplayRole:
            value = self._data[index.row()][index.column()]
            if index.column() in [1, 2]:
                value = round(value, 2)
            logger.debug(f"Data pada {index.row()}, {index.column()} adalah {value}")
            return value

    def rowCount(self, index):
        """
        Menghitung jumlah baris dalam tabel.

        Args:
            index (QModelIndex): Index model.

        Returns:
            int: Jumlah baris dalam tabel.
        """
        count = len(self._data)
        logger.debug(f"Jumlah baris dalam model: {count}")
        return count

    def columnCount(self, index):
        """
        Menghitung jumlah kolom dalam tabel.

        Args:
            index (QModelIndex): Index model.

        Returns:
            int: Jumlah kolom dalam tabel.
        """
        count = len(self._data[0]) if self._data else 0  # Pastikan tidak terjadi IndexError
        logger.debug(f"Jumlah kolom dalam model: {count}")
        return count

    def headerData(self, section, orientation, role):
        """
        Mengambil data header untuk tabel.

        Args:
            section (int): Bagian dari header (baris/kolom).
            orientation (Qt.Orientation): Orientasi dari header.
            role (int): Peran untuk data yang diminta.

        Returns:
            Any: Data untuk header yang diminta.
        """
        headers = ["Asset", "Available", "Locked"]
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                logger.debug(f"Header horizontal untuk kolom {section} adalah {headers[section]}")
                return headers[section]
            if orientation == Qt.Vertical:
                logger.debug(f"Header vertical untuk baris {section} adalah {section + 1}")
                return section + 1
