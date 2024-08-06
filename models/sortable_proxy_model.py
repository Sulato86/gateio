from PyQt5.QtCore import QSortFilterProxyModel, Qt

class SortableProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(SortableProxyModel, self).__init__(parent)

    def lessThan(self, left, right):
        left_data = self.sourceModel().data(left, Qt.DisplayRole)
        right_data = self.sourceModel().data(right, Qt.DisplayRole)

        try:
            left_value = float(left_data)
            right_value = float(right_data)
            return left_value < right_value
        except ValueError:
            return left_data < right_data
