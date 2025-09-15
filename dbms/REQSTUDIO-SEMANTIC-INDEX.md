# Y10K-REQ-EMB-LL-001 — ReqStudio Semantic Indexing & Traceability (Git + Postgres + pgvector + EmbeddingGemma)

**Version:** v1.0
**Owner:** Y10K Software Engineering
**Date:** 2025-09-15
**Status:** Draft (intended for direct handoff to an AI coding agent)

---

## 0. Objective

Build a **semantic indexing & traceability layer** for ReqStudio that keeps **Git** as the source of truth for requirement documents (Markdown), while **PostgreSQL + pgvector** provides fast query capabilities (semantic search, link suggestions, duplicate detection, impact analysis). Use **`google/embeddinggemma-300m`** as the embedding model.

**Non-goal:** Forking Git or changing its storage model. This is an additive subsystem.

---

## 1. Deliverables (High-Level)

* A **PostgreSQL schema** (with `pgvector`) to store commits, documents, SRS items, links, baselines, and **embeddings**.
* An **Indexer** (Python CLI) that ingests changed files from Git, extracts metadata/links, computes embeddings, and upserts into Postgres.
* A small **HTTP API service** (FastAPI) exposing endpoints for search, suggestions, matrices, and baseline operations.
* Minimal **GUI integration** hooks in ReqStudio (PyQt6) to call the API and show results.
* **Docker Compose** for local dev (Postgres+pgvector + API), plus `Makefile` tasks.
* **Tests** (unit & integration), **observability**, and **docs**.

---

## 2. Definitions & Assumptions

* **SRS-ID format:** `{COMPANY}-{PROJ}-{AREA}-{TYPE}-{NNN}` with `TYPE ∈ {HL,LL,CMP,API,DB,TST}` and `NNN ∈ 001..999`.
* **Documents:** Markdown/Text files in a Git repo (workspaces). Optional YAML front-matter for metadata (`id`, `title`, `version`, `status`, `owner`, `links`).
* **Embedding model:** `google/embeddinggemma-300m` (Sentence-Transformers). Vectors **768-d**, plus **Matryoshka** truncation to **256-d** for fast ANN. Requires accepting the Gemma terms on first download.
* **pgvector:** cosine similarity using `<=>` operator. Index type IVFFlat or HNSW depending on version.
* **Derived DB:** Postgres is **rebuildable** from Git (no unique business data lives only in DB).

---

## 3. Architecture Overview

```
+----------------------+        +-----------------+
|      ReqStudio       |        |   Git Repo(s)   |
|  (PyQt6 GUI Client)  |        |  (source of     |
|   - Edit/Commit      |        |   truth)        |
|   - Search panel ----+------> |  .md/.txt docs  |
|   - Link suggest     |        +-----------------+
+----------+-----------+
           |
           | HTTP (localhost or remote)
           v
+----------------------+     Git scan       +---------------------+
|  FastAPI Service     | <----------------- |  Indexer CLI        |
|  /search, /suggest   |  Embeddings push   |  (Python)           |
|  /matrix, /baseline  | -----------------> |  - parse docs       |
+-----------+----------+                     |  - embeddings       |
            |                                 |  - upsert Postgres  |
            v                                 +----------+----------+
+------------------------------+                         |
|  PostgreSQL + pgvector       | <----------------------+
|  - commits/doc revisions     |
|  - srs_item, links           |
|  - embeddings (768/256)      |
|  - baselines/approvals       |
+------------------------------+
```

---

## 4. Data Model (Postgres)

> Create in `db/migrations/0001_init.sql`. Use `CREATE EXTENSION IF NOT EXISTS vector;` before tables.

