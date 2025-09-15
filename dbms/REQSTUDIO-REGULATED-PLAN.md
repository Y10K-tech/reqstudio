# Y10K-REQ-EMB-LL-002 — Regulated-Grade Extensions for ReqStudio (Automotive, Defense, Medical, Gov)

**Version:** v1.0  
**Owner:** Y10K Software Engineering  
**Date:** 2025-09-15  
**Status:** Draft — *handoff-ready for an AI coding agent*  
**Depends on:** `Y10K-REQ-EMB-LL-001 — Semantic Indexing & Traceability` (baseline search/index APIs, DB schema, indexer).

> Scope: elevate ReqStudio to **regulated-grade** use (automotive, defense, medical, public sector) while staying **open-source**, **Git-native**, and **extensible**. This document defines additional **data model**, **APIs**, **UI**, **policy**, and **validation** requirements needed for industry-grade auditability, traceability, and sign-offs.

---

## 0. Executive Summary

We extend the semantic index foundation with: **auditable change control**, **electronic approvals/signatures**, **baselines**, **risk management**, **coverage matrices**, **policy enforcement**, and **exportable evidence packages**. All additions remain **rebuildable from Git** and are designed for **offline review**, **long-term retention**, and **cryptographic integrity**.

**Explicit policy:** *Generated source code, comments, UI text, logs, and docs must **not** mention third‑party RM tools by name. Do not include “inspired by X” or similar phrases.* Violations fail CI via a **banned-term linter** (see §12.3).

---

## 1. Regulatory Posture (informational, non-exhaustive)

This plan targets capabilities commonly expected in high-assurance environments:
- **Traceability:** Requirements ↔ Design Components ↔ Code Commits ↔ Tests ↔ Releases.
- **Change control & baselines:** Immutable snapshots with review/approval gates.
- **Electronic records & e‑signatures:** Reviewer identity, meaning of signature, timestamp, non‑repudiation.
- **Risk management:** Link hazards/risks ↔ controls (requirements) ↔ verification evidence.
- **Audit trail:** Append-only events; tamper‑evident hashing.
- **Evidence packages:** Exportable “compliance bundles” (PDF/CSV/JSON) tied to baselines.

> This is **not legal advice**. We provide technical features enabling alignment with common frameworks (e.g., functional safety, medical device SDLC, aerospace/defense quality systems).

---

## 2. Functional Requirements

### 2.1 Identity & Access (RBAC-lite over Git workflows)
- **R1.1** Users authenticate to the ReqStudio **API** with org SSO (OIDC) or local accounts.
- **R1.2** Roles: `Author`, `Reviewer`, `Approver`, `Admin`.  
- **R1.3** Action gating: only `Approver` may sign approvals; only `Admin` may configure policy.
- **R1.4** Link **Git identities** (name/email, signing key) to app users for provenance.

### 2.2 Baselines & Change Control
- **R2.1** Create **immutable baselines** bound to Git tags (`baseline/<name>`), stored in DB with manifest.
- **R2.2** **Compare** baselines (added/changed/removed SRS-IDs); export report.
- **R2.3** **Change Request (CR)** objects tie proposed edits to one or more SRS-IDs, with status flow: `Draft → In Review → Approved/Rejected`. CRs reference impact & tests.

### 2.3 Electronic Approvals & Signatures
- **R3.1** Approval records capture: approver user-id, full name, reason/meaning, timestamp, document hash, and associated **commit SHA**.
- **R3.2** Optional **cryptographic signature**: GPG or Sigstore (cosign) envelope over an approval payload JSON; stored and verifiable offline.
- **R3.3** GUI prompts for **re-authentication** (password/SSO refresh) at signing time.

### 2.4 Risk Management
- **R4.1** Support **Hazard/Risk** items with fields: `risk_id`, `title`, `severity`, `probability`, `risk_level`, `status`.
- **R4.2** Link risks ↔ **controls** (requirements), and ↔ **verification** (tests).  
- **R4.3** Risk matrix view and export; auto-flag “suspect” controls when risk changes.

### 2.5 Traceability & Coverage
- **R5.1** Coverage matrices: Requirement ↔ Component ↔ Test(s) ↔ Release(s).
- **R5.2** **Suspect propagation:** when an upstream item changes, dependents become suspect until re-verified.
- **R5.3** Semantic link suggestions continue to assist users (from §6 of baseline spec).

### 2.6 Evidence Packages & Exports
- **R6.1** Export **Evidence Bundle** for a baseline: PDFs of docs, approval ledger, risk register, coverage matrix, SBOM (if available), integrity manifest.
- **R6.2** Bundle format: ZIP with `/manifest.json`, `/pdf/`, `/csv/`, `/json/`, and `/signatures/`. Manifest includes hashes (SHA-256) for all files.

