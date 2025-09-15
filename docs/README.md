# ReqStudio Documentation

Extensive, offline-first documentation for Y10K ReqStudio. The docs ship in two forms:

- Single‑page app (SPA) with client-side routing and search under `docs/`.
- Classic static multi‑page site generated into `docs/site/`.

This README explains how to view, develop, and extend the docs.


## Contents

- Overview
- Directory layout
- Quickstart: view the docs
- Local docs server (FastAPI)
- Build the static site
- Authoring pages
- Navigation and search
- Styling and theming
- Deploying docs
- Maintenance tips
- Roadmap for docs


## Overview

The docs are intentionally framework‑free (vanilla HTML/CSS/JS) for simplicity and portability. The SPA provides quick navigation and search without a build step. A small Python builder also emits a traditional multi‑page site for environments that prefer standalone HTML files.


## Directory Layout

```
/docs
  index.html          # SPA entrypoint (hash routing)
  styles.css          # Global styles and CSS variables
  app.js              # SPA router, sidebar, and search
  README.md           # This file
  build_static.py     # Build script for classic multi‑page site
  /pages              # Page content (HTML fragments with <h1>...)
    overview.html
    install.html
    getting-started.html
    ui.html
    srs-ids.html
    templates.html
    git.html
    export.html
    configuration.html
    cli.html
    api.html
    docs-server.html
    architecture.html
    app.html
    core.html
    core-git-backend.html
    core-highlighter.html
    core-templates.html
    core-utils.html
    dbms.html
    roadmap.html
    troubleshooting.html
    faq.html
    contributing.html
    changelog.html
    license.html
    glossary.html
    docs-static.html
  /site               # Output of build_static.py (generated)
```

Related folders:

- `/media` — shared assets (e.g., `reqstudio_logo.png`).
- `/api/docs_server.py` — FastAPI server for local/offline hosting.


## Quickstart: View the Docs

Open the SPA directly in a browser (no server required):

- File URL: open `docs/index.html` in your browser.

Features available:

- Sidebar with sections and active highlighting
- Hash-based routing (`#/overview`, `#/ui`, etc.)
- Client-side search (Ctrl+/ to focus). Title + excerpt preview
- Remembers last visited page per browser


## Local Docs Server (FastAPI)

Install via `pyproject.toml` (from project root):

```
python -m venv .venv
. .venv/bin/activate                 # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install .
# Optional (if defined): python -m pip install .[dev]
```

Run the server:

```
python -m api.docs_server
# or
uvicorn api.docs_server:app --host 127.0.0.1 --port 8000
```

Endpoints:

- `/` → redirects to `/docs/`
- `/docs/` → serves the SPA
- `/docs-site/` → serves the generated static site (if built)
- `/media/` → serves the repo’s media assets
- `/healthz` → health check JSON

Config via environment variables:

- `DOCS_HOST` (default `127.0.0.1`)
- `DOCS_PORT` (default `8000`)


## Build the Static Site

Generate a traditional multi‑page site to `docs/site/`:

```
python docs/build_static.py
```

Open locally (no server needed):

- Open `docs/site/index.html` in a browser.
- Or serve via the docs server at `/docs-site/`.

The builder copies required media to `docs/site/media/`.


## Authoring Pages

Pages live in `docs/pages/` as small HTML fragments:

- Start each file with a single `<h1>` — it becomes the page title.
- Use plain semantic HTML (`<h2>`, `<p>`, `<ul>`, `<pre><code>…</code></pre>`) for content.
- Keep pages focused and scannable; prefer multiple short sections.

Linking:

- SPA links: use `#page-id` (e.g., `<a href="#ui">UI</a>`).
- Static site links: use relative `.html` (e.g., `<a href="ui.html">UI</a>`). The builder fixes the sidebar; inline links you add should use `.html` for static pages or `#...` for SPA depending on context.

Adding a new page:

1) Create `docs/pages/<id>.html` with a top-level `<h1>`.
2) Add the page to navigation:
   - SPA: update the `NAV` array in `docs/app.js`.
   - Static site: update `NAV` in `docs/build_static.py`.
3) If serving via FastAPI, no changes required; it serves from `docs/` or `docs/site/` automatically.

Note: The SPA and static builder each contain a `NAV` definition. Keep them in sync when adding or reordering pages. If you prefer a single source of truth later, we can refactor to load `NAV` from a shared JSON file.


## Navigation and Search

- Navigation: grouped by sections in the sidebar; the active page is highlighted.
- Routing: SPA uses hash routing (no server rewrite rules required).
- Search: client-side fuzzy match across page titles and text content.
  - Shortcut: `Ctrl+/` focuses the search box.
  - Results: shows up to 20 matches with excerpt; Enter navigates to the top match.


## Styling and Theming

Global styles live in `docs/styles.css` with CSS variables:

- Colors: `--bg`, `--fg`, `--muted`, `--accent`, etc.
- Layout: responsive grid with a sticky header.
- Components: sidebar, content area, code blocks, tables, search dropdown.

To customize:

- Tweak CSS variables for brand colors.
- Add print styles for export-friendly pages (roadmap).
- Add an optional dark mode by toggling a class on `<body>` and providing `@media (prefers-color-scheme: dark)` overrides.


## Deploying Docs

Options:

- Host the SPA: serve `docs/` via any static web server.
- Host the static site: run the builder and deploy `docs/site/` (fully standalone HTML files).
- GitHub Pages: configure Pages to serve from `/docs/site` and commit the generated output.
- Internal portals: mount either output under a reverse proxy (Nginx/Apache) or behind VPN.


## Maintenance Tips

- Keep SPA `NAV` and static builder `NAV` aligned.
- Prefer small, well-named pages to keep search useful and quick.
- Reuse phrasing from the main `README.md`, but avoid duplication by linking.
- When code changes, update corresponding pages under `Architecture` and `Core`.


## Roadmap for Docs

- Dark mode and print styles
- Server-side search index for large docs sets (optional)
- Breadcrumbs and prev/next links
- Shared `nav.json` to drive both SPA and static builder
- Automated site build in CI


---

For issues or proposals, open a ticket and mention “docs”. Contributions welcome — see `docs/pages/contributing.html`.