```sql
-- Extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS vector;

-- Repos (tracked workspaces)
CREATE TABLE repo (
  id              BIGSERIAL PRIMARY KEY,
  name            TEXT NOT NULL,
  root_path       TEXT NOT NULL,
  default_branch  TEXT NOT NULL DEFAULT 'main',
  UNIQUE(root_path)
);

-- Commits
CREATE TABLE commit (
  sha          CHAR(40) PRIMARY KEY,
  repo_id      BIGINT NOT NULL REFERENCES repo(id),
  author_name  TEXT,
  author_email TEXT,
  authored_at  TIMESTAMPTZ,
  message      TEXT,
  branch       TEXT
);

-- Documents (by path)
CREATE TABLE document (
  id           BIGSERIAL PRIMARY KEY,
  repo_id      BIGINT NOT NULL REFERENCES document(id),
  rel_path     TEXT NOT NULL,
  kind         TEXT CHECK (kind IN ('HL','LL','CMP','ADR','API','DB','TST','OTHER')) DEFAULT 'OTHER',
  UNIQUE (repo_id, rel_path)
);

-- Snapshot at a commit
CREATE TABLE doc_revision (
  id           BIGSERIAL PRIMARY KEY,
  document_id  BIGINT NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  commit_sha   CHAR(40) NOT NULL REFERENCES commit(sha) ON DELETE CASCADE,
  size_bytes   INT,
  content_hash TEXT,
  content_text TEXT
);
CREATE UNIQUE INDEX docrev_uniq ON doc_revision(document_id, commit_sha);

-- Parsed items
CREATE TABLE srs_item (
  id           BIGSERIAL PRIMARY KEY,
  srs_id       TEXT NOT NULL,
  type         TEXT NOT NULL,
  title        TEXT,
  status       TEXT,
  version      TEXT,
  owner        TEXT,
  document_id  BIGINT NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  docrev_id    BIGINT NOT NULL REFERENCES doc_revision(id) ON DELETE CASCADE,
  commit_sha   CHAR(40) NOT NULL REFERENCES commit(sha) ON DELETE CASCADE,
  line_start   INT,
  line_end     INT,
  meta         JSONB DEFAULT '{}'::jsonb
);
CREATE INDEX ON srs_item(srs_id);
CREATE INDEX ON srs_item(type);
CREATE INDEX srs_item_fts_idx ON srs_item USING GIN (to_tsvector('simple', coalesce(title,'') || ' ' || coalesce(meta::text,'')));

-- Links between items
CREATE TABLE srs_link (
  from_item_id BIGINT REFERENCES srs_item(id) ON DELETE CASCADE,
  to_srs_id    TEXT NOT NULL,
  link_type    TEXT DEFAULT 'ref',  -- ref/implements/tests/depends/blocks
  commit_sha   CHAR(40) NOT NULL REFERENCES commit(sha) ON DELETE CASCADE,
  PRIMARY KEY (from_item_id, to_srs_id, link_type)
);
CREATE INDEX ON srs_link(to_srs_id);

-- Baselines
CREATE TABLE baseline (
  id           BIGSERIAL PRIMARY KEY,
  repo_id      BIGINT NOT NULL REFERENCES repo(id) ON DELETE CASCADE,
  name         TEXT NOT NULL,
  tag_ref      TEXT NOT NULL,
  commit_sha   CHAR(40) NOT NULL REFERENCES commit(sha) ON DELETE CASCADE,
  created_at   TIMESTAMPTZ DEFAULT now(),
  UNIQUE(repo_id, name)
);

CREATE TABLE baseline_item (
  baseline_id  BIGINT REFERENCES baseline(id) ON DELETE CASCADE,
  srs_id       TEXT NOT NULL,
  docrev_id    BIGINT REFERENCES doc_revision(id) ON DELETE RESTRICT,
  commit_sha   CHAR(40) NOT NULL,
  PRIMARY KEY (baseline_id, srs_id)
);

-- Embeddings
CREATE TABLE srs_item_embedding (
  srs_item_id   BIGINT PRIMARY KEY REFERENCES srs_item(id) ON DELETE CASCADE,
  commit_sha    CHAR(40) NOT NULL REFERENCES commit(sha) ON DELETE CASCADE,
  dim           INT NOT NULL CHECK (dim IN (768,256)),
  embedding     vector(768),
  embedding256  vector(256)
);
-- ANN indexes
CREATE INDEX srs_item_emb_768_ivf ON srs_item_embedding USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX srs_item_emb_256_ivf ON srs_item_embedding USING ivfflat (embedding256 vector_cosine_ops) WITH (lists = 100);
```

**Note:** Switch to HNSW if your pgvector build supports it; parameterize `lists/efConstruction` in a later migration.

---

## 5. Indexer CLI (Python)

### 5.1 Package layout

```
/indexer
  reqstudio_indexer/
    __init__.py
    cli.py
    git_scan.py
    parse.py
    embed.py
    db.py
  pyproject.toml
```

### 5.2 Behavior

* Scan **changed files only** since last known commit (or a `--since` ref).
* Parse front-matter + extract **SRS-IDs** and **\[\[SRS-ID]]** links.
* Upsert commits, documents, doc revisions, items, links.
* Compute embeddings for each **srs\_item** text (title + local context/body).
* Upsert embeddings (768-d + 256-d slice, normalized cosine).