### 2.7 Policy Enforcement
- **R7.1** **Required fields** in front-matter per item type (HL/LL/CMP/TST/RISK).  
- **R7.2** **Commit guard**: block merges without required approvals for impacted SRS-IDs.
- **R7.3** **Banned-term linter** fails CI if vendor/tool names appear in code/comments/strings/docs.
- **R7.4** **Status transitions** enforced: e.g., `Draft → In Review → Approved` only with required signatures.

---

## 3. Data Model Extensions (PostgreSQL)

> Place in `db/migrations/0002_regulated.sql` (depends on 0001 schema).

```sql
-- Users & roles (can be mirrored from IdP; store subset for audit join)
CREATE TABLE app_user (
  id           BIGSERIAL PRIMARY KEY,
  subject      TEXT UNIQUE NOT NULL,   -- OIDC sub or local UUID
  name         TEXT NOT NULL,
  email        TEXT NOT NULL,
  git_email    TEXT,                   -- optional link to Git identity
  created_at   TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE role (
  id   SMALLSERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL           -- Author/Reviewer/Approver/Admin
);

CREATE TABLE user_role (
  user_id BIGINT REFERENCES app_user(id) ON DELETE CASCADE,
  role_id SMALLINT REFERENCES role(id) ON DELETE CASCADE,
  PRIMARY KEY(user_id, role_id)
);

-- Change Requests (CR)
CREATE TABLE change_request (
  id           BIGSERIAL PRIMARY KEY,
  repo_id      BIGINT REFERENCES repo(id) ON DELETE CASCADE,
  title        TEXT NOT NULL,
  description  TEXT,
  status       TEXT NOT NULL CHECK (status IN ('Draft','In Review','Approved','Rejected')) DEFAULT 'Draft',
  created_by   BIGINT REFERENCES app_user(id),
  created_at   TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE change_request_item (
  cr_id        BIGINT REFERENCES change_request(id) ON DELETE CASCADE,
  srs_id       TEXT NOT NULL,
  PRIMARY KEY (cr_id, srs_id)
);

-- Approvals (electronic records; optionally signed cryptographically)
CREATE TABLE approval (
  id            BIGSERIAL PRIMARY KEY,
  srs_id        TEXT NOT NULL,
  docrev_id     BIGINT REFERENCES doc_revision(id),
  commit_sha    CHAR(40) NOT NULL REFERENCES commit(sha),
  approver_id   BIGINT REFERENCES app_user(id) ON DELETE SET NULL,
  meaning       TEXT NOT NULL,             -- e.g., "Review", "Approval", "Verification"
  reason        TEXT,                      -- free text
  signed_at     TIMESTAMPTZ DEFAULT now(),
  sig_alg       TEXT,                      -- 'gpg' | 'sigstore' | null
  sig_payload   BYTEA,                     -- detached signature or bundle
  payload_hash  TEXT NOT NULL              -- SHA-256 over canonical payload JSON
);
CREATE INDEX ON approval(srs_id);
CREATE INDEX ON approval(commit_sha);

-- Audit events (append-only, tamper-evident via hash chain)
CREATE TABLE audit_event (
  id            BIGSERIAL PRIMARY KEY,
  ts            TIMESTAMPTZ DEFAULT now(),
  user_id       BIGINT REFERENCES app_user(id),
  action        TEXT NOT NULL,             -- 'baseline.create','approval.sign','cr.create',etc.
  entity_type   TEXT NOT NULL,
  entity_id     TEXT NOT NULL,
  data          JSONB DEFAULT '{}'::jsonb,
  prev_hash     TEXT,                      -- SHA-256 of previous row’s canonical JSON
  this_hash     TEXT NOT NULL              -- SHA-256 of this row’s canonical JSON incl prev_hash
);
CREATE INDEX ON audit_event(entity_type, entity_id);

-- Risks & links
CREATE TABLE risk_item (
  id           BIGSERIAL PRIMARY KEY,
  risk_id      TEXT UNIQUE NOT NULL,  -- e.g., RISK-001
  title        TEXT NOT NULL,
  severity     TEXT,                  -- org-defined categories
  probability  TEXT,
  risk_level   TEXT,
  status       TEXT CHECK (status IN ('Open','Mitigated','Accepted','Closed')) DEFAULT 'Open',
  owner_id     BIGINT REFERENCES app_user(id),
  meta         JSONB DEFAULT '{}'::jsonb,
  created_at   TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE risk_link (
  risk_id      BIGINT REFERENCES risk_item(id) ON DELETE CASCADE,
  srs_id       TEXT NOT NULL,         -- control requirement or test SRS-ID
  link_type    TEXT NOT NULL CHECK (link_type IN ('controls','verified_by')),
  PRIMARY KEY (risk_id, srs_id, link_type)
);

-- Coverage (verification evidence)
CREATE TABLE verification_evidence (
  id           BIGSERIAL PRIMARY KEY,
  srs_id       TEXT NOT NULL,         -- requirement under test
  test_id      TEXT NOT NULL,         -- test SRS-ID
  passed       BOOLEAN,
  commit_sha   CHAR(40) NOT NULL REFERENCES commit(sha),
  run_at       TIMESTAMPTZ DEFAULT now(),
  meta         JSONB DEFAULT '{}'::jsonb
);
CREATE INDEX ON verification_evidence(srs_id);
CREATE INDEX ON verification_evidence(test_id);

-- Baseline manifest (freeze additional artifacts)
ALTER TABLE baseline ADD COLUMN manifest JSONB DEFAULT '{}'::jsonb;
```

