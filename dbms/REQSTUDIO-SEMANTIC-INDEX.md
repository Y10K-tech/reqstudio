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

- A **PostgreSQL schema** (with `pgvector`) to store commits, documents, SRS items, links, baselines, and **embeddings**.
- An **Indexer** (Python CLI) that ingests changed files from Git, extracts metadata/links, computes embeddings, and upserts into Postgres.
- A small **HTTP API service** (FastAPI) exposing endpoints for search, suggestions, matrices, and baseline operations.
- Minimal **GUI integration** hooks in ReqStudio (PyQt6) to call the API and show results.
- **Docker Compose** for local dev (Postgres+pgvector + API), plus `Makefile` tasks.
- **Tests** (unit & integration), **observability**, and **docs**.

---

## 2. Definitions & Assumptions

- **SRS-ID format:** `Y10K-{PROJ}-{AREA}-{TYPE}-{NNN}` with `TYPE ∈ {HL,LL,CMP,API,DB,TST}` and `NNN ∈ 001..999`.
- **Documents:** Markdown/Text files in a Git repo (workspaces). Optional YAML front-matter for metadata (`id`, `title`, `version`, `status`, `owner`, `links`).
- **Embedding model:** `google/embeddinggemma-300m` (Sentence-Transformers). Vectors **768-d**, plus **Matryoshka** truncation to **256-d** for fast ANN. Requires accepting the Gemma terms on first download.
- **pgvector:** cosine similarity using `<=>` operator. Index type IVFFlat or HNSW depending on version.
- **Derived DB:** Postgres is **rebuildable** from Git (no unique business data lives only in DB).

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
  repo_id      BIGINT NOT NULL REFERENCES repo(id),
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
- Scan **changed files only** since last known commit (or a `--since` ref).
- Parse front-matter + extract **SRS-IDs** and **[[SRS-ID]]** links.
- Upsert commits, documents, doc revisions, items, links.
- Compute embeddings for each **srs_item** text (title + local context/body).
- Upsert embeddings (768-d + 256-d slice, normalized cosine).

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
- Model: `google/embeddinggemma-300m` via `sentence-transformers`.
- Prompts:
  - Document: `title: {title} | text: {text}`
  - Query: `task: search result | query: {q}`
- Compute 768-d vectors; also store 256-d **prefix slice** (Matryoshka). Normalize both.

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
- `GET /health` → `{status:"ok"}`
- `POST /search` → body `{q:string, k:int=20, dim:768|256}` → returns list `[ {srs_id,title,similarity,doc_path} ]`
- `POST /hybrid_search` → `{q, k=20, alpha=0.7}` → combines vector + FTS
- `POST /suggest_links` → `{srs_id, k=10}` → suggests target SRS-IDs (CMP/ADR prioritized)
- `GET /matrix` → returns traceability matrix (req ↔ components ↔ tests) for a repo or subset
- `POST /baseline/create` → `{name}` → record signed tag + freeze items
- `GET /baseline/compare?from=...&to=...` → changed/added/removed SRS-IDs

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

- Add **Search panel**: sends `/search` or `/hybrid_search` requests; shows results, double-click opens file.
- Add **Link Suggestions** popup: for current SRS-ID, call `/suggest_links` and insert `[[Y10K-...]]` into the doc.
- Add **Baseline** menu: call `/baseline/create` and `/baseline/compare` (show report).

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
- Provide a `Makefile`: `make up`, `make down`, `make migrate`, `make seed`.

### 8.2 Migrations
- Keep SQL files in `db/migrations/*.sql` and an `apply.py` that runs them in order (or use Alembic).

---

## 9. Security & Privacy

- **No secrets** in documents to be embedded; mask prior to indexing.
- DB creds via env vars; consider TLS if remote.
- Optional: **git notes** store approvals; API allows read-only of approvals.
- No telemetry by default; logs local only.

---

## 10. Observability

- FastAPI with Prometheus metrics (latencies, QPS, DB times).
- Structured logs with request IDs.
- Optional OpenTelemetry traces (client span from ReqStudio through API and DB).

---

## 11. Performance Targets

