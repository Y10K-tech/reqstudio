from __future__ import annotations

from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton, QFileDialog
)


class WorkspaceStartupDialog(QDialog):
    def __init__(self, last_workspace: str | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Workspace")
        self.resize(520, 140)
        self._selected: str | None = None

        v = QVBoxLayout(self)
        v.addWidget(QLabel("Choose a workspace folder to open:"))

        row = QHBoxLayout()
        self.in_path = QLineEdit(last_workspace or "")
        self.in_path.setReadOnly(True)
        row.addWidget(self.in_path)
        self.btn_browse = QPushButton("Browse…")
        row.addWidget(self.btn_browse)
        v.addLayout(row)

        row2 = QHBoxLayout()
        self.btn_open = QPushButton("Open")
        self.btn_skip = QPushButton("Skip")
        row2.addWidget(self.btn_open)
        row2.addWidget(self.btn_skip)
        v.addLayout(row2)

        self.btn_browse.clicked.connect(self.on_browse)
        self.btn_open.clicked.connect(self.on_open)
        self.btn_skip.clicked.connect(self.reject)

    def on_browse(self):
        d = QFileDialog.getExistingDirectory(self, "Select Workspace")
        if d:
            self.in_path.setText(d)

    def on_open(self):
        path = self.in_path.text().strip()
        if path and Path(path).exists():
            self._selected = path
            self.accept()

    def selected_path(self) -> str | None:
        return self._selected

