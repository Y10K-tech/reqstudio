from __future__ import annotations

import re
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox


class FindReplaceDialog(QDialog):
    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Find & Replace")
        self.editor = editor

        v = QVBoxLayout(self)
        self.in_find = QLineEdit(); v.addWidget(QLabel("Find:")); v.addWidget(self.in_find)
        self.in_replace = QLineEdit(); v.addWidget(QLabel("Replace:")); v.addWidget(self.in_replace)
        self.cb_regex = QCheckBox("Regex"); self.cb_case = QCheckBox("Match case")
        row = QHBoxLayout(); row.addWidget(self.cb_regex); row.addWidget(self.cb_case)
        v.addLayout(row)
        row2 = QHBoxLayout()
        self.btn_find = QPushButton("Find Next"); row2.addWidget(self.btn_find)
        self.btn_replace = QPushButton("Replace"); row2.addWidget(self.btn_replace)
        self.btn_replace_all = QPushButton("Replace All"); row2.addWidget(self.btn_replace_all)
        self.btn_close = QPushButton("Close"); row2.addWidget(self.btn_close)
        v.addLayout(row2)

        self.btn_find.clicked.connect(self.on_find_next)
        self.btn_replace.clicked.connect(self.on_replace)
        self.btn_replace_all.clicked.connect(self.on_replace_all)
        self.btn_close.clicked.connect(self.close)

    def _flags(self):
        return 0 if self.cb_case.isChecked() else re.IGNORECASE

    def on_find_next(self):
        term = self.in_find.text()
        if not term:
            return
        doc = self.editor.document()
        cursor = self.editor.textCursor()
        if self.cb_regex.isChecked():
            # fallback regex search: convert whole text
            text = self.editor.toPlainText()
            m = re.search(term, text[cursor.position():], flags=self._flags())
            if not m:
                m = re.search(term, text, flags=self._flags())
                if not m:
                    return
                start = m.start()
            else:
                start = cursor.position() + m.start()
            c = self.editor.textCursor()
            c.setPosition(start); c.setPosition(start + (m.end()-m.start()), c.MoveMode.KeepAnchor)
            self.editor.setTextCursor(c)
        else:
            cursor = doc.find(term, cursor)
            if cursor.isNull():
                cursor = doc.find(term)
            if not cursor.isNull():
                self.editor.setTextCursor(cursor)

    def on_replace(self):
        if not self.editor.textCursor().hasSelection():
            self.on_find_next()
        c = self.editor.textCursor()
        if c.hasSelection():
            c.insertText(self.in_replace.text())

    def on_replace_all(self):
        find = self.in_find.text()
        repl = self.in_replace.text()
        if not find:
            return
        text = self.editor.toPlainText()
        if self.cb_regex.isChecked():
            text = re.sub(find, repl, text, flags=self._flags())
        else:
            flags = 0 if self.cb_case.isChecked() else re.IGNORECASE
            # simple case-insensitive replace
            if flags == re.IGNORECASE:
                def repl_ci(m: re.Match):
                    return repl
                text = re.sub(re.escape(find), repl_ci, text, flags=flags)
            else:
                text = text.replace(find, repl)
        self.editor.setPlainText(text)