### 5.3 Commands

```bash
# index current repo (auto-detect) into $DATABASE_URL
reqstudio-index scan --repo . --since HEAD~100

# reindex entire repo (slow path)
reqstudio-index full --repo .

# backfill embeddings only
reqstudio-index embed --repo . --batch 32
```

### 5.4 Embedding policy

* Model: `google/embeddinggemma-300m` via `sentence-transformers`.
* Prompts:

  * Document: `title: {title} | text: {text}`
  * Query: `task: search result | query: {q}`
* Compute 768-d vectors; also store 256-d **prefix slice** (Matryoshka). Normalize both.

### 5.5 Pseudocode (core)

```python
# parse.py
SRS_RX = r"\bY10K-[A-Z0-9]+-[A-Z0-9]+-(HL|LL|CMP|API|DB|TST)-\d{3}\b"

def parse_items(text:str):
    # find SRS-IDs, infer titles (first heading below), capture line ranges
    ...

def parse_links(text:str):
    # [[Y10K-...]] wiki-style links
    ...

# embed.py
from sentence_transformers import SentenceTransformer
import numpy as np
model = SentenceTransformer("google/embeddinggemma-300m")

def embed_doc(title, body):
    s = f"title: {title or 'none'} | text: {body or ''}"
    v = model.encode_document([s], convert_to_numpy=True, normalize_embeddings=True)[0]
    v256 = v[:256]; v256 = v256 / np.linalg.norm(v256)
    return v.astype(np.float32), v256.astype(np.float32)
```

---

## 6. FastAPI Service

### 6.1 Endpoints

* `GET /health` → `{status:"ok"}`
* `POST /search` → body `{q:string, k:int=20, dim:768|256}` → returns list `[ {srs_id,title,similarity,doc_path} ]`
* `POST /hybrid_search` → `{q, k=20, alpha=0.7}` → combines vector + FTS
* `POST /suggest_links` → `{srs_id, k=10}` → suggests target SRS-IDs (CMP/ADR prioritized)
* `GET /matrix` → returns traceability matrix (req ↔ components ↔ tests) for a repo or subset
* `POST /baseline/create` → `{name}` → record signed tag + freeze items
* `GET /baseline/compare?from=...&to=...` → changed/added/removed SRS-IDs

### 6.2 Query SQL (examples)

```sql
-- vector-only search
SELECT si.srs_id, si.title, d.rel_path,
       (1 - (e.embedding <=> $1)) AS sim
FROM srs_item si
JOIN srs_item_embedding e ON e.srs_item_id = si.id
JOIN document d ON d.id = si.document_id
ORDER BY e.embedding <=> $1
LIMIT $2;
```

```sql
-- hybrid
WITH f AS (
  SELECT id, ts_rank(to_tsvector('simple', coalesce(title,'') || ' ' || meta::text), plainto_tsquery('simple', $q)) AS ts
  FROM srs_item
)
SELECT si.srs_id, si.title, d.rel_path,
       ( $alpha * (1 - (e.embedding <=> $v)) + (1-$alpha) * COALESCE(f.ts,0) ) AS score
FROM srs_item si
JOIN srs_item_embedding e ON e.srs_item_id = si.id
LEFT JOIN f ON f.id = si.id
JOIN document d ON d.id = si.document_id
ORDER BY score DESC
LIMIT $k;
```

---

## 7. GUI (ReqStudio) — Minimal Integration

* Add **Search panel**: sends `/search` or `/hybrid_search` requests; shows results, double-click opens file.
* Add **Link Suggestions** popup: for current SRS-ID, call `/suggest_links` and insert `[[Y10K-...]]` into the doc.
* Add **Baseline** menu: call `/baseline/create` and `/baseline/compare` (show report).

---

## 8. DevOps & Local Run

### 8.1 Docker Compose (`infra/compose.yml`)

```yaml
version: "3.9"
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_PASSWORD: reqstudio
      POSTGRES_USER: reqstudio
      POSTGRES_DB: reqstudio
    ports: ["5432:5432"]
    healthcheck: { test: ["CMD-SHELL","pg_isready -U reqstudio"], interval: 5s, timeout: 5s, retries: 20 }

  api:
    build: ./api
    environment:
      DATABASE_URL: postgresql://reqstudio:reqstudio@db:5432/reqstudio
    depends_on: [db]
    ports: ["8000:8000"]
```

