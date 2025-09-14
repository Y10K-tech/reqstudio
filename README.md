<p align="center">
  <img src="media/reqstudio_logo.png" alt="Reqstudio logo" width="300"/>
</p>

# Y10K ReqStudio

> **Git-driven requirements editor (PyQt6) for SRS workflows** — write, version, and export your specs with **traceability by design**.

![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-informational.svg)
![Language](https://img.shields.io/badge/language-Python%203.10%2B-blue.svg)
![GUI](https://img.shields.io/badge/GUI-PyQt6-purple.svg)


---

## TL;DR

- **What:** A fast, Git-backed editor for **requirements and SRS** (Markdown/Text) with **PDF export** and **file history**.
- **Why:** Tired of slow, locked-in RM tools. Keep it **simple, auditable, and developer-friendly**.
- **How:** Open a folder as a **workspace** (Git repo). Write specs, insert **Y10K templates**, **commit** with SRS-ID, and **export PDF**.

---

## Kort på svenska (Short Swedish summary)

**Y10K ReqStudio** är en Git-driven texteditor för krav/SRS (Markdown). Den har mallar (HL/LL/CMP/ADR/Ticket), PDF-export, commit/historik samt automatisk upptäckt av **SRS-ID**. Öppna en mapp som arbetsyta (Git), skriv krav, committa, exportera.

---

## Why Y10K ReqStudio?

- **Speed & control:** Local files + Git. No vendor lock-in, no lag.
- **Traceability first:** **SRS-ID** is detected in text and surfaced in the UI for frictionless commit messages and branch naming.
- **Works with your stack:** Use it alongside your **FastAPI/Django**, **Next.js**, **Postgres/Redis** projects and CI.
- **Open source:** Extend, fork, embed, or ship to clients without legal gymnastics.

---

## Feature Highlights

- **Git-backed workspace**
  - Init or open an existing repo.
  - Stage & commit current file or **all changes**.
  - Create/switch branches, **push/pull**, and view **per-file history with inline diffs**.
- **SRS-centric editing**
  - Markdown/Text editor with a light **syntax highlighter** (headings, bold/italic, code).
  - **SRS-ID detection:** `Y10K-<PROJ>-<AREA>-(HL|LL|CMP|API|DB|TST)-NNN`.
  - **Built-in templates:** HL, LL, CMP, ADR, Ticket (insert wherever your cursor is).
- **Export**
  - **PDF export** (Qt print pipeline). Ready to attach to approvals or releases.
- **Quality of life**
  - Status bar shows **Workspace / File / Branch / SRS-IDs** found in the buffer.
  - Simple **Find** dialog (Ctrl+F).
  - Cross-platform: Windows, macOS, Linux.

---

## Roadmap (public)

- [ ] Richer Markdown → **styled PDF** (pandoc/WeasyPrint optional integration).
- [ ] **SRS-ID live validation** (highlight invalid formats in red).
- [ ] **Commit message guard**: enforce SRS-ID presence per repo policy.
- [ ] **Branch naming wizard**: suggest `feature/{SRS-ID}-{short}`.
- [ ] **Template manager** (JSON/YAML) + org-wide template packs.
- [ ] **Plugin hooks** (pre-commit checks, export transforms, linters).
- [ ] **Dark theme** / font & spacing preferences.
- [ ] **Localization** packs (sv, en, …) for UI text.
- [ ] **Unit tests** (pytest) and CI badges.
- [ ] **App bundle** builds (PyInstaller) with signed binaries.

---

## Screenshots (placeholders)

```
/docs/img/
  reqstudio-main.png        # Editor + status bar + menu
  reqstudio-history.png     # File history + diff
  reqstudio-templates.png   # Template insertion menu
```

*(Add your images and link them here.)*

---

## Tech Stack

- **Python 3.10+**
- **PyQt6** (GUI, PDF print)
- **GitPython** (version control)
- Light **Markdown highlighter** (custom)

---

## System Requirements

- **OS:** Windows 10/11, macOS 12+, Linux (X11/Wayland)
- **Python:** 3.10 or newer
- **Git:** Git CLI installed & available in PATH (recommended)

---

## Installation

### From source (recommended)

```bash
git clone https://github.com/<your-org>/y10k-reqstudio.git
cd y10k-reqstudio
python -m venv .venv
# Linux/Mac:
. .venv/bin/activate
# Windows:
# .venv\Scripts\activate

pip install -r requirements.txt
python app.py
```

> First run? Use **File → Open Workspace…** to select a folder. If it’s not a Git repo, **Git → Init**.

---

## Usage

### Basic workflow
1. **Open workspace:** `File → Open Workspace…` (choose a folder that’s or will be a Git repo).
2. **Create or open a spec:** `File → Open…` or `File → New`.
3. **Insert a template:** `Templates →` (HL, LL, CMP, ADR, Ticket). Fill in fields.
4. **Save:** `Ctrl+S`.
5. **Commit:** `Git → Stage & Commit…`
   - Default message auto-includes the first detected **SRS-ID** if present.
   - Option to **stage all changes** in the workspace.
6. **Export PDF:** `File → Export as PDF…`
7. **History:** `Git → History (current file)…` to browse commits and view diffs.

### SRS-ID format (Y10K)
```
Y10K-{PROJ}-{AREA}-{TYPE}-{NNN}
TYPE ∈ {HL, LL, CMP, API, DB, TST}
NNN ∈ 001..999
Example: Y10K-ACME-AUTH-LL-003
```

### Branch naming (suggested)
```
feature/{SRS-ID}-{short-name}
# e.g.
feature/Y10K-ACME-AUTH-LL-003-login
```

### Commit messages (suggested)
```
Y10K-ACME-AUTH-LL-003 – refine login error model; add 429 handling
```

---

## Export to PDF

Current export uses **Qt’s print engine** directly from the text buffer. This is robust and dependency-free.

**Planned optional exporters** (if you add them):
- **Pandoc** (Markdown → PDF via LaTeX) for typographically rich output.
- **WeasyPrint** (Markdown → HTML → CSS → PDF) for CSS-driven styling.

We’ll accept PRs behind a **Settings → Exporter** preference.

---

## Configuration & Customization

- **Templates:** see `templates.py`. Add/edit entries and titles.
- **SRS-ID regex:** defined in `app.py` as `SRS_ID_REGEX`. Adjust to your org’s variant.
- **Highlighter:** `highlighter.py` (headings, emphasis, inline code, SRS-IDs).

---

## Keyboard Shortcuts

- **New:** `Ctrl+N`
- **Open:** `Ctrl+O`
- **Save:** `Ctrl+S`
- **Save As:** `Ctrl+Shift+S`
- **Export PDF:** `Ctrl+P`
- **Undo/Redo:** `Ctrl+Z` / `Ctrl+Y`
- **Find:** `Ctrl+F`

---

## Project Layout

```
y10k-reqstudio/
├─ app.py                 # Main window, menus, actions, PDF export, dialogs
├─ git_backend.py         # GitFacade wrapper (GitPython)
├─ highlighter.py         # Lightweight Markdown/SRS-ID highlighter
├─ templates.py           # HL/LL/CMP/ADR/Ticket content blocks
├─ utils.py               # Helpers (newline normalize, SRS-ID detect)
├─ requirements.txt
├─ README.md              # (this file)
└─ LICENSE                # MIT
```

---

## Development (Hacking)

### Dev setup
```bash
git clone https://github.com/<your-org>/y10k-reqstudio.git
cd y10k-reqstudio
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Suggested dev tools (optional)
- **Black** + **Ruff** for formatting/linting
- **pytest** for tests (coming soon)
- **pre-commit** hooks (lint/format before commit)

Example `.pre-commit-config.yaml` (optional):
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.8.0
    hooks: [{id: black}]
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.6
    hooks: [{id: ruff}]
```

### Contribution guide (short)
1. Fork & branch: `feature/<ticket-or-srs-id>-short-name`
2. Keep PRs small and focused (< ~300 LOC changed).
3. Reference SRS-ID in commit messages if applicable.
4. Add/update docs if behavior changes.
5. Pass CI (format/lint/tests).

A more detailed `CONTRIBUTING.md` is welcome via PR.

---

## Alignment with the Y10K SRS Workflow

ReqStudio was built around the **Y10K principles**:
- Single **standard stack**, clear **ADR** for deviations.
- **Traceability > perfection:** SRS-ID everywhere (specs, tickets, PRs, releases).
- **Lean throughput:** low meeting overhead, Kanban, CI/CD by default.
- **Proto vs Product:** different gates and artifacts.

**Included templates** map to your process artifacts:
- **HL** — High-level SRS
- **LL** — Low-level SRS
- **CMP** — Component spec
- **ADR** — Architecture Decision Record
- **Ticket** — PR/Issue template content

---

## Packaging (optional)

To create a standalone app:
- **PyInstaller**: one-file or one-folder bundles per OS.
- Sign binaries as needed (organization-specific).

Example command (very rough):
```bash
pip install pyinstaller
pyinstaller --name "Y10K ReqStudio" --noconfirm --windowed app.py
```

Contributions to set up polished build scripts are welcome.

---

## Security

- ReqStudio edits local files and runs **no untrusted code**.
- Git operations are performed via **GitPython**: ensure your remotes are the ones you intend to use.
- If you find a security issue, please open a private channel (e.g., security@yourdomain.example) or a GitHub Security Advisory.

---

## FAQ

**Q: Does ReqStudio replace full RM suites?**  
A: It’s a **lean alternative** for teams who value speed, Git workflows, and open text formats. If you need advanced workflows (RBAC, sign-offs, e-sign), integrate with your existing toolchain or propose plugins.

**Q: Can I enforce SRS-ID in commits?**  
A: Planned via pre-commit hook / commit guard plugin. For now, use your repo hooks or CI checks.

**Q: Markdown → beautifully styled PDF?**  
A: Current export is plain (robust). Rich exporters (pandoc/WeasyPrint) are on the roadmap behind a toggle.

**Q: Multiple files / multi-doc packaging?**  
A: Yes—workspaces are just folders. Organize as you like (`/srs/hl`, `/srs/ll`, etc.). A “Bundle Export” feature is on the roadmap.

---

## Troubleshooting

- **“No remote configured”** during push/pull  
  Add one: `git remote add origin <URL>` → `git push -u origin <branch>`.
- **No SRS-ID detected**  
  Check your pattern. Default expects `Y10K-*-*-{HL|LL|CMP|API|DB|TST}-NNN`.
- **PDF looks plain**  
  That’s expected for now. Use your corporate template or help us add a styled exporter.

---

## Changelog

We’ll keep a `CHANGELOG.md` with notable changes after the first public release.

---

## Acknowledgments

- Built by **Y10K Software Engineering** for teams who prefer **clarity, speed, and traceability**.
- Thanks to the PyQt and GitPython communities.

---
