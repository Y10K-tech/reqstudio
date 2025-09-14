Here’s a drop-in `TO-DO.md` you can add to the repo.

---

# TO-DO — Y10K ReqStudio

> Focus: evolve a fast, Git-native requirements editor into a **serious, enterprise-capable RM toolchain** while staying simple, auditable, and open.

**Principles**

* Git as the **single source of truth**.
* Markdown-first with **structured metadata** for traceability.
* Everything scriptable; GUIs never block automation.
* Keep the core lean; move extras to plugins.

---

## 0) Immediate polish (post-open-source)

* [ ] **Fix**: Search dialog uses `QInputDialog` only (no dead calls).
* [ ] **Add**: “About” dialog with version, license, and links.
* [ ] **Docs**: Update screenshots and quickstart GIFs in `/docs/img`.
* [ ] **Repo hygiene**: Add `.editorconfig`, `.gitattributes`, and `.gitignore`.
* [ ] **Pre-commit**: Black + Ruff config and badge in README.
* [ ] **CI (GitHub Actions)**: lint, build, smoke-run on Windows/macOS/Linux.
* [ ] **Issue templates**: `bug_report.md`, `feature_request.md`, `question.md`.
* [ ] **Codeowners**: set maintainers for fast triage.

---

## 1) MVP++ (close gaps in the current app)

* [ ] **Two-pane Preview**: Live Markdown preview (read-only), toggle with `F8`.
* [ ] **Styled PDF Export (optional)**:

  * [ ] WeasyPrint (HTML+CSS → PDF) exporter with org CSS.
  * [ ] Pandoc pipeline behind a setting (only if binary found).
  * [ ] Export settings dialog (margins, header/footer, page numbers).
* [ ] **SRS-ID Live Validation**:

  * [ ] Inline highlight for invalid IDs (red underline).
  * [ ] “Validate Document” report listing bad IDs & duplicates.
* [ ] **Commit Guard (optional)**: Block commit if no SRS-ID in message (repo setting).
* [ ] **Branch Wizard**: Suggest `feature/{SRS-ID}-{slug}`, copy to clipboard/switch.
* [ ] **Template Manager**:

  * [ ] Editable templates (stored in `~/.y10k/reqstudio/templates/` and workspace `.reqstudio/templates/`).
  * [ ] Org pack loading (read-only) with override mechanism.
* [ ] **Find/Replace** with regex and “Replace in Selection”.
* [ ] **Status Bar enhancements**: word/char count, cursor line/col.

---

## 2) Structured requirements & traceability

* [ ] **Front-matter metadata** (YAML at top of doc):

  * `id`, `title`, `version`, `status` (Draft/Approved/Deprecated), `owner`, `links` (list).
  * Validate on save. Surface in sidebar (future).
* [ ] **Cross-reference linking**: detect `[[Y10K-...]]` and navigate across files.
* [ ] **Traceability Matrix Generator** (CLI + GUI):

  * [ ] Scan repo for SRS-IDs in specs, ADRs, code (comments), and tests.
  * [ ] Emit CSV/Markdown/HTML matrix: `Requirement ↔ Component ↔ Test(s) ↔ ADR`.
  * [ ] “Suspect” flags when upstream item changed since last baseline.
* [ ] **Impact Analysis**: show incoming/outgoing links for current document (graph).

---

## 3) Reviews, approvals, and baselines

* [ ] **Review Mode**: side comments anchored to line ranges (stored in `.reqstudio/comments/*.json` to avoid merge pain).
* [ ] **Approval Records**: per document, list approvers with date & GPG sig (optional).
* [ ] **Baselines UI**:

  * [ ] Create Baseline → writes manifest + Git tag.
  * [ ] Compare Baselines → generate diff (changed/added/removed IDs).
  * [ ] Export Baseline Pack (ZIP of PDFs + manifest + matrix).

---

## 4) Interop & migration (move-in, move-out)

* [ ] **ReqIF Import/Export** (subset first; full later).
* [ ] **DOCX/CSV Import**: rules-based extraction into Markdown + front-matter.
* [ ] **OpenAPI/GraphQL ingest**: generate requirement stubs from API surface.
* [ ] **Jira/GitHub Issues sync (optional)**: push/pull items mapped by SRS-ID.

---

## 5) Plugin system & automation

* [ ] **Plugin API** (Python entry-points):

  * Hooks: `on_open`, `on_save`, `on_commit`, `on_export`, `validate(document)`.
  * Access to document AST (Markdown + front-matter).
* [ ] **Headless CLI**: `reqstudio-cli`

  * [ ] Validate repo, generate PDFs, produce matrices, create baselines.
  * [ ] Exit codes for CI gates.
* [ ] **Server-assist (optional, separate package)**:

  * [ ] FastAPI indexer for large repos (FTS over specs/comments/ADRs).
  * [ ] REST endpoints used by GUI for global search and analytics dashboards.
  * [ ] No vendor lock-in: all data still lives in Git.