* Provide a `Makefile`: `make up`, `make down`, `make migrate`, `make seed`.

### 8.2 Migrations

* Keep SQL files in `db/migrations/*.sql` and an `apply.py` that runs them in order (or use Alembic).

---

## 9. Security & Privacy

* **No secrets** in documents to be embedded; mask prior to indexing.
* DB creds via env vars; consider TLS if remote.
* Optional: **git notes** store approvals; API allows read-only of approvals.
* No telemetry by default; logs local only.

---

## 10. Observability

* FastAPI with Prometheus metrics (latencies, QPS, DB times).
* Structured logs with request IDs.
* Optional OpenTelemetry traces (client span from ReqStudio through API and DB).

---

## 11. Performance Targets

* Indexer: 1,000 files (avg 1KB each) embeds in **<60s** on CPU; batch size 32.
* Search: vector-only **P95 < 150ms** for k=20 locally (ANN index warmed).
* Hybrid search overhead **< 50ms** over vector-only.
* DB size: embeddings (768-d float32) \~ 3KB each; plan disk accordingly.

---

## 12. Testing

### 12.1 Unit

* Parser finds all valid SRS-IDs and no false positives for provided fixtures.
* Embedding wrapper returns normalized vectors; 256-d is a prefix slice.
* SQL builders parameterize correctly; no SQL injection path.

### 12.2 Integration

* Spin up Docker Compose; run **indexer** on a sample repo with HL/LL/CMP docs.
* Verify rows in `commit`, `document`, `doc_revision`, `srs_item`, `srs_link`, `srs_item_embedding`.
* `/search` returns items with relevance > 0.5 for matching queries.
* `/suggest_links` returns CMP items for a LL change.

### 12.3 E2E (Optional)

* In ReqStudio, edit doc → save → commit → run indexer → search & link from GUI.

---

## 13. Rollout Plan

* Phase 1 (MVP): schema + indexer + `/search`, `/suggest_links` + GUI search.
* Phase 2: baselines, hybrid search, matrix endpoint.
* Phase 3: approvals mirror (git notes), impact analysis view, polished UI states.

---

## 14. API Shapes (JSON)

```http
POST /search
{
  "q": "rate limit tokens",
  "k": 20,
  "dim": 768
}
-> 200 OK
[
  {"srs_id":"Y10K-ACME-AUTH-LL-003","title":"Login flow","similarity":0.78,"path":"docs/srs/ll/auth.md"},
  ...
]
```

```http
POST /suggest_links
{
  "srs_id": "Y10K-ACME-AUTH-LL-003",
  "k": 10
}
-> 200 OK
{
  "candidates": [
    {"srs_id":"Y10K-ACME-AUTH-CMP-012","title":"Token Service","similarity":0.81},
    ...
  ]
}
```

---

## 15. Checklist (Markdown checkboxes)

### Schema & Migrations

* [ ] Create `db/migrations/0001_init.sql` with tables above.
* [ ] Add migration runner (`apply.py`) or Alembic setup.
* [ ] Verify pgvector extension loads in CI and local Docker.

### Indexer

* [ ] Implement `reqstudio_indexer` package (scan/parse/embed/db).
* [ ] Implement `scan`, `full`, `embed` CLI commands.
* [ ] Compute 768-d + 256-d normalized vectors.
* [ ] Upsert logic idempotent per `(document, commit)`.
* [ ] Unit tests for parser & embedder.
* [ ] Integration test against Docker Postgres.

### API

* [ ] FastAPI project scaffolding with `/health`, `/search`, `/hybrid_search`, `/suggest_links`.
* [ ] Connection pool to Postgres; parameterized SQL.
* [ ] Pagination & limits.
* [ ] Basic metrics and structured logging.
* [ ] Integration tests (testclient + Docker DB).

### GUI Integration

* [ ] Add Search panel in ReqStudio (PyQt6).
* [ ] Add Link Suggestions (context menu / button).
* [ ] Config panel for API URL.
* [ ] Graceful error states (API down).

### DevOps

* [ ] Docker Compose for DB + API.
* [ ] `Makefile` tasks (`up`, `down`, `migrate`, `seed`).
* [ ] GitHub Actions: run unit/integration tests with services.

### Performance

* [ ] Measure indexer throughput on CPU (≥ 16 docs/s target).
* [ ] P95 latency checks for `/search` < 150ms locally.
* [ ] Tune ANN indexes (`lists`, `HNSW`) if needed.

