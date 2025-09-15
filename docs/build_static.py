"""
Build static multi-page docs into docs/site/ using existing content in docs/pages/.

Usage:
  python docs/build_static.py

Outputs:
  docs/site/*.html and docs/site/media/* (logo)
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PAGES_DIR = ROOT / "pages"
SITE_DIR = ROOT / "site"
MEDIA_SRC = ROOT.parent / "media"
MEDIA_DST = SITE_DIR / "media"


@dataclass
class Item:
    id: str
    title: str


NAV: list[tuple[str, list[Item]]] = [
    (
        "Getting Started",
        [
            Item("overview", "Overview"),
            Item("install", "Install"),
            Item("getting-started", "Quickstart"),
            Item("ui", "UI Guide"),
        ],
    ),
    (
        "Core Concepts",
        [
            Item("srs-ids", "SRS IDs"),
            Item("templates", "Templates"),
            Item("git", "Git Integration"),
            Item("export", "Export (PDF)"),
            Item("configuration", "Configuration"),
        ],
    ),
    (
        "Interfaces",
        [
            Item("cli", "CLI"),
            Item("api", "API & MCP"),
            Item("docs-server", "Docs Server"),
        ],
    ),
    (
        "Architecture",
        [
            Item("architecture", "System Overview"),
            Item("app", "App (PyQt6)"),
            Item("core", "Core Package"),
            Item("core-git-backend", "Git Backend"),
            Item("core-highlighter", "Markdown Highlighter"),
            Item("core-templates", "Template Library"),
            Item("core-utils", "Utilities"),
            Item("dbms", "DBMS (future)"),
        ],
    ),
    (
        "Project",
        [
            Item("roadmap", "Roadmap"),
            Item("troubleshooting", "Troubleshooting"),
            Item("faq", "FAQ"),
            Item("contributing", "Contributing"),
            Item("changelog", "Changelog"),
            Item("license", "License"),
            Item("glossary", "Glossary"),
            Item("docs-static", "Docs Static Build"),
        ],
    ),
]


def read_page_html(page_id: str) -> str:
    path = PAGES_DIR / f"{page_id}.html"
    if not path.exists():
        raise FileNotFoundError(f"Missing page: {path}")
    return path.read_text(encoding="utf-8")


def sidebar_html(active_id: str) -> str:
    parts: list[str] = []
    for section_title, items in NAV:
        parts.append('<div class="nav-section">')
        parts.append(f'<div class="nav-title">{section_title}</div>')
        parts.append('<ul class="nav-list">')
        for item in items:
            cls = "active" if item.id == active_id else ""
            parts.append(
                f'<li class="nav-item"><a class="{cls}" href="{item.id}.html">{item.title}</a></li>'
            )
        parts.append("</ul>")
        parts.append("</div>")
    return "".join(parts)


def page_frame(title: str, body_html: str, active_id: str) -> str:
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{title} — ReqStudio Docs</title>
  <link rel=\"icon\" href=\"media/reqstudio_logo.png\" />
  <link rel=\"stylesheet\" href=\"../styles.css\" />
</head>
<body>
  <header class=\"topbar\">
    <div class=\"brand\"> <img src=\"media/reqstudio_logo.png\" alt=\"ReqStudio\" /> <span>ReqStudio Documentation</span></div>
  </header>
  <div class=\"layout\">
    <aside class=\"sidebar\">{sidebar_html(active_id)}</aside>
    <main class=\"content\">
      <article class=\"doc\">{body_html}</article>
      <footer class=\"footer\"><div>Static build</div><div><a href=\"changelog.html\">Changelog</a> · <a href=\"license.html\">License</a></div></footer>
    </main>
  </div>
</body>
</html>"""


def copy_media():
    MEDIA_DST.mkdir(parents=True, exist_ok=True)
    logo = MEDIA_SRC / "reqstudio_logo.png"
    if logo.exists():
        shutil.copy2(logo, MEDIA_DST / logo.name)


def build():
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    copy_media()
    # Generate a page for every nav item
    for _, items in NAV:
        for item in items:
            html = read_page_html(item.id)
            title = item.title
            out = page_frame(title, html, item.id)
            (SITE_DIR / f"{item.id}.html").write_text(out, encoding="utf-8")
    # Index: point to overview
    index = page_frame("Overview", read_page_html("overview"), "overview")
    (SITE_DIR / "index.html").write_text(index, encoding="utf-8")
    print(f"Built static docs to: {SITE_DIR}")


if __name__ == "__main__":
    build()