---

## 6) UI/UX upgrades

* [ ] **Sidebars**:

  * Outline (headings), IDs list, metadata editor.
  * Links/Impacts panel with mini-graph.
* [ ] **Themes**: Light/Dark and custom font/spacing preferences (persisted).
* [ ] **Large File Mode**: virtualization for 10k+ line docs; non-blocking ops.
* [ ] **Conflict Helper**: basic 3-way merge assist for Markdown blocks.

---

## 7) Quality, performance, and reliability

* [ ] **Unit tests**: highlighter, validators, ID parser, CLI tools.
* [ ] **Integration tests**: open workspace, edit, save, commit, export (headless).
* [ ] **Load tests**: open 500+ files; generate matrices from 10k+ IDs.
* [ ] **Crash reporting** (opt-in local logs; no telemetry by default).
* [ ] **Binary releases**: PyInstaller builds for Win/macOS/Linux with notarization/signing docs.

---

## 8) Security & compliance helpers

* [ ] **PII linter** (optional plugin): highlight potential secrets/PII in specs.
* [ ] **Commit signing**: detect/encourage GPG use; show badge if signed.
* [ ] **Policy presets**: enforce statuses/required metadata fields per repo.
* [ ] **Export redaction**: rule-based removal of internal notes on PDF export.

---

## 9) Documentation & community

* [ ] **User Guide** (with gifs): editing, linking, baselines, matrices, export.
* [ ] **Admin Guide**: org templates, policies, hooks, CI integration examples.
* [ ] **Developer Guide**: plugin API, architecture diagram, extension points.
* [ ] **Cookbook**:

  * [ ] “Enforce SRS-ID in PR titles” via CI.
  * [ ] “Generate traceability report nightly.”
  * [ ] “Baseline per release tag” workflow.
* [ ] **Discussions** enabled; roadmap board; good first issues.

---

## 10) Architecture evolution

* [ ] **Document Model**: internal AST for Markdown with positional anchors (stable IDs).
* [ ] **Link Index**: cached cross-ref graph to power impact view & suspect flags.
* [ ] **Export Pipeline**: pluggable backends with common intermediate (HTML AST).
* [ ] **Workspace Settings**: `.reqstudio/config.yaml` for org rules and exporter prefs.
* [ ] **Performance**: lazy load, background index, cancelable tasks.

---

## 11) Competitive-parity targets (generic)

* [ ] **Baselines & comparison** at scale, with reports.
* [ ] **Suspect propagation** when upstream changes.
* [ ] **Rich import/export** (ReqIF, DOCX) to interoperate with legacy tools.
* [ ] **Review & approvals** with signatures and audit trail (Git-native).
* [ ] **Traceability matrices** spanning requirements ↔ design ↔ tests.
* [ ] **Policy enforcement** for statuses/fields/workflows (configurable).
* [ ] **Scalable search/index** for multi-repo organizations (optional server).

---

## 12) Non-goals (to avoid bloat)

* Heavy multi-user real-time editing (use Git workflows instead).
* Replacing your ticket tracker or CI system.
* Closed data stores: **all artifacts live in Git**, human-readable.

---

## 13) Versioning & release plan (proposal)

* **v0.2** — MVP++: preview, styled PDFs (optional), ID validation, template manager, CLI validate/export.
* **v0.3** — Traceability & baselines: matrix generator, cross-refs, baselines UI, suspect flags (initial).
* **v0.4** — Reviews/approvals: comments, approver records, signed releases; ReqIF export (subset).
* **v0.5** — Plugins & server-assist: plugin API, search index service, rich reports.
* **v1.0** — Enterprise-ready: scalability, interop maturity, policy enforcement, binaries & docs polished.

---

## 14) Nice-to-haves / Stretch

* Mermaid/Graphviz previews in the editor/exports.
* Diagram stencils for C4 (Context/Container) with export.
* Multi-document publish pipeline (release notes + bundle PDF).
* Spellcheck with user dictionaries.

---

## 15) Acceptance criteria (quality gates)

* Each feature ships with:

  * [ ] Unit/integration tests (where applicable)
  * [ ] Docs updated (User/Dev/Admin)
  * [ ] CLI parity if feature affects pipelines
  * [ ] Works on Win/macOS/Linux (CI proof)
  * [ ] No telemetry; opt-in logs only

---

### Implementation seeds (references inside repo)

* `app.py`: main window, menus, export, dialogs → extend for preview, sidebars, settings.
* `highlighter.py`: add validators & underline styles.
* `templates.py`: make paths dynamic; introduce template packs.
* `git_backend.py`: expand for baseline tags, signed commits, blame for impact hints.
* `utils.py`: add front-matter parser, ID link resolver, matrix generator helpers.
* `cli/reqstudio_cli.py` (new): headless commands for CI.

---

**Call for contributors**: If you care about fast, open, Git-native requirements, pick any unchecked item and open a PR. Keep it small, reference an SRS-ID where relevant, and include docs.