- Indexer: 1,000 files (avg 1KB each) embeds in **<60s** on CPU; batch size 32.
- Search: vector-only **P95 < 150ms** for k=20 locally (ANN index warmed).
- Hybrid search overhead **< 50ms** over vector-only.
- DB size: embeddings (768-d float32) ~ 3KB each; plan disk accordingly.

---

## 12. Testing

### 12.1 Unit
- Parser finds all valid SRS-IDs and no false positives for provided fixtures.
- Embedding wrapper returns normalized vectors; 256-d is a prefix slice.
- SQL builders parameterize correctly; no SQL injection path.

### 12.2 Integration
- Spin up Docker Compose; run **indexer** on a sample repo with HL/LL/CMP docs.
- Verify rows in `commit`, `document`, `doc_revision`, `srs_item`, `srs_link`, `srs_item_embedding`.
- `/search` returns items with relevance > 0.5 for matching queries.
- `/suggest_links` returns CMP items for a LL change.

### 12.3 E2E (Optional)
- In ReqStudio, edit doc → save → commit → run indexer → search & link from GUI.

---

## 13. Rollout Plan

- Phase 1 (MVP): schema + indexer + `/search`, `/suggest_links` + GUI search.
- Phase 2: baselines, hybrid search, matrix endpoint.
- Phase 3: approvals mirror (git notes), impact analysis view, polished UI states.

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
- [ ] Create `db/migrations/0001_init.sql` with tables above.
- [ ] Add migration runner (`apply.py`) or Alembic setup.
- [ ] Verify pgvector extension loads in CI and local Docker.

### Indexer
- [ ] Implement `reqstudio_indexer` package (scan/parse/embed/db).
- [ ] Implement `scan`, `full`, `embed` CLI commands.
- [ ] Compute 768-d + 256-d normalized vectors.
- [ ] Upsert logic idempotent per `(document, commit)`.
- [ ] Unit tests for parser & embedder.
- [ ] Integration test against Docker Postgres.

### API
- [ ] FastAPI project scaffolding with `/health`, `/search`, `/hybrid_search`, `/suggest_links`.
- [ ] Connection pool to Postgres; parameterized SQL.
- [ ] Pagination & limits.
- [ ] Basic metrics and structured logging.
- [ ] Integration tests (testclient + Docker DB).

### GUI Integration
- [ ] Add Search panel in ReqStudio (PyQt6).
- [ ] Add Link Suggestions (context menu / button).
- [ ] Config panel for API URL.
- [ ] Graceful error states (API down).

### DevOps
- [ ] Docker Compose for DB + API.
- [ ] `Makefile` tasks (`up`, `down`, `migrate`, `seed`).
- [ ] GitHub Actions: run unit/integration tests with services.

### Performance
- [ ] Measure indexer throughput on CPU (≥ 16 docs/s target).
- [ ] P95 latency checks for `/search` < 150ms locally.
- [ ] Tune ANN indexes (`lists`, `HNSW`) if needed.

### Docs
- [ ] README section for “Semantic Indexing” with setup steps.
- [ ] API reference (OpenAPI auto-generated).
- [ ] Example repo with sample HL/LL/CMP docs.

---

## 16. Risks & Mitigations

- **Model download/licensing:** Document one-time HF login/terms. Mirror in internal cache if needed.
- **Large repos:** Batch indexing and resume; consider pygit2 for speed.
- **Inconsistent IDs:** Add a validator step; surface errors in GUI.
- **PII in embeddings:** Add masking; optional denylist patterns.

---

## 17. Acceptance Criteria (DoD)

- [ ] Given a repo with 30+ SRS docs, running `reqstudio-index scan` fills all core tables.
- [ ] `/search?q=<known term>` returns the expected item top-3.
- [ ] `/suggest_links?srs_id=<LL>` returns at least one CMP suggestion with sim > 0.6.
- [ ] Baseline creation stores a row and resolves items to `baseline_item`.
- [ ] ReqStudio GUI can search and insert a suggested link with two clicks.
- [ ] All unit/integration tests pass in CI on Linux/macOS/Windows.
- [ ] No secrets or telemetry enabled by default; logs are local and structured.