---

## 4. API Additions (FastAPI)

> Place under `/api` project.

### 4.1 Auth & Users
- `GET /me` → current user profile & roles.
- `GET /users/:id` (Admin) → view; `POST /users` (Admin) → create/link; `POST /roles/assign`.

### 4.2 Baselines & Change Control
- `POST /baseline/create {name}` → creates tag & DB rows; writes audit event.
- `GET /baseline/compare?from=&to=` → summary JSON.
- `POST /cr {title, description, srs_ids[]}` → creates CR; `PATCH /cr/:id {status}`.

### 4.3 Approvals & Signatures
- `POST /approval/sign` → body: `{srs_id, docrev_id, commit_sha, meaning, reason, sign_method}`; returns signature receipt.
- `GET /approval/list?srs_id=` → history.

### 4.4 Risks & Coverage
- `POST /risk` → create risk; `POST /risk/:id/link` (controls/verified_by).  
- `GET /risk/:id` → details; `GET /risk` → list/filter.  
- `POST /evidence` → submit verification results (from CI); `GET /coverage?srs_id=`.

### 4.5 Evidence Packages
- `POST /export/evidence?baseline=...` → returns a **ZIP** with manifest, PDFs, matrices, signatures, hashes.

### 4.6 Policy
- `GET /policy` → required fields, banned terms, status transitions.  
- `POST /policy` (Admin) → update policy JSON.

---

## 5. Indexer Enhancements

- Parse **front‑matter** required fields by type; emit validation events.  
- Generate **document hash** (SHA-256) and attach to approvals.  
- Detect **outbound references** (`[[Y10K-...]]`) and update suspect flags when targets changed.  
- Allow **risk** documents with `type: RISK` and specific fields; populate `risk_item` & `risk_link`.  
- CLI adds: `reqstudio-index risks`, `reqstudio-index coverage --from junit.xml`.

---

## 6. GUI Requirements (PyQt6)

- **Search & Suggestions:** continue from baseline; add filters for `status`, `owner`, `type`.
- **Approvals:**  
  - Panel shows approval history per SRS-ID.  
  - **Sign** dialog: displays signing payload, requires re-auth, writes audit event.  
- **Baselines:** create/compare; show diff view by SRS-ID; export Evidence Bundle.
- **Risks:** risk register view; link controls/tests; matrix heatmap.
- **Coverage:** per requirement show latest pass/fail & links to CI runs.
- **Policy feedback:** inline field validation and status transition guards.
- **No vendor references:** UI strings must not include proprietary tool names.

---

## 7. Policy & Governance

- **Required front‑matter by type** (configurable):  
  - `HL/LL/CMP`: `id,title,version,status,owner,links`  
  - `TST`: `id,title,status,owner,verifies`  
  - `RISK`: `risk_id,title,severity,probability,risk_level,status,owner`
- **Status flow config:** JSON state machine per type; default guards as in §2.7.
- **Banned-term policy:** default list includes known proprietary RM brand names; editable.  
- **Commit hooks & server gates:** block merges to `main` if approvals missing or banned terms detected.

---

## 8. Security & Integrity

- **Tamper evidence:** all `audit_event` rows form a hash chain (`prev_hash`→`this_hash`).  
- **Cryptographic sign-offs:** GPG or Sigstore signatures over canonical JSON of approval payload.  
- **Signed baselines:** tag annotated & signed; baseline manifest includes SHA-256 for artifacts.  
- **PII controls:** redact sensitive content from embeddings prior to indexing.

---

## 9. Observability

- API metrics (p95 latency per endpoint), DB timings, indexer throughput.  
- Structured logging with request IDs; optional OpenTelemetry.  
- Compliance dashboard tiles: unapproved items, suspect items, coverage %, open risks.

---

## 10. Performance Targets (regulated mode)

