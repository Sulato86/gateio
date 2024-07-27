import pandas as pd
from PyQt5.QtCore import QAbstractTableModel, QSortFilterProxyModel, Qt
from control.logging_config import setup_logging

# Konfigurasi logging
logger = setup_logging('pandasa.log')

class PandasModel(QAbstractTableModel):
    """
    Kelas PandasModel mengimplementasikan model tabel berdasarkan DataFrame Pandas untuk digunakan dalam Qt.
    """

    def __init__(self, data):
        """
        Inisialisasi model dengan DataFrame.

        :param data: DataFrame yang akan digunakan sebagai sumber data.
        """
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        """
        Mengembalikan jumlah baris dalam model.

        :param parent: Indeks induk (tidak digunakan).
        :return: Jumlah baris dalam DataFrame.
        """
        return len(self._data)

    def columnCount(self, parent=None):
        """
        Mengembalikan jumlah kolom dalam model.

        :param parent: Indeks induk (tidak digunakan).
        :return: Jumlah kolom dalam DataFrame.
        """
        return len(self._data.columns)

    def data(self, index, role=Qt.DisplayRole):
        """
        Mengembalikan data untuk sel tertentu dalam model.

        :param index: Indeks dari sel yang diminta datanya.
        :param role: Peran data yang diminta (default: Qt.DisplayRole).
        :return: Data untuk sel yang diberikan atau None jika indeks tidak valid.
        """
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            if pd.isnull(value):
                return ""
            return str(value)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
        Mengembalikan data header untuk baris atau kolom tertentu.

        :param section: Indeks dari baris atau kolom.
        :param orientation: Orientasi header (horizontal atau vertikal).
        :param role: Peran data yang diminta (default: Qt.DisplayRole).
        :return: Data header untuk bagian yang diberikan atau None jika peran bukan Qt.DisplayRole.
        """
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self._data.columns[section]
        if orientation == Qt.Vertical:
            return self._data.index[section]
        return None

    def sort(self, column, order):
        """
        Mengurutkan data dalam model berdasarkan kolom tertentu.

        :param column: Indeks kolom yang akan digunakan untuk pengurutan.
        :param order: Urutan pengurutan (Qt.AscendingOrder atau Qt.DescendingOrder).
        """
        colname = self._data.columns[column]
        self.layoutAboutToBeChanged.emit()
        self._data.sort_values(by=[colname], ascending=(order == Qt.AscendingOrder), inplace=True)
        self.layoutChanged.emit()
        logger.debug(f"Data sorted by {colname} in {'ascending' if order == Qt.AscendingOrder else 'descending'} order")

    def update_data(self, data):
        """
        Memperbarui data dalam model dengan DataFrame baru.

        :param data: DataFrame baru yang akan digunakan sebagai sumber data.
        """
        self.layoutAboutToBeChanged.emit()
        self._data = data
        self.layoutChanged.emit()
        logger.debug("Data model updated")

class CustomSortFilterProxyModel(QSortFilterProxyModel):
    """
    Kelas CustomSortFilterProxyModel mengimplementasikan model proxy untuk penyortiran dan penyaringan khusus.
    """

    def lessThan(self, left, right):
        """
        Menentukan urutan kurang dari untuk dua item.

        :param left: Indeks dari item kiri.
        :param right: Indeks dari item kanan.
        :return: True jika item kiri kurang dari item kanan, False sebaliknya.
        """
        left_data = self.sourceModel().data(left, Qt.DisplayRole)
        right_data = self.sourceModel().data(right, Qt.DisplayRole)
        column = left.column()
        pair_column_index = 1
        
        if column == pair_column_index:
            result = left_data < right_data
            logger.debug(f"Comparing pairs: {left_data} < {right_data}: {result}")
            return result
        else:
            try:
                left_data = float(left_data)
                right_data = float(right_data)
                result = left_data < right_data
                logger.debug(f"Comparing numerical data: {left_data} < {right_data}: {result}")
                return result
            except ValueError:
                result = left_data < right_data
                logger.debug(f"Comparing string data: {left_data} < {right_data}: {result}")
                return result

    def filterAcceptsRow(self, source_row, source_parent):
        """
        Menentukan apakah baris tertentu diterima oleh filter.

        :param source_row: Indeks baris sumber.
        :param source_parent: Indeks induk sumber.
        :return: True jika baris diterima oleh filter, False sebaliknya.
        """
        return super().filterAcceptsRow(source_row, source_parent)
