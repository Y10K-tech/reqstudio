from __future__ import annotations

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles


def _project_root() -> Path:
    # api/ is one level below project root
    return Path(__file__).resolve().parent.parent


ROOT = _project_root()
DOCS_DIR = ROOT / "docs"
MEDIA_DIR = ROOT / "media"
DOCS_SITE_DIR = DOCS_DIR / "site"

app = FastAPI(title="ReqStudio Docs Server", version="0.1.0")


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/")
def root():
    # Serve the docs under /docs to keep API routes at root clean
    return RedirectResponse(url="/docs/")


# Static mounts
if DOCS_DIR.exists():
    app.mount(
        "/docs",
        StaticFiles(directory=str(DOCS_DIR), html=True),
        name="docs",
    )

if MEDIA_DIR.exists():
    app.mount(
        "/media",
        StaticFiles(directory=str(MEDIA_DIR), html=False),
        name="media",
    )

# Optional: static multipage build at /docs-site
if DOCS_SITE_DIR.exists():
    app.mount(
        "/docs-site",
        StaticFiles(directory=str(DOCS_SITE_DIR), html=True),
        name="docs-site",
    )


def main():
    # Allow: python -m api.docs_server
    import uvicorn

    host = os.environ.get("DOCS_HOST", "127.0.0.1")
    # Use a non-default port to avoid collisions with any primary API service
    port = int(os.environ.get("DOCS_PORT", "8808"))
    uvicorn.run("api.docs_server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
