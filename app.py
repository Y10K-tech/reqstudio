import sys
from pathlib import Path
import difflib

from PyQt6.QtCore import Qt, QSettings, QSaveFile, QTimer, QStandardPaths
from PyQt6.QtGui import QAction, QFont, QTextCursor, QTextDocument, QIcon
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
    QSplitter,
    QDockWidget,
    QColorDialog,
)
from PyQt6.QtPrintSupport import QPrinter

from core.git_backend import GitFacade, GitError
from core.highlighter import MarkdownHighlighter, LivePreviewHighlighter
from core.renderer import render_markdown_html, pygments_css
from core.ui.search import SearchDock
from core.ui.theme import apply_theme
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

        # App icon
        icon_path = str(Path("media") / "reqstudio_logo.png")
        if Path(icon_path).exists():
            self.setWindowIcon(QIcon(icon_path))

        # Source editor
        self.editor = QTextEdit()
        font = QFont("Consolas")
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        font.setPointSize(11)
        self.editor.setFont(font)
        self.highlighter = MarkdownHighlighter(self.editor.document(), SRS_ID_REGEX)

        # Rendered preview (side-by-side when enabled)
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setAcceptRichText(True)

        # Central splitter for side-by-side edit/preview
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        self.preview.setVisible(False)
        self.setCentralWidget(self.splitter)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self.current_file: Path | None = None
        self.workspace: Path | None = None
        self.repo = GitFacade()

        self._md_css_light = """
        body { font-family: system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif; font-size: 14px; color: #222; }
        h1,h2,h3,h4,h5,h6 { color: #111; }
        h1 { font-size: 1.8em; margin: 0.8em 0 0.4em; }
        h2 { font-size: 1.6em; margin: 0.8em 0 0.4em; }
        h3 { font-size: 1.4em; margin: 0.8em 0 0.4em; }
        h4 { font-size: 1.2em; margin: 0.8em 0 0.4em; }
        h5 { font-size: 1.1em; margin: 0.8em 0 0.4em; }
        h6 { font-size: 1.0em; margin: 0.8em 0 0.4em; }
        a { color: #DB89C8; text-decoration: none; }
        a:hover { text-decoration: underline; }
        p { margin: 0.4em 0 0.8em; }
        ul, ol { margin: 0.4em 0 0.8em 1.4em; }
        code { background: #f5f5f5; padding: 0 3px; border-radius: 3px; }
        pre { background: #f5f5f5; padding: 8px; border-radius: 4px; overflow-x: auto; }
        table { border-collapse: collapse; margin: 0.8em 0; }
        th, td { border: 1px solid #ddd; padding: 6px 10px; }
        th { background: #fafafa; }
        blockquote { border-left: 3px solid #ccc; margin: 0.8em 0; padding: 0.2em 0 0.2em 0.8em; color: #555; }
        hr { border: none; border-top: 1px solid #ddd; margin: 1em 0; }
        """.strip()

        self._md_css_dark = """
        body { font-family: system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif; font-size: 14px; color: #eaeaea; background: transparent; }
        h1,h2,h3,h4,h5,h6 { color: #fafafa; }
        h1 { font-size: 1.8em; margin: 0.8em 0 0.4em; }
        h2 { font-size: 1.6em; margin: 0.8em 0 0.4em; }
        h3 { font-size: 1.4em; margin: 0.8em 0 0.4em; }
        h4 { font-size: 1.2em; margin: 0.8em 0 0.4em; }
        h5 { font-size: 1.1em; margin: 0.8em 0 0.4em; }
        h6 { font-size: 1.0em; margin: 0.8em 0 0.4em; }
        a { color: #DB89C8; text-decoration: none; }
        a:hover { text-decoration: underline; }
        p { margin: 0.4em 0 0.8em; }
        ul, ol { margin: 0.4em 0 0.8em 1.4em; }
        code { background: #2a2a2a; color: #f0f0f0; padding: 0 3px; border-radius: 3px; }
        pre { background: #2a2a2a; color: #f0f0f0; padding: 8px; border-radius: 4px; overflow-x: auto; }
        table { border-collapse: collapse; margin: 0.8em 0; }
        th, td { border: 1px solid #444; padding: 6px 10px; }
        th { background: #2a2a2a; }
        tr:nth-child(even) td { background: #1d1d1d; }
        blockquote { border-left: 3px solid #444; margin: 0.8em 0; padding: 0.2em 0 0.2em 0.8em; color: #cfcfcf; }
        hr { border: none; border-top: 1px solid #444; margin: 1em 0; }
        """.strip()

        self._md_css_current = self._md_css_dark if getattr(self, "dark_theme", False) else self._md_css_light
        self._pyg_css_current = pygments_css(getattr(self, "dark_theme", False))

        # Accent color (WORKPLAN): RGB(219,137,200)
        self.accent_css = "#DB89C8"
        # Apply saved theme (default light)
        mode = self.settings.value("theme_mode", "light")
        if mode == "system":
            self._apply_system_theme()
        elif (self.settings.value("theme", "light") or "light") == "dark":
            self.dark_theme = True
            apply_theme(self, True, self.accent_css)
        else:
            self.dark_theme = False
            apply_theme(self, False, self.accent_css)

        self._make_actions()
        self._make_menus()
        self._make_toolbar()
        self._wire_signals()

        last_ws = self.settings.value("workspace", "")
        if last_ws and Path(last_ws).exists():
            self.load_workspace(Path(last_ws))

        self.update_status()
        # Search dock (pave for semantic index API)
        self.search_dock = SearchDock(parent=self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.search_dock)
        self.search_dock.searchRequested.connect(self.on_search_requested)

        # Editor context menu with formatting actions
        self.editor.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.editor.customContextMenuRequested.connect(self.on_context_menu)

        # Auto-save timer
        self.autosave_path = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation) or ".") / "reqstudio_autosave.md"
        self.autosave_path.parent.mkdir(parents=True, exist_ok=True)
        self.autosave = QTimer(self)
        self.autosave.setInterval(15000)
        self.autosave.timeout.connect(self._on_autosave)
        self.autosave.start()
        self._maybe_restore_autosave()

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

        self.act_split_view = QAction("Split View (Preview)", self)
        self.act_split_view.setCheckable(True)
        self.act_split_view.setChecked(False)

        self.act_theme_light = QAction("Light Theme", self)
        self.act_theme_light.setCheckable(True)
        self.act_theme_dark = QAction("Dark Theme", self)
        self.act_theme_dark.setCheckable(True)
        self.act_theme_light.setChecked(True)

        self.act_set_api_url = QAction("Set Semantic API URL…", self)

        # Formatting actions
        self.act_bold = QAction("Bold", self)
        self.act_bold.setShortcut("Ctrl+B")
        self.act_italic = QAction("Italic", self)
        self.act_italic.setShortcut("Ctrl+I")
        # Headings H1..H6
        self.act_h1 = QAction("Heading 1", self); self.act_h1.setShortcut("Ctrl+1")
        self.act_h2 = QAction("Heading 2", self); self.act_h2.setShortcut("Ctrl+2")
        self.act_h3 = QAction("Heading 3", self); self.act_h3.setShortcut("Ctrl+3")
        self.act_h4 = QAction("Heading 4", self); self.act_h4.setShortcut("Ctrl+4")
        self.act_h5 = QAction("Heading 5", self); self.act_h5.setShortcut("Ctrl+5")
        self.act_h6 = QAction("Heading 6", self); self.act_h6.setShortcut("Ctrl+6")
        # Lists / quote / code / link / image
        self.act_ulist = QAction("Unordered List", self); self.act_ulist.setShortcut("Ctrl+Shift+U")
        self.act_olist = QAction("Ordered List", self); self.act_olist.setShortcut("Ctrl+Shift+O")
        self.act_check = QAction("Checklist Item", self); self.act_check.setShortcut("Ctrl+Shift+C")
        self.act_quote = QAction("Blockquote", self); self.act_quote.setShortcut("Ctrl+Shift+Q")
        self.act_codeblock = QAction("Code Block", self); self.act_codeblock.setShortcut("Ctrl+Shift+K")
        self.act_link = QAction("Insert Link", self); self.act_link.setShortcut("Ctrl+K")
        self.act_image = QAction("Insert Image", self); self.act_image.setShortcut("Ctrl+Shift+I")

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
        self.act_replace = QAction("Find & Replace…", self)
        self.act_replace.setShortcut("Ctrl+H")
        m_edit.addAction(self.act_replace)

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
        m_tools.addAction(self.act_split_view)
        m_tools.addAction(self.act_toggle_md)
        m_tools.addSeparator()
        m_tools.addAction(self.act_set_api_url)

        m_color = self.menuBar().addMenu("&Colorize")
        self.act_color_pick = QAction("Pick Color…", self)
        self.act_color_pick.triggered.connect(self.on_colorize_pick)
        m_color.addAction(self.act_color_pick)
        m_color.addSeparator()
        # Presets
        presets = [
            ("Accent", self.accent_css),
            ("Red", "#e53935"),
            ("Orange", "#fb8c00"),
            ("Yellow", "#fdd835"),
            ("Green", "#43a047"),
            ("Blue", "#1e88e5"),
            ("Purple", "#8e24aa"),
        ]
        self.color_presets: list[QAction] = []
        for name, hexv in presets:
            act = QAction(f"{name}", self)
            act.triggered.connect(lambda checked=False, hv=hexv: self.on_colorize_apply(hv))
            m_color.addAction(act)
            self.color_presets.append(act)
        # Highlight submenu
        m_high = m_color.addMenu("Highlight")
        self.act_high_pick = QAction("Pick Highlight…", self)
        self.act_high_pick.triggered.connect(self.on_highlight_pick)
        m_high.addAction(self.act_high_pick)
        m_high.addSeparator()
        hl_presets = [
            ("Yellow", "#fff59d"),
            ("Green", "#a5d6a7"),
            ("Blue", "#90caf9"),
            ("Pink", "#f8bbd0"),
        ]
        for name, hv in hl_presets:
            act = QAction(name, self)
            act.triggered.connect(lambda checked=False, col=hv: self.on_highlight_apply(col))
            m_high.addAction(act)

        m_view = self.menuBar().addMenu("&Visa")
        m_view.addAction(self.act_theme_light)
        m_view.addAction(self.act_theme_dark)
        self.act_theme_system = QAction("Follow System Theme", self)
        self.act_theme_system.setCheckable(True)
        self.act_theme_system.setChecked(self.settings.value("theme_mode", "light") == "system")
        m_view.addAction(self.act_theme_system)

        m_help = self.menuBar().addMenu("&Hjälp")
        self.act_about = QAction("About ReqStudio", self)
        m_help.addAction(self.act_about)

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
        # Formatting toolbar group
        tb.addSeparator()
        for a in [self.act_bold, self.act_italic, self.act_h1, self.act_h2, self.act_h3, self.act_ulist, self.act_olist, self.act_quote]:
            tb.addAction(a)

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
        self.act_replace.triggered.connect(self.on_replace_dialog)
        self.editor.cursorPositionChanged.connect(self.update_status)

        # Inline live state
        self.live_highlighter = None
        self._inline_prev_blocknum = -1

        self.act_split_view.toggled.connect(self.on_toggle_split_view)
        self.act_theme_light.triggered.connect(self.on_theme_light)
        self.act_theme_dark.triggered.connect(self.on_theme_dark)
        self.act_theme_system.triggered.connect(self.on_theme_system)
        self.act_about.triggered.connect(self.on_about)
        self.act_set_api_url.triggered.connect(self.on_set_api_url)
        # Formatting signals
        self.act_bold.triggered.connect(self.on_bold)
        self.act_italic.triggered.connect(self.on_italic)
        self.act_h1.triggered.connect(lambda: self.on_heading(1))
        self.act_h2.triggered.connect(lambda: self.on_heading(2))
        self.act_h3.triggered.connect(lambda: self.on_heading(3))
        self.act_h4.triggered.connect(lambda: self.on_heading(4))
        self.act_h5.triggered.connect(lambda: self.on_heading(5))
        self.act_h6.triggered.connect(lambda: self.on_heading(6))
        self.act_ulist.triggered.connect(self.on_ulist)
        self.act_olist.triggered.connect(self.on_olist)
        self.act_check.triggered.connect(self.on_check)
        self.act_quote.triggered.connect(self.on_quote)
        self.act_codeblock.triggered.connect(self.on_codeblock)
        self.act_link.triggered.connect(self.on_link)
        self.act_image.triggered.connect(self.on_image)

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
        css = self._md_css_current + "\n" + (self._pyg_css_current or "")
        html = render_markdown_html(self.editor.toPlainText(), css)
        self.preview.setHtml(html)

    def on_toggle_preview_mode(self, enabled: bool):
        # When enabled, switch to rendered preview; when disabled, return to source editor
        if enabled:
            self.update_preview()
            # Full preview replaces editor in splitter (hide editor)
            self.editor.setVisible(False)
            self.preview.setVisible(True)
        else:
            self.editor.setVisible(True)
            if not self.act_split_view.isChecked():
                self.preview.setVisible(False)

    def on_toggle_inline_live(self, enabled: bool):
        # Inline live is mutually exclusive with full preview; ensure editor is visible
        if enabled:
            if self.act_live_preview.isChecked():
                self.act_live_preview.setChecked(False)
            self.editor.setVisible(True)
            if not self.act_split_view.isChecked():
                self.preview.setVisible(False)
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

    def on_toggle_split_view(self, enabled: bool):
        # Show both panes side-by-side; disable full preview mode
        if self.act_live_preview.isChecked():
            self.act_live_preview.setChecked(False)
        self.preview.setVisible(enabled)
        if enabled:
            self.update_preview()

    def on_toggle_highlight(self, enabled: bool):
        if enabled:
            self.highlighter.setDocument(self.editor.document())
            self.highlighter.rehighlight()
        else:
            self.highlighter.setDocument(None)

    def on_editor_changed(self):
        self.update_status()
        # If in preview mode, keep it in sync
        if self.act_live_preview.isChecked() or self.act_split_view.isChecked():
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
        if self.act_live_preview.isChecked() or self.act_split_view.isChecked():
            self.update_preview()

    # Drag & Drop open files
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return
        path = urls[0].toLocalFile()
        if not path:
            return
        # Open first file
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            self.editor.setPlainText(normalize_newlines(text))
            self.current_file = Path(path)
            self.update_window_title()
            self.update_status()
            if self.act_live_preview.isChecked() or self.act_split_view.isChecked():
                self.update_preview()
        except Exception as e:
            QMessageBox.critical(self, "Open", f"Failed to open file: {e}")

    def _on_autosave(self):
        try:
            if not self.editor.document().isModified():
                return
            text = self.editor.toPlainText()
            with open(self.autosave_path, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception:
            pass

    def _maybe_restore_autosave(self):
        try:
            if self.autosave_path.exists() and self.autosave_path.stat().st_size > 0:
                ret = QMessageBox.question(self, "Restore unsaved work", "An autosave was found. Restore it?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if ret == QMessageBox.StandardButton.Yes:
                    with open(self.autosave_path, "r", encoding="utf-8") as f:
                        self.editor.setPlainText(f.read())
                    self.update_status()
        except Exception:
            pass

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
        css = self._md_css_current + "\n" + (self._pyg_css_current or "")
        html = render_markdown_html(self.editor.toPlainText(), css)
        doc = QTextDocument()
        doc.setHtml(html)
        doc.print(printer)
        self.status.showMessage(f"PDF exporterad: {path}", 5000)

    def on_search_requested(self, q: str):
        # Placeholder: pave the way for semantic API integration
        lines = []
        if q:
            lines.append(f"Search placeholder for: {q}")
            api_url = self.settings.value("api_url", "") or "(not configured)"
            lines.append(f"API: {api_url}")
        self.search_dock.setResults(lines)

    def on_set_api_url(self):
        url, ok = QInputDialog.getText(self, "Semantic API", "Base URL (e.g., http://localhost:8000):",
                                       text=self.settings.value("api_url", ""))
        if ok:
            self.settings.setValue("api_url", url.strip())
            self.status.showMessage("Semantic API URL saved", 3000)

    # Formatting helpers
    def on_context_menu(self, pos):
        menu = self.editor.createStandardContextMenu()
        menu.addSeparator()
        menu.addAction(self.act_bold)
        menu.addAction(self.act_italic)
        menu.addSeparator()
        for a in [self.act_h1, self.act_h2, self.act_h3, self.act_h4, self.act_h5, self.act_h6]:
            menu.addAction(a)
        menu.addSeparator()
        for a in [self.act_ulist, self.act_olist, self.act_check, self.act_quote, self.act_codeblock, self.act_link, self.act_image]:
            menu.addAction(a)
        menu.addSeparator()
        menu.addAction(self.act_color_pick)
        menu.exec(self.editor.mapToGlobal(pos))

    def on_bold(self):
        self._wrap_selection("**")

    def on_italic(self):
        self._wrap_selection("*")

    def _wrap_selection(self, marker: str):
        c = self.editor.textCursor()
        if not c.hasSelection():
            return
        sel = c.selectedText()
        # Replace unicode line separators with newlines in selection
        sel = sel.replace('\u2029', '\n')
        c.insertText(f"{marker}{sel}{marker}")

    # Colorize helpers
    def on_colorize_pick(self):
        col = QColorDialog.getColor()
        if not col.isValid():
            return
        self.on_colorize_apply(col.name())

    def on_colorize_apply(self, color_hex: str):
        c = self.editor.textCursor()
        if not c.hasSelection():
            return
        sel = c.selectedText().replace('\u2029', '\n')
        c.insertText(f"{{color:{color_hex}}}{sel}{{/color}}")

    def on_highlight_pick(self):
        col = QColorDialog.getColor()
        if not col.isValid():
            return
        self.on_highlight_apply(col.name())

    def on_highlight_apply(self, color_hex: str):
        c = self.editor.textCursor()
        if not c.hasSelection():
            return
        sel = c.selectedText().replace('\u2029', '\n')
        c.insertText(f"{{highlight:{color_hex}}}{sel}{{/highlight}}")

    def on_heading(self, level: int):
        c = self.editor.textCursor()
        block = c.block()
        text = block.text()
        hashes = '#' * max(1, min(6, level))
        # Normalize: remove existing heading markers, then apply desired level
        import re
        m = re.match(r"^(\s{0,3})(#{1,6})(\s?|\s+)(.*)$", text)
        content = text
        indent = ''
        if m:
            indent = m.group(1)
            content = m.group(4)
        content = content.lstrip()
        new_line = f"{indent}{hashes} {content}" if content else f"{indent}{hashes} "
        # Replace current block text
        doc = self.editor.document()
        bc = QTextCursor(doc)
        bc.setPosition(block.position())
        bc.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        bc.insertText(new_line)

    def on_ulist(self):
        self._toggle_prefix("- ")

    def on_olist(self):
        c = self.editor.textCursor()
        block = c.block()
        text = block.text()
        import re
        if re.match(r"^\s*\d+[\.)]\s+", text):
            # remove ordered marker
            new = re.sub(r"^(\s*)\d+[\.)]\s+", r"\1", text)
        else:
            # add '1. '
            new = re.sub(r"^(\s*)", r"\1", text)
            new = f"{new if new != text else text}"  # keep
            new = f"1. {text.lstrip()}" if text.strip() else "1. "
        self._replace_block_text(block, new)

    def on_check(self):
        import re
        c = self.editor.textCursor()
        block = c.block()
        text = block.text()
        if re.match(r"^\s*- \[( |x)\] ", text):
            # toggle off checklist
            new = re.sub(r"^(\s*)- \[( |x)\] ", r"\1", text)
        else:
            new = re.sub(r"^(\s*)", r"\1", text)
            new = f"- [ ] {text.lstrip()}" if text.strip() else "- [ ] "
        self._replace_block_text(block, new)

    def on_quote(self):
        self._toggle_prefix("> ")

    def on_codeblock(self):
        c = self.editor.textCursor()
        if c.hasSelection():
            sel = c.selectedText().replace('\u2029', '\n')
            c.insertText(f"```\n{sel}\n```\n")
        else:
            c.insertText("```\n\n```\n")

    def on_link(self):
        from PyQt6.QtWidgets import QInputDialog
        url, ok = QInputDialog.getText(self, "Insert Link", "URL:")
        if not ok or not url:
            return
        c = self.editor.textCursor()
        if c.hasSelection():
            txt = c.selectedText().replace('\u2029', ' ')
        else:
            txt = "link"
        c.insertText(f"[{txt}]({url})")

    def on_image(self):
        from PyQt6.QtWidgets import QInputDialog
        url, ok = QInputDialog.getText(self, "Insert Image", "Image URL:")
        if not ok or not url:
            return
        alt, ok = QInputDialog.getText(self, "Insert Image", "Alt text:")
        if not ok:
            alt = ""
        c = self.editor.textCursor()
        c.insertText(f"![{alt}]({url})")

    def _toggle_prefix(self, prefix: str):
        import re
        c = self.editor.textCursor()
        block = c.block()
        text = block.text()
        if text.lstrip().startswith(prefix.strip()):
            # remove
            pattern = r"^(\s*)" + re.escape(prefix)
            new = re.sub(pattern, r"\1", text)
        else:
            new = re.sub(r"^(\s*)", r"\1", text)
            new = f"{prefix}{text.lstrip()}" if text.strip() else prefix
        self._replace_block_text(block, new)

    def _replace_block_text(self, block, new_text: str):
        doc = self.editor.document()
        bc = QTextCursor(doc)
        bc.setPosition(block.position())
        bc.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        bc.insertText(new_text)

    # Themes
    def on_theme_light(self):
        apply_theme(self, False, self.accent_css)
        self.dark_theme = False
        self.settings.setValue("theme_mode", "light")
        self.act_theme_light.setChecked(True)
        self.act_theme_dark.setChecked(False)
        self.act_theme_system.setChecked(False)
        self.settings.setValue("theme", "light")
        self._md_css_current = self._md_css_light
        self._pyg_css_current = pygments_css(False)
        if self.preview.isVisible():
            self.update_preview()

    def on_theme_dark(self):
        apply_theme(self, True, self.accent_css)
        self.dark_theme = True
        self.settings.setValue("theme_mode", "dark")
        self.act_theme_light.setChecked(False)
        self.act_theme_dark.setChecked(True)
        self.act_theme_system.setChecked(False)
        self.settings.setValue("theme", "dark")
        self._md_css_current = self._md_css_dark
        self._pyg_css_current = pygments_css(True)
        if self.preview.isVisible():
            self.update_preview()

    def on_theme_system(self):
        self.settings.setValue("theme_mode", "system")
        self.act_theme_system.setChecked(True)
        # Uncheck explicit modes
        self.act_theme_light.setChecked(False)
        self.act_theme_dark.setChecked(False)
        self._apply_system_theme()
        if self.preview.isVisible():
            self.update_preview()

    def _apply_system_theme(self):
        # Simple detection based on palette lightness
        pal = self.palette()
        base = pal.window().color()
        # luminance
        lum = 0.2126 * base.redF() + 0.7152 * base.greenF() + 0.0722 * base.blueF()
        dark = lum < 0.5
        self.dark_theme = dark
        apply_theme(self, dark, self.accent_css)
        self._md_css_current = self._md_css_dark if dark else self._md_css_light
        self._pyg_css_current = pygments_css(dark)

    # About dialog with logo + animation
    def on_about(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
        from PyQt6.QtGui import QMovie
        dlg = QDialog(self)
        dlg.setWindowTitle("About ReqStudio")
        v = QVBoxLayout(dlg)
        lab_logo = QLabel()
        p = Path("media") / "reqstudio_logo.png"
        if p.exists():
            lab_logo.setPixmap(QIcon(str(p)).pixmap(120,120))
        v.addWidget(lab_logo)
        lab_gif = QLabel()
        gif_path = Path("media") / "feather-pen.gif"
        if gif_path.exists():
            mv = QMovie(str(gif_path))
            lab_gif.setMovie(mv)
            mv.start()
            v.addWidget(lab_gif)
        lab_txt = QLabel("Y10K ReqStudio — Modern Markdown Editor")
        v.addWidget(lab_txt)
        dlg.resize(300, 280)
        dlg.exec()

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

    def on_replace_dialog(self):
        dlg = FindReplaceDialog(self.editor, self)
        dlg.resize(420, 180)
        dlg.exec()

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
        c = self.editor.textCursor()
        pos = f"L{c.blockNumber()+1}:C{c.positionInBlock()+1}"
        mode = "FullPreview" if self.act_live_preview.isChecked() else ("Split" if self.act_split_view.isChecked() else "Edit")
        self.status.showMessage(f"WS: {ws} | Fil: {cur} | Branch: {branch} | Pos: {pos} | Mode: {mode} | SRS-ID: {srs_show}")


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName(ORG)
    app.setApplicationName(APP_NAME)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