### Docs

* [ ] README section for “Semantic Indexing” with setup steps.
* [ ] API reference (OpenAPI auto-generated).
* [ ] Example repo with sample HL/LL/CMP docs.

---

## 16. Risks & Mitigations

* **Model download/licensing:** Document one-time HF login/terms. Mirror in internal cache if needed.
* **Large repos:** Batch indexing and resume; consider pygit2 for speed.
* **Inconsistent IDs:** Add a validator step; surface errors in GUI.
* **PII in embeddings:** Add masking; optional denylist patterns.

---

## 17. Libraries that could be useful together with pyqt6 to make it look better, modern sleek and sexy (avoid using libraries that may class state)

Full themes & component kits

QFluentWidgets (Fluent/Windows 11 look) — a full widget set (nav bars, cards, acrylic, dialogs) with light/dark and accent colors. PyQt6 builds are available; it also has Designer integration.
[https://pyqt-fluent-widgets.readthedocs.io](https://pyqt-fluent-widgets.readthedocs.io)

Install: pip install PyQt6-Fluent-Widgets

Qt-Material (Material Design look) — stylesheet-based theming for PyQt6/PySide6; includes dark/light, custom accents, and runtime switching. Because it’s just QSS + assets, it layers well over your widgets.
[https://pypi.org/project/qt-material/](https://pypi.org/project/qt-material/)

Install: pip install qt-material

QDarkStyle / PyQtDarkTheme (clean dark/light themes) — drop-in themes that work across PyQt6/PySide6. Great when you want a neutral modern base instead of a full design language.
[https://pyqtdarktheme.readthedocs.io](https://pyqtdarktheme.readthedocs.io)
[https://pypi.org/project/QDarkStyle/](https://pypi.org/project/QDarkStyle/)
[https://github.com/pythonguis/pyqtdarktheme](https://github.com/pythonguis/pyqtdarktheme)

Install: pip install QDarkStyle pyqtdarktheme

Icons, extra widgets, and window chrome

QtAwesome (Font Awesome icons in Qt) — consistent, vector icons you can color/stack programmatically. Works with PyQt6.
[https://github.com/spyder-ide/qtawesome](https://github.com/spyder-ide/qtawesome)

Install: pip install qtawesome

superqt (“missing” widgets) — high-quality community widgets (spinners, range sliders, validators, etc.) tested on PyQt6.
[https://github.com/pyvista/superqt](https://github.com/pyvista/superqt)

Install: pip install superqt

PyQt6-Frameless-Window — polished, cross-platform frameless windows with shadows, drag/resize, Mica/Acrylic‐style effects on Windows. Plays well with the theming libs above.
[https://pypi.org/project/PyQt6-Frameless-Window/](https://pypi.org/project/PyQt6-Frameless-Window/)

Install: pip install PyQt6-Frameless-Window

Charts/visuals that match modern styling

PyQtGraph — fast, interactive plotting (2D/3D) that supports PyQt6; easy to theme so it matches your app.
[https://www.pyqtgraph.org](https://www.pyqtgraph.org)

## Install: pip install pyqtgraph

## 18. Reqstudio Nodes: Visualizing Functional Requirements and Component Connections

The **Reqstudio Nodes** view provides an interactive, graphical interface for visualizing the relationships between functional requirements and their corresponding system components. This module enables users to intuitively explore and comprehend the traceability and dependency structures within a given requirement specification document.

Reqstudio Nodes are accessed through a dedicated page view within the application's GUI. While this view occupies a distinct space in the interface, it remains integrated within the main window of the application—no separate window is launched. A page selector interface, located on the left side of the GUI, allows users to switch seamlessly between standard views (e.g., requirement lists, documentation) and the Reqstudio Nodes visualization.

### Features

* **Interactive Graph Visualization**
  Nodes represent individual functional requirements and components. Connections (edges) illustrate traceability, dependencies, or implementation mappings between these entities.

* **Dynamic Exploration**
  Users can expand or collapse nodes, highlight paths, or filter based on tags, categories, or status, enabling focused analysis of specific requirement chains.

* **Scalable and Responsive UI**
  The graph adapts to varying levels of complexity, ensuring performance and clarity across small and large specification documents.

* **Contextual Metadata Display**
  Clicking or hovering on a node reveals detailed metadata, such as descriptions, linked documents, status indicators, and assigned stakeholders.

This feature is critical for system engineers, analysts, and developers who require a clear and immediate understanding of how functional requirements map to implementation components.

---

## 19. Acceptance Criteria (DoD) — UPDATED

### 19.1 Schema & Migrations

* [ ] Running `make migrate` creates **all** objects from §4 without error on a clean Postgres 16 + pgvector image.
* [ ] All tables have the indexes/constraints specified (including GIN/IVF indexes) and appear in `pg_indexes`.
* [ ] Dropping the DB and reapplying migrations yields the **same schema** (hash of `pg_dump --schema-only` unchanged).

### 19.2 Indexer Correctness & Idempotency

* [ ] On a repo with ≥30 SRS docs, `reqstudio-index scan --since HEAD~100` populates `commit`, `document`, `doc_revision`, `srs_item`, `srs_link`, and `srs_item_embedding` with non-zero counts.
* [ ] Re-running the identical scan produces **no duplicate** logical rows (idempotent upsert semantics verified by stable counts and spot checks).
* [ ] Indexer only touches rows for files actually changed (verified by modifying 1 file and observing ≤3 affected rows across core tables).

### 19.3 Embeddings & Search Quality

* [ ] Stored vectors are **unit-normalized**; `||v|| = 1.0 ± 1e-5` for both 768-d and 256-d slices (sample ≥100 rows).
* [ ] For a labeled sample set (≥30 query→target pairs), **vector search** returns the correct target in **top‑3** for ≥80% of queries.
* [ ] **Hybrid search** (α=0.7) improves or matches vector-only **NDCG\@10** on the same sample set.

### 19.4 Performance (Local Dev Baseline)

* [ ] Vector-only `/search` with k=20 has **p95 < 150 ms** over 200 requests with warm indexes.
* [ ] Hybrid search adds **< 50 ms** overhead (same workload, same box).
* [ ] Indexer throughput **≥ 16 docs/s** on CPU for 1KB average docs (batch=32).

### 19.5 API Behavior & Safety

* [ ] All endpoints in §6 return **HTTP 2xx/4xx/5xx** appropriately, with structured JSON errors and no stack traces in responses.
* [ ] Inputs are validated (types/ranges); SQL execution uses bound parameters only (static analysis confirms no string‑built SQL).
* [ ] Pagination is supported on list endpoints; limits default to ≤50 and cap at 200.

### 19.6 Baselines

* [ ] `POST /baseline/create {name}` inserts a baseline row and resolves **all** current SRS items to `baseline_item`.
* [ ] `GET /baseline/compare?from=&to=` reports **added/changed/removed** SRS‑IDs correctly for a known synthetic change set.
* [ ] Baseline operation is **deterministic**: rebuilding DB from Git and re-running baseline creation yields identical manifests (hash match).

### 19.7 Traceability Matrix & Links

* [ ] `/matrix` returns, for a seeded sample, the expected requirement→component→test groupings.
* [ ] Editing a requirement and rescanning marks downstream links as **suspect** (visible via API) until re‑verified.

### 19.8 GUI Integration (PyQt6)

* [ ] User can search, select a result, and open the underlying doc within **two clicks** from the search panel.
* [ ] **Link Suggestions** action inserts an `[[SRS-ID]]` token at the cursor position for the current doc.
* [ ] When API is unreachable, GUI shows a non-blocking error banner and the editor remains usable.

### 19.9 Reproducibility

* [ ] Dropping the DB and running `reqstudio-index full` against the same Git revision reproduces identical row counts and **stable content hashes** for `doc_revision.content_text`.

### 19.10 Security & Privacy

* [ ] Embedding pipeline excludes lines matching a configurable deny‑list (e.g., secrets/PII patterns); sample redaction test passes.
* [ ] No credentials are written to logs; logs redact tokens and connection strings.

### 19.11 Observability

* [ ] `/health` returns `{"status":"ok"}`.
* [ ] Prometheus metrics expose request counts, latencies (p50/p95), and DB timings for `/search`, `/hybrid_search`, `/suggest_links`.

### 19.12 Cross‑Platform

* [ ] CI proves green on Linux, macOS, and Windows (indexer + API unit/integration suites).

### 19.13 Reqstudio Nodes (Graph View)

* [ ] For a project with ≥200 items and ≥400 links, the Nodes view renders in **< 1.5 s** and remains interactive (pan/zoom/select) with **p95 frame time < 20 ms**.
* [ ] Clicking a node highlights its immediate neighbors and displays metadata panel (title, type, status, path).

---
