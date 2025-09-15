# Docker — Docs Server

This Docker setup serves the ReqStudio documentation (SPA and static build, if present) via FastAPI.

Ports:

- 8808/tcp — Docs Server (default); override with `-p` in `docker run` or compose.

Build and run:

```
# From repo root
docker build -f install/docker/Dockerfile -t reqstudio-docs .
docker run --rm -p 8808:8808 reqstudio-docs

# Open
# http://127.0.0.1:8808/docs/
# http://127.0.0.1:8808/docs-site/   (if you built docs/site)
```

Compose:

```
docker compose -f install/docker/docker-compose.yml up --build
```

Notes:

- The image does not install PyQt6 or the desktop app dependencies — it only serves documentation.
- To update the docs, rebuild the image after changes.