- Baseline compare (10k SRS-IDs): **p95 < 400 ms**.  
- Evidence export (500 docs, 50 MB total): **< 60 s** on dev laptop.  
- Approval sign operation: **< 200 ms** to persist + audit + signature generation (excluding external key prompts).

---

## 11. Testing & Validation

### 11.1 Unit
- Required front‑matter validator by type.  
- Status machine guards.  
- Audit hash chain continuity.  
- Signature envelope verify (GPG/Sigstore).

### 11.2 Integration
- Create baseline → compare → export bundle; integrity manifest verifies.  
- Approvals recorded; detached signature verifies offline.  
- Risk ↔ control ↔ test links appear in coverage matrix.

### 11.3 End-to-End
- Author edits LL → CR created → Review → Approval → Baseline → Evidence export.  
- CI posts test results → coverage % increases; suspect clears when re-verified.

---

## 12. Tooling & CI

### 12.1 Makefile tasks
- `make migrate` (apply SQL), `make api`, `make index`, `make evidence`.

### 12.2 GitHub Actions (example matrix)
- Services: Postgres (pgvector), API.  
- Jobs: lint, unit, integration, **policy gates** (required fields, approvals, banned terms).

### 12.3 Banned-Term Linter (fail build if violated)
- Implement as Python script: scan `*.py, *.md, *.ui, *.qss, *.json` for banned terms list from policy.  
- Exit non‑zero with report of offending files/lines.  
- Default list includes major proprietary RM brand names. *(Do not print them in logs; mask with `***`)*

---

## 13. Evidence Bundle Layout

```
bundle_<baseline>_<timestamp>.zip
├─ manifest.json              # baseline name, commit, hashes, signer info
├─ pdf/                       # exported PDFs for specs at baseline
├─ csv/
│   ├─ coverage.csv
│   ├─ approvals.csv
│   └─ risks.csv
├─ json/
│   ├─ items.json             # SRS catalog at baseline
│   ├─ links.json             # traceability edges
│   └─ matrix.json            # coverage matrix
└─ signatures/
    ├─ baseline.tag.asc       # signed tag
    └─ approvals/…            # detached signatures
```

---

## 14. Acceptance Criteria (DoD — Regulated Mode)

- [ ] Baseline creation forms a signed tag, DB rows, and evidence bundle with hashes.  
- [ ] Approvals include identity, meaning, timestamp, payload hash; optional crypto signature verifies offline.  
- [ ] Audit log shows a consistent hash chain across all regulated actions.  
- [ ] Risk register, links, and coverage matrix export correctly at baseline.  
- [ ] Policy gates reject missing front‑matter, invalid status transitions, and merges without required approvals.  
- [ ] Banned-term linter prevents proprietary tool names from entering code, comments, UI, or docs.  
- [ ] All endpoints meet p95 targets; integration tests pass in CI on Linux/macOS/Windows.  

---

## 15. Checklists (Markdown)

### 15.1 Schema & Migrations
- [ ] Create `0002_regulated.sql` with tables in §3.  
- [ ] Seed roles (Author/Reviewer/Approver/Admin).  
- [ ] Add DB constraints & indexes; verify in CI.

### 15.2 API
- [ ] Implement endpoints in §4 with auth.  
- [ ] Add OpenAPI docs; redact secrets in logs.  
- [ ] Add `/export/evidence` ZIP streaming with manifest + hashes.

### 15.3 Indexer
- [ ] Enforce required fields by type; emit warnings → policy gate.  
- [ ] Populate `risk_item`, `risk_link`, `verification_evidence`.  
- [ ] Attach document hash to approvals.

### 15.4 GUI
- [ ] Approvals panel & sign dialog with re-auth.  
- [ ] Baseline create/compare & evidence export.  
- [ ] Risk register & coverage indicators; suspect flags.

### 15.5 CI/Policy
- [ ] Commit-msg hook & server gates for approvals.  
- [ ] Banned-term linter wired into CI.  
- [ ] Performance checks for p95 budgets.

---

## 16. Implementation Notes

- Keep **Git as source of truth**; DB remains derived and rebuildable.  
- Store signatures and manifests in both **Git (notes/tags)** and DB for convenience.  
- Export PDFs via current Qt print; allow optional styled exporters later.  
- All dates **UTC**; store precise commit SHAs for reproducibility.

---

## 17. Out of Scope (for now)

- Real-time collaborative editing.  
- Full-blown identity management (we integrate with existing IdP).  
- Proprietary standard checklists; we provide generic hooks and mappable fields.

---

## 18. Glossary (selected)

- **Baseline** — immutable snapshot of requirements and links at a specific commit/tag.  
- **Approval** — electronic record that a user reviewed and approved a specific item state.  
- **Evidence bundle** — portable package of docs, matrices, and signatures proving conformance.
