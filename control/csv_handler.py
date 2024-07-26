import csv
from PyQt5.QtCore import QThread, pyqtSignal, Qt

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
                
                for row in range(self.model.rowCount()):
                    rowData = [self.model.index(row, column).data() for column in range(self.model.columnCount())]
                    writer.writerow(rowData)
                    self.progress.emit(int((row + 1) / self.model.rowCount() * 100))
            self.finished.emit(f"Data berhasil diekspor ke {self.filePath}")
        except Exception as e:
            self.finished.emit(f"Ekspor gagal: {str(e)}")
