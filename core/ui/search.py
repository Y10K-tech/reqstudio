from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QLineEdit, QPushButton, QListWidget


class SearchDock(QDockWidget):
    searchRequested = pyqtSignal(str)

    def __init__(self, title: str = "Search", parent=None):
        super().__init__(title, parent)
        cont = QWidget()
        v = QVBoxLayout(cont)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Search requirements…")
        self.btn = QPushButton("Search")
        self.results = QListWidget()
        v.addWidget(self.input)
        v.addWidget(self.btn)
        v.addWidget(self.results, 1)
        self.setWidget(cont)

        self.btn.clicked.connect(self._emit)
        self.input.returnPressed.connect(self._emit)

    def _emit(self):
        q = self.input.text().strip()
        self.searchRequested.emit(q)

    def setResults(self, lines: list[str]):
        self.results.clear()
        for line in lines:
            self.results.addItem(line)

