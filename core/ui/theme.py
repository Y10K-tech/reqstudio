from __future__ import annotations

def build_css(dark: bool, accent: str) -> str:
    if not dark:
        return f"""
        QWidget {{ font-size: 13px; }}
        QToolBar {{ background: #fafafa; border-bottom: 1px solid #e5e5e5; }}
        QPushButton {{ padding: 6px 10px; border-radius: 6px; background: {accent}; color: #111; }}
        /* No CSS filter in Qt stylesheets; use subtle background change via palette instead */
        QLineEdit {{ padding: 6px 8px; border: 1px solid #ddd; border-radius: 6px; }}
        QTextEdit {{ border: none; }}
        QStatusBar {{ background: #ffffff; border-top: 1px solid #e5e5e5; }}
        """
    else:
        return f"""
        QWidget {{ font-size: 13px; color: #e6e6e6; }}
        QMainWindow {{ background: #1f1f1f; }}

        /* Menubar and menus */
        QMenuBar {{ background: #2a2a2a; color: #eaeaea; border-bottom: 1px solid #333; }}
        QMenuBar::item {{ background: transparent; color: #eaeaea; padding: 4px 8px; }}
        QMenuBar::item:selected {{ background: #3a3a3a; color: #ffffff; border-radius: 4px; }}
        QMenu {{ background: #2a2a2a; color: #eaeaea; border: 1px solid #333; }}
        QMenu::item:selected {{ background: #3a3a3a; color: #ffffff; }}

        /* Toolbars and toolbuttons */
        QToolBar {{ background: #2a2a2a; border-bottom: 1px solid #333; }}
        QToolBar QToolButton {{ color: #eaeaea; padding: 6px 8px; }}
        QToolBar QToolButton::hover {{ background: #333333; border-radius: 4px; }}

        /* Common controls */
        QLabel {{ color: #eaeaea; }}
        QLineEdit {{ padding: 6px 8px; border: 1px solid #444; border-radius: 6px; background: #1c1c1c; color: #eeeeee; }}
        QTextEdit {{ border: none; background: #202020; color: #eaeaea; }}
        QPlainTextEdit {{ border: none; background: #202020; color: #eaeaea; }}
        QStatusBar {{ background: #1b1b1b; border-top: 1px solid #333; color: #e0e0e0; }}
        QDockWidget::title {{ background: #2a2a2a; color: #eaeaea; padding: 4px; }}

        /* Buttons */
        QPushButton {{ padding: 6px 10px; border-radius: 6px; background: {accent}; color: #111; }}
        QPushButton:disabled {{ background: #555; color: #222; }}
        """


def apply_theme(window, dark: bool, accent: str) -> None:
    window.setStyleSheet(build_css(dark, accent))
