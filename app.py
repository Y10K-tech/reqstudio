import os
import sys
import re
import difflib
from pathlib import Path

from PyQt6.QtCore import Qt, QSettings, QSaveFile, QFileInfo
from PyQt6.QtGui import QAction, QIcon, QFont, QTextCursor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QTextEdit, QMessageBox,
    QStatusBar, QToolBar, QDialog, QVBoxLayout, QListWidget, QWidget,
    QSplitter, QPlainTextEdit, QLabel, QHBoxLayout, QLineEdit, QPushButton,
    QCheckBox
)
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

from core.git_backend import GitFacade, GitError
from core.highlighter import MarkdownHighlighter
from core.templates import TEMPLATES
from core.utils import detect_srs_ids, normalize_newlines


APP_NAME = "Y10K ReqStudio"
ORG = "Y10K Software Engineering"
SRS_ID_REGEX = r"\bY10K-[A-Z0-9]+-[A-Z0-9]+-(HL|LL|CMP|API|DB|TST)-\d{3}\b"


class HistoryDialog(QDialog):
    def __init__(self, repo, file_abspath, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historik (nuvarande fil)")
        self.resize(1000, 700)
        self.repo = repo
        self.file_abspath = file_abspath

        layout = QVBoxLayout(self)

        info = QLabel(f"Fil: {file_abspath}")
        info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(info)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # commit-list vänster
        self.list = QListWidget()
        splitter.addWidget(self.list)

        # viewer höger (två paneler: commit-innehåll och diff mot arbetsfil)
        right = QWidget()
        right_layout = QVBoxLayout(right)

        self.commit_label = QLabel("Commit: -")
        right_layout.addWidget(self.commit_label)

        self.text_commit = QPlainTextEdit()
        self.text_commit.setReadOnly(True)
        font = QFont("Consolas" if sys.platform.startswith("win") else "Monospace")
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        self.text_commit.setFont(font)
        right_layout.addWidget(self.text_commit, 2)

        self.diff_label = QLabel("Diff mot aktuell buffert:")
        right_layout.addWidget(self.diff_label)

        self.text_diff = QPlainTextEdit()
        self.text_diff.setReadOnly(True)
        self.text_diff.setFont(font)
        right_layout.addWidget(self.text_diff, 3)

        splitter.addWidget(right)
        splitter.setSizes([300, 700])

        # Ladda commits
        rel = self.repo.relpath(file_abspath)
        commits = self.repo.log_file(rel, max_count=200)
        for c in commits:
            self.list.addItem(f"{c['short']}  {c['when']}  {c['author']}: {c['msg']}")

        self.commits = commits
        self.list.currentRowChanged.connect(self.on_row)
        if commits:
            self.list.setCurrentRow(0)

    def on_row(self, row):
        if row < 0:
            return
        commit = self.commits[row]
        self.commit_label.setText(f"Commit: {commit['hash']}")
        rel = self.repo.relpath(self.file_abspath)
        try:
            content = self.repo.get_file_at_commit(commit['hash'], rel)
        except GitError as e:
            QMessageBox.critical(self, "Git-fel", str(e))
            return
        self.text_commit.setPlainText(content)

        # Gör diff mot nuvarande text i editorn om huvudfönstret finns
        parent = self.parent()
        current = ""
        if parent and isinstance(parent, QMainWindow) and hasattr(parent, "editor"):
            current = parent.editor.toPlainText()
        diff = difflib.unified_diff(
            content.splitlines(), current.splitlines(),
            fromfile=f"{rel}@{commit['short']}",
            tofile=f"{rel}@WORKTREE",
            lineterm=""
        )
        self.text_diff.setPlainText("\n".join(diff))


class CommitDialog(QDialog):
    def __init__(self, default_message, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Git Commit")
        self.resize(600, 220)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Commit-meddelande:"))
        self.msg = QLineEdit(default_message)
        layout.addWidget(self.msg)

        self.cb_stage_all = QCheckBox("Stage ALLA ändrade filer i arbetsytan (inte bara denna fil)")
        self.cb_stage_all.setChecked(False)
        layout.addWidget(self.cb_stage_all)

        btns = QHBoxLayout()
        self.ok = QPushButton("Commit")
        self.cancel = QPushButton("Avbryt")
        btns.addWidget(self.ok)
        btns.addWidget(self.cancel)
        layout.addLayout(btns)

        self.ok.clicked.connect(self.accept)
        self.cancel.clicked.connect(self.reject)

    def values(self):
        return self.msg.text().strip(), self.cb_stage_all.isChecked()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}")
        self.resize(1200, 800)

        self.settings = QSettings(ORG, APP_NAME)

        self.editor = QTextEdit()
        font = QFont("Consolas" if sys.platform.startswith("win") else "Monospace")
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        font.setPointSize(11)
        self.editor.setFont(font)
        self.setCentralWidget(self.editor)

        self.highlighter = MarkdownHighlighter(self.editor.document(), SRS_ID_REGEX)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self.current_file: Path | None = None
        self.workspace: Path | None = None
        self.repo = GitFacade()

        self._make_actions()
        self._make_menus()
        self._make_toolbar()
        self._wire_signals()

        # Återställ senaste arbetsyta
        last_ws = self.settings.value("workspace", "")
        if last_ws and Path(last_ws).exists():
            self.load_workspace(Path(last_ws))

        self.update_status()

    # UI wiring
    def _make_actions(self):
        self.act_new = QAction("Ny", self)
        self.act_open = QAction("Öppna fil…", self)
        self.act_open_ws = QAction("Öppna arbetsyta…", self)
        self.act_save = QAction("Spara", self)
        self.act_save_as = QAction("Spara som…", self)
        self.act_export_pdf = QAction("Exportera som PDF…", self)
        self.act_exit = QAction("Avsluta", self)

        self.act_undo = QAction("Ångra", self)
        self.act_redo = QAction("Gör om", self)
        self.act_cut = QAction("Klipp ut", self)
        self.act_copy = QAction("Kopiera", self)
        self.act_paste = QAction("Klistra in", self)
        self.act_find = QAction("Sök…", self)

        # Templates
        self.template_actions = {}
        for key, meta in TEMPLATES.items():
            a = QAction(f"Infoga: {meta['title']}", self)
            self.template_actions[key] = a

        # Git
        self.act_git_init = QAction("Initiera repo här", self)
        self.act_git_commit = QAction("Stage & Commit…", self)
        self.act_git_branch_create = QAction("Skapa branch…", self)
        self.act_git_branch_switch = QAction("Byt branch…", self)
        self.act_git_history = QAction("Historik (denna fil)…", self)
        self.act_git_push = QAction("Push", self)
        self.act_git_pull = QAction("Pull", self)

        # Verktyg
        self.act_validate_ids = QAction("Validera SRS-ID i dokument", self)

        # Shortcuts
        self.act_new.setShortcut("Ctrl+N")
        self.act_open.setShortcut("Ctrl+O")
        self.act_save.setShortcut("Ctrl+S")
        self.act_save_as.setShortcut("Ctrl+Shift+S")
        self.act_export_pdf.setShortcut("Ctrl+P")
        self.act_find.setShortcut("Ctrl+F")
        self.act_undo.setShortcut("Ctrl+Z")
        self.act_redo.setShortcut("Ctrl+Y")

        # Rendering toggle
        self.act_toggle_md = QAction("Realtime Markdown Rendering", self)
        self.act_toggle_md.setCheckable(True)
        self.act_toggle_md.setChecked(True)

    def _make_menus(self):
        m_file = self.menuBar().addMenu("&Arkiv")
        m_file.addAction(self.act_new)
        m_file.addAction(self.act_open)
        m_file.addSeparator()
        m_file.addAction(self.act_open_ws)
        m_file.addSeparator()
        m_file.addAction(self.act_save)
        m_file.addAction(self.act_save_as)
        m_file.addSeparator()
        m_file.addAction(self.act_export_pdf)
        m_file.addSeparator()
        m_file.addAction(self.act_exit)

        m_edit = self.menuBar().addMenu("&Redigera")
        m_edit.addAction(self.act_undo)
        m_edit.addAction(self.act_redo)
        m_edit.addSeparator()
        m_edit.addAction(self.act_cut)
        m_edit.addAction(self.act_copy)
        m_edit.addAction(self.act_paste)
        m_edit.addSeparator()
        m_edit.addAction(self.act_find)

        m_tpl = self.menuBar().addMenu("&Mallar")
        for a in self.template_actions.values():
            m_tpl.addAction(a)

        m_git = self.menuBar().addMenu("&Git")
        m_git.addAction(self.act_git_init)
        m_git.addSeparator()
        m_git.addAction(self.act_git_commit)
        m_git.addAction(self.act_git_history)
        m_git.addSeparator()
        m_git.addAction(self.act_git_branch_create)
        m_git.addAction(self.act_git_branch_switch)
        m_git.addSeparator()
        m_git.addAction(self.act_git_pull)
        m_git.addAction(self.act_git_push)

        m_tools = self.menuBar().addMenu("&Verktyg")
        m_tools.addAction(self.act_toggle_md)
        m_tools.addAction(self.act_validate_ids)

    def _make_toolbar(self):
        tb = QToolBar("Snabbverktyg")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)
        for a in [self.act_new, self.act_open, self.act_save, self.act_export_pdf,
                  self.act_git_commit, self.act_git_history]:
            tb.addAction(a)
        tb.addSeparator()
        tb.addAction(self.act_toggle_md)

    def _wire_signals(self):
        self.act_new.triggered.connect(self.on_new)
        self.act_open.triggered.connect(self.on_open)
        self.act_open_ws.triggered.connect(self.on_open_workspace)
        self.act_save.triggered.connect(self.on_save)
        self.act_save_as.triggered.connect(self.on_save_as)
        self.act_export_pdf.triggered.connect(self.on_export_pdf)
        self.act_exit.triggered.connect(self.close)

        self.act_undo.triggered.connect(self.editor.undo)
        self.act_redo.triggered.connect(self.editor.redo)
        self.act_cut.triggered.connect(self.editor.cut)
        self.act_copy.triggered.connect(self.editor.copy)
        self.act_paste.triggered.connect(self.editor.paste)
        self.act_find.triggered.connect(self.on_find)

        for key, act in self.template_actions.items():
            act.triggered.connect(lambda checked=False, k=key: self.insert_template(k))

        self.act_git_init.triggered.connect(self.on_git_init)
        self.act_git_commit.triggered.connect(self.on_git_commit)
        self.act_git_branch_create.triggered.connect(self.on_git_branch_create)
        self.act_git_branch_switch.triggered.connect(self.on_git_branch_switch)
        self.act_git_history.triggered.connect(self.on_git_history)
        self.act_git_pull.triggered.connect(self.on_git_pull)
        self.act_git_push.triggered.connect(self.on_git_push)

        self.editor.textChanged.connect(self.update_status)
        self.act_toggle_md.toggled.connect(self.on_toggle_markdown)

    def on_toggle_markdown(self, enabled: bool):
        # Attach/detach the syntax highlighter to enable/disable live rendering
        if enabled:
            self.highlighter.setDocument(self.editor.document())
            self.highlighter.rehighlight()
        else:
            self.highlighter.setDocument(None)

    # File ops
    def on_new(self):
        if not self.maybe_save():
            return
        self.editor.clear()
        self.current_file = None
        self.update_window_title()

    def on_open(self):
        if not self.workspace:
            QMessageBox.information(self, "Ingen arbetsyta",
                                    "Öppna först en arbetsyta (mapp).")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Öppna fil", str(self.workspace),
            "Text/Markdown (*.md *.markdown *.txt);;Alla filer (*.*)"
        )
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        self.editor.setPlainText(normalize_newlines(text))
        self.current_file = Path(path)
        self.update_window_title()
        self.update_status()

    def on_open_workspace(self):
        d = QFileDialog.getExistingDirectory(self, "Välj arbetsyta (mapp)")
        if not d:
            return
        self.load_workspace(Path(d))

    def load_workspace(self, path: Path):
        self.workspace = path
        self.settings.setValue("workspace", str(path))
        self.status.showMessage(f"Arbetsyta: {path}", 5000)
        # Ladda/öppna git
        try:
            self.repo.open(path)
        except GitError:
            # Ingen repo – ok
            pass
        self.update_status()

    def on_save(self):
        if not self.current_file:
            return self.on_save_as()
        self._save_to_path(self.current_file)

    def on_save_as(self):
        if not self.workspace:
            QMessageBox.information(self, "Ingen arbetsyta",
                                    "Öppna först en arbetsyta (mapp).")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Spara som", str(self.workspace / "untitled.md"),
            "Markdown (*.md);;Text (*.txt);;Alla filer (*.*)"
        )
        if not path:
            return
        self.current_file = Path(path)
        self._save_to_path(self.current_file)
        self.update_window_title()

    def _save_to_path(self, path: Path):
        text = self.editor.toPlainText()
        sf = QSaveFile(str(path))
        if not sf.open(QSaveFile.OpenModeFlag.WriteOnly | QSaveFile.OpenModeFlag.Text):
            QMessageBox.critical(self, "Fel", "Kunde inte spara filen.")
            return
        sf.write(text.encode("utf-8"))
        if not sf.commit():
            QMessageBox.critical(self, "Fel", "Kunde inte committa skrivning.")
            return
        self.status.showMessage(f"Sparad: {path}", 3000)
        self.update_status()

    def on_export_pdf(self):
        if self.editor.document().isEmpty():
            QMessageBox.information(self, "Tomt dokument", "Inget att exportera.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportera som PDF", str(self.workspace or Path.cwd() / "document.pdf"),
            "PDF (*.pdf)"
        )
        if not path:
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)
        # Skriv ut (plaintext -> PDF)
        self.editor.document().print(printer)
        self.status.showMessage(f"PDF exporterad: {path}", 5000)

    # Tools
    def on_find(self):
        term, ok = QFileDialog.getText(self, "Sök", "Sökterm:")
        # QFileDialog.getText finns inte – använd enkel dialog via QInputDialog
        from PyQt6.QtWidgets import QInputDialog
        term, ok = QInputDialog.getText(self, "Sök", "Sökterm:")
        if not ok or not term:
            return
        doc = self.editor.document()
        cursor = self.editor.textCursor()
        cursor = doc.find(term, cursor)
        if cursor.isNull():
            cursor = doc.find(term)
        if not cursor.isNull():
            self.editor.setTextCursor(cursor)
            self.status.showMessage(f"Hittade '{term}'", 2000)
        else:
            QMessageBox.information(self, "Sök", f"Inget resultat för '{term}'.")

    def insert_template(self, key: str):
        meta = TEMPLATES[key]
        cursor = self.editor.textCursor()
        if not cursor:
            cursor = QTextCursor(self.editor.document())
        block = meta["content"].strip() + "\n"
        cursor.insertText(block)

    def on_git_init(self):
        if not self.workspace:
            QMessageBox.information(self, "Ingen arbetsyta", "Öppna en arbetsyta först.")
            return
        try:
            self.repo.init(self.workspace)
            QMessageBox.information(self, "Git", f"Initierade Git-repo i {self.workspace}")
        except GitError as e:
            QMessageBox.critical(self, "Git-fel", str(e))
        self.update_status()

    def on_git_commit(self):
        if not self.workspace or not self.current_file:
            QMessageBox.information(self, "Git", "Spara en fil i en arbetsyta först.")
            return
        # Spara ev. osparat
        if self.editor.document().isModified():
            self.on_save()
        # Förifyll commit-meddelande med SRS-ID om hittad
        text = self.editor.toPlainText()
        ids = detect_srs_ids(text, SRS_ID_REGEX)
        default_msg = ids[0] + " – uppdaterad kravspec" if ids else "Uppdaterad kravspec"
        dlg = CommitDialog(default_msg, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        msg, stage_all = dlg.values()
        try:
            if not self.repo.is_open():
                # försök öppna
                self.repo.open(self.workspace)
            paths = None if stage_all else [self.current_file]
            self.repo.commit(paths=paths, message=msg)
            QMessageBox.information(self, "Git", "Commit klar.")
        except GitError as e:
            QMessageBox.critical(self, "Git-fel", str(e))
        self.update_status()

    def on_git_branch_create(self):
        if not self.repo.is_open():
            QMessageBox.information(self, "Git", "Initiera/öppna repo först.")
            return
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Ny branch", "Branch-namn (t.ex. feature/Y10K-ACME-AUTH-LL-003-login):")
        if not ok or not name.strip():
            return
        try:
            self.repo.create_branch(name.strip(), checkout=True)
            self.status.showMessage(f"Bytte till branch {name}", 4000)
        except GitError as e:
            QMessageBox.critical(self, "Git-fel", str(e))
        self.update_status()

    def on_git_branch_switch(self):
        if not self.repo.is_open():
            QMessageBox.information(self, "Git", "Initiera/öppna repo först.")
            return
        branches = self.repo.list_branches()
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getItem(self, "Byt branch", "Välj branch:", branches, 0, False)
        if not ok or not name:
            return
        try:
            self.repo.checkout(name)
            self.status.showMessage(f"Bytte till branch {name}", 4000)
        except GitError as e:
            QMessageBox.critical(self, "Git-fel", str(e))
        self.update_status()

    def on_git_history(self):
        if not self.repo.is_open() or not self.current_file:
            QMessageBox.information(self, "Git", "Öppna repo och en fil först.")
            return
        dlg = HistoryDialog(self.repo, str(self.current_file), self)
        dlg.exec()

    def on_git_pull(self):
        if not self.repo.is_open():
            QMessageBox.information(self, "Git", "Initiera/öppna repo först.")
            return
        try:
            out = self.repo.pull()
            QMessageBox.information(self, "Git Pull", out or "OK")
        except GitError as e:
            QMessageBox.critical(self, "Git-fel", str(e))

    def on_git_push(self):
        if not self.repo.is_open():
            QMessageBox.information(self, "Git", "Initiera/öppna repo först.")
            return
        try:
            out = self.repo.push()
            QMessageBox.information(self, "Git Push", out or "OK")
        except GitError as e:
            QMessageBox.critical(self, "Git-fel", str(e))

    def maybe_save(self) -> bool:
        if not self.editor.document().isModified():
            return True
        ret = QMessageBox.question(self, "Spara ändringar?",
                                   "Dokumentet har ändringar. Vill du spara?",
                                   QMessageBox.StandardButton.Yes |
                                   QMessageBox.StandardButton.No |
                                   QMessageBox.StandardButton.Cancel)
        if ret == QMessageBox.StandardButton.Yes:
            self.on_save()
            return True
        if ret == QMessageBox.StandardButton.No:
            return True
        return False

    def update_window_title(self):
        fn = str(self.current_file) if self.current_file else "untitled"
        branch = ""
        if self.repo and self.repo.is_open():
            try:
                branch = f" [{self.repo.current_branch()}]"
            except GitError:
                branch = ""
        self.setWindowTitle(f"{APP_NAME} — {fn}{branch}")

    def update_status(self):
        branch = "-"
        if self.repo.is_open():
            try:
                branch = self.repo.current_branch()
            except GitError:
                branch = "-"
        srs = detect_srs_ids(self.editor.toPlainText(), SRS_ID_REGEX)
        srs_show = ", ".join(srs) if srs else "–"
        ws = str(self.workspace) if self.workspace else "–"
        cur = str(self.current_file) if self.current_file else "–"
        self.status.showMessage(f"WS: {ws} | Fil: {cur} | Branch: {branch} | SRS-ID: {srs_show}")

    def closeEvent(self, event):
        if self.maybe_save():
            event.accept()
        else:
            event.ignore()


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName(ORG)
    app.setApplicationName(APP_NAME)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
