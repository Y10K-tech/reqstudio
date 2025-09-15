import sys
from pathlib import Path
import difflib

from PyQt6.QtCore import Qt, QSettings, QSaveFile
from PyQt6.QtGui import QAction, QFont, QTextCursor, QTextDocument
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QTextEdit,
    QMessageBox,
    QStatusBar,
    QToolBar,
    QDialog,
    QVBoxLayout,
    QListWidget,
    QWidget,
    QPlainTextEdit,
    QLabel,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QInputDialog,
    QStackedWidget,
)
from PyQt6.QtPrintSupport import QPrinter

from core.git_backend import GitFacade, GitError
from core.highlighter import MarkdownHighlighter, LivePreviewHighlighter
from core.templates import TEMPLATES
from core.utils import detect_srs_ids, normalize_newlines

try:
    import markdown as _markdown
except Exception:
    _markdown = None


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

        splitter = QWidget()
        s_layout = QVBoxLayout(splitter)
        layout.addWidget(splitter)

        self.list = QListWidget()
        s_layout.addWidget(self.list)

        self.commit_label = QLabel("Commit: -")
        s_layout.addWidget(self.commit_label)

        self.text_commit = QPlainTextEdit()
        self.text_commit.setReadOnly(True)
        font = QFont("Consolas")
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        self.text_commit.setFont(font)
        s_layout.addWidget(self.text_commit, 1)

        self.diff_label = QLabel("Diff mot aktuell buffert:")
        s_layout.addWidget(self.diff_label)

        self.text_diff = QPlainTextEdit()
        self.text_diff.setReadOnly(True)
        self.text_diff.setFont(font)
        s_layout.addWidget(self.text_diff, 2)

        rel = self.repo.relpath(file_abspath)
        commits = self.repo.log_file(rel, max_count=200)
        for c in commits:
            self.list.addItem(f"{c['short']}  {c['when']}  {c['author']}: {c['msg']}")
        self.commits = commits
        self.list.currentRowChanged.connect(self.on_row)
        if commits:
            self.list.setCurrentRow(0)

    def on_row(self, row: int):
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

        parent = self.parent()
        current = ""
        if parent and isinstance(parent, QMainWindow) and hasattr(parent, "editor"):
            current = parent.editor.toPlainText()
        diff = difflib.unified_diff(
            content.splitlines(), current.splitlines(),
            fromfile=f"{rel}@{commit['short']}",
            tofile=f"{rel}@WORKTREE",
            lineterm="",
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

        self.ok = QPushButton("Commit")
        self.cancel = QPushButton("Avbryt")
        row = QHBoxLayout()
        row.addWidget(self.ok)
        row.addWidget(self.cancel)
        layout.addLayout(row)

        self.ok.clicked.connect(self.accept)
        self.cancel.clicked.connect(self.reject)

    def values(self):
        return self.msg.text().strip()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 800)

        self.settings = QSettings(ORG, APP_NAME)

        # Source editor
        self.editor = QTextEdit()
        font = QFont("Consolas")
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        font.setPointSize(11)
        self.editor.setFont(font)
        self.highlighter = MarkdownHighlighter(self.editor.document(), SRS_ID_REGEX)

        # Rendered preview (single-pane mode when active)
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setAcceptRichText(True)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.editor)   # index 0
        self.stack.addWidget(self.preview)  # index 1
        self.setCentralWidget(self.stack)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self.current_file: Path | None = None
        self.workspace: Path | None = None
        self.repo = GitFacade()

        self._md_css = """
        body { font-family: system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif; font-size: 14px; color: #222; }
        h1 { font-size: 1.8em; margin: 0.8em 0 0.4em; }
        h2 { font-size: 1.6em; margin: 0.8em 0 0.4em; }
        h3 { font-size: 1.4em; margin: 0.8em 0 0.4em; }
        h4 { font-size: 1.2em; margin: 0.8em 0 0.4em; }
        h5 { font-size: 1.1em; margin: 0.8em 0 0.4em; }
        h6 { font-size: 1.0em; margin: 0.8em 0 0.4em; }
        p { margin: 0.4em 0 0.8em; }
        ul, ol { margin: 0.4em 0 0.8em 1.4em; }
        code { background: #f5f5f5; padding: 0 3px; border-radius: 3px; }
        pre { background: #f5f5f5; padding: 8px; border-radius: 4px; overflow-x: auto; }
        table { border-collapse: collapse; margin: 0.8em 0; }
        th, td { border: 1px solid #ddd; padding: 6px 10px; }
        blockquote { border-left: 3px solid #ccc; margin: 0.8em 0; padding: 0.2em 0 0.2em 0.8em; color: #555; }
        hr { border: none; border-top: 1px solid #ddd; margin: 1em 0; }
        """.strip()

        self._make_actions()
        self._make_menus()
        self._make_toolbar()
        self._wire_signals()

        last_ws = self.settings.value("workspace", "")
        if last_ws and Path(last_ws).exists():
            self.load_workspace(Path(last_ws))

        self.stack.setCurrentIndex(0)
        self.update_status()

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
        self.act_git_commit = QAction("Commit…", self)
        self.act_git_branch_create = QAction("Skapa branch…", self)
        self.act_git_branch_switch = QAction("Byt branch…", self)
        self.act_git_history = QAction("Historik (denna fil)…", self)
        self.act_git_push = QAction("Push", self)
        self.act_git_pull = QAction("Pull", self)

        # View / Tools
        self.act_toggle_md = QAction("Syntax highlighting", self)
        self.act_toggle_md.setCheckable(True)
        self.act_toggle_md.setChecked(True)

        self.act_live_preview = QAction("Realtime Markdown Preview", self)
        self.act_live_preview.setCheckable(True)
        self.act_live_preview.setChecked(False)

        self.act_inline_live = QAction("Live Inline Markdown", self)
        self.act_inline_live.setCheckable(True)
        self.act_inline_live.setChecked(False)

        # Shortcuts
        self.act_new.setShortcut("Ctrl+N")
        self.act_open.setShortcut("Ctrl+O")
        self.act_save.setShortcut("Ctrl+S")
        self.act_save_as.setShortcut("Ctrl+Shift+S")
        self.act_export_pdf.setShortcut("Ctrl+P")
        self.act_find.setShortcut("Ctrl+F")
        self.act_undo.setShortcut("Ctrl+Z")
        self.act_redo.setShortcut("Ctrl+Y")

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
        m_tools.addAction(self.act_live_preview)
        m_tools.addAction(self.act_inline_live)
        m_tools.addAction(self.act_toggle_md)

    def _make_toolbar(self):
        tb = QToolBar("Snabbverktyg")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)
        for a in [
            self.act_new,
            self.act_open,
            self.act_save,
            self.act_export_pdf,
            self.act_git_commit,
            self.act_git_history,
        ]:
            tb.addAction(a)
        tb.addSeparator()
        tb.addAction(self.act_live_preview)

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

        self.editor.textChanged.connect(self.on_editor_changed)

        self.act_toggle_md.toggled.connect(self.on_toggle_highlight)
        self.act_live_preview.toggled.connect(self.on_toggle_preview_mode)
        self.act_inline_live.toggled.connect(self.on_toggle_inline_live)
        self.editor.cursorPositionChanged.connect(self._on_cursor_pos_changed)

        # Inline live state
        self.live_highlighter = None
        self._inline_prev_blocknum = -1

    # Preview / render
    def render_markdown(self, text: str) -> str:
        if not _markdown:
            safe = (
                text.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
            )
            body = f"<pre>{safe}</pre>"
        else:
            try:
                body = _markdown.markdown(text, extensions=["extra"])  # tables, etc.
            except Exception:
                safe = (
                    text.replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                )
                body = f"<pre>{safe}</pre>"
        return f"<html><head><meta charset='utf-8'><style>{self._md_css}</style></head><body>{body}</body></html>"

    def update_preview(self):
        html = self.render_markdown(self.editor.toPlainText())
        self.preview.setHtml(html)

    def on_toggle_preview_mode(self, enabled: bool):
        # When enabled, switch to rendered preview; when disabled, return to source editor
        if enabled:
            self.update_preview()
            self.stack.setCurrentIndex(1)
        else:
            self.stack.setCurrentIndex(0)

    def on_toggle_inline_live(self, enabled: bool):
        # Inline live is mutually exclusive with full preview; ensure editor is visible
        if enabled:
            if self.stack.currentIndex() != 0:
                self.stack.setCurrentIndex(0)
            # detach normal highlighter
            self.highlighter.setDocument(None)
            # attach live highlighter
            self.live_highlighter = LivePreviewHighlighter(self.editor.document())
            self._on_cursor_pos_changed()
        else:
            # detach live and restore normal highlighter
            if self.live_highlighter:
                self.live_highlighter.setDocument(None)
                self.live_highlighter = None
            self.highlighter.setDocument(self.editor.document())
            self.highlighter.rehighlight()

    def _on_cursor_pos_changed(self):
        if not self.live_highlighter:
            return
        cursor = self.editor.textCursor()
        pos = cursor.position()
        blocknum = cursor.blockNumber()
        self.live_highlighter.setCaretPosition(pos)
        # Rehighlight current and previous block to show/hide markers correctly
        doc = self.editor.document()
        if self._inline_prev_blocknum >= 0 and self._inline_prev_blocknum != blocknum:
            prev_block = doc.findBlockByNumber(self._inline_prev_blocknum)
            if prev_block.isValid():
                self.live_highlighter.rehighlightBlock(prev_block)
        cur_block = cursor.block()
        if cur_block.isValid():
            self.live_highlighter.rehighlightBlock(cur_block)
        self._inline_prev_blocknum = blocknum

    def on_toggle_highlight(self, enabled: bool):
        if enabled:
            self.highlighter.setDocument(self.editor.document())
            self.highlighter.rehighlight()
        else:
            self.highlighter.setDocument(None)

    def on_editor_changed(self):
        self.update_status()
        # If in preview mode, keep it in sync
        if self.stack.currentIndex() == 1:
            self.update_preview()

    # File ops
    def on_new(self):
        if not self.maybe_save():
            return
        self.editor.clear()
        self.current_file = None
        self.update_window_title()

    def on_open(self):
        if not self.workspace:
            QMessageBox.information(self, "Ingen arbetsyta", "Öppna först en arbetsyta (mapp).")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Öppna fil", str(self.workspace), "Text/Markdown (*.md *.markdown *.txt);;Alla filer (*.*)"
        )
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        self.editor.setPlainText(normalize_newlines(text))
        self.current_file = Path(path)
        self.update_window_title()
        self.update_status()
        if self.stack.currentIndex() == 1:
            self.update_preview()

    def on_open_workspace(self):
        d = QFileDialog.getExistingDirectory(self, "Välj arbetsyta (mapp)")
        if not d:
            return
        self.load_workspace(Path(d))

    def load_workspace(self, path: Path):
        self.workspace = path
        self.settings.setValue("workspace", str(path))
        self.status.showMessage(f"Arbetsyta: {path}", 5000)
        try:
            self.repo.open(path)
        except GitError:
            pass
        self.update_status()

    def on_save(self):
        if not self.current_file:
            return self.on_save_as()
        self._save_to_path(self.current_file)

    def on_save_as(self):
        if not self.workspace:
            QMessageBox.information(self, "Ingen arbetsyta", "Öppna först en arbetsyta (mapp).")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Spara som", str(self.workspace / "untitled.md"), "Markdown (*.md);;Text (*.txt);;Alla filer (*.*)"
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
            self, "Exportera som PDF", str(self.workspace or Path.cwd() / "document.pdf"), "PDF (*.pdf)"
        )
        if not path:
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)
        html = self.render_markdown(self.editor.toPlainText())
        doc = QTextDocument()
        doc.setHtml(html)
        doc.print(printer)
        self.status.showMessage(f"PDF exporterad: {path}", 5000)

    # Tools
    def on_find(self):
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

    # Git
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
        if not self.workspace:
            QMessageBox.information(self, "Git", "Spara i en arbetsyta först.")
            return
        if self.editor.document().isModified():
            self.on_save()
        text = self.editor.toPlainText()
        ids = detect_srs_ids(text, SRS_ID_REGEX)
        default_msg = ids[0] + " – uppdaterad kravspec" if ids else "Uppdaterad kravspec"
        dlg = CommitDialog(default_msg, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        msg = dlg.values()
        try:
            if not self.repo.is_open():
                self.repo.open(self.workspace)
            self.repo.commit(paths=None, message=msg)
            QMessageBox.information(self, "Git", "Commit klar.")
        except GitError as e:
            QMessageBox.critical(self, "Git-fel", str(e))
        self.update_status()

    def on_git_branch_create(self):
        if not self.repo.is_open():
            QMessageBox.information(self, "Git", "Initiera/Öppna repo först.")
            return
        name, ok = QInputDialog.getText(self, "Ny branch", "Branch-namn:")
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
            QMessageBox.information(self, "Git", "Initiera/Öppna repo först.")
            return
        branches = self.repo.list_branches()
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
            QMessageBox.information(self, "Git", "Initiera/Öppna repo först.")
            return
        try:
            out = self.repo.pull()
            QMessageBox.information(self, "Git Pull", out or "OK")
        except GitError as e:
            QMessageBox.critical(self, "Git-fel", str(e))

    def on_git_push(self):
        if not self.repo.is_open():
            QMessageBox.information(self, "Git", "Initiera/Öppna repo först.")
            return
        try:
            out = self.repo.push()
            QMessageBox.information(self, "Git Push", out or "OK")
        except GitError as e:
            QMessageBox.critical(self, "Git-fel", str(e))

    def maybe_save(self) -> bool:
        if not self.editor.document().isModified():
            return True
        ret = QMessageBox.question(
            self,
            "Spara ändringar?",
            "Dokumentet har ändringar. Vill du spara?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
        )
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
        self.setWindowTitle(f"{APP_NAME} – {fn}{branch}")

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


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName(ORG)
    app.setApplicationName(APP_NAME)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
