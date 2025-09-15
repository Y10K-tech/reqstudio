#!/usr/bin/env python3
import sys
import os
import json
import re
import subprocess
from pathlib import Path

STRICT_SRS = r"Y10K-[A-Z0-9]+-[A-Z0-9]+-(HL|LL|CMP|API|DB|TST)-\d{3}"
RELAXED_SRS = r"Y10K-[^-\s]+-[^-\s]+-[A-Z]{2,}-\d{2,}"


def run(cmd, cwd=None, check=True, capture=False):
    if capture:
        result = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    else:
        result = subprocess.run(cmd, cwd=cwd)
    if check and result.returncode != 0:
        msg = result.stderr if capture else f"command failed: {' '.join(cmd)}"
        raise RuntimeError(msg.strip() or "command failed")
    return result


def usage():
    print(
        "\n".join(
            [
                "git req — ReqStudio git extensions",
                "",
                "Usage:",
                "  git req baseline-create <NAME>",
                "  git req matrix <OUT>",
                "  git req verify",
                "  git req notes-add <COMMIT|HEAD> <JSON>",
                "  git req notes-show <COMMIT|HEAD>",
                "  git req install-hook", 
                "  git req install-server-hooks <DIR>",
                "",
                "Examples:",
                "  git req baseline-create v1.2",
                "  git req matrix out/traceability.json",
                "  git req matrix-store",
                "  git req verify",
                "",
                "Notes:",
                "  - Baselines create signed annotated tags baseline/<NAME>.",
                "  - Matrix scans last 500 commits and extracts SRS-IDs.",
                "  - Verify checks HEAD has strict SRS-ID and is after latest baseline.",
            ]
        )
    )


def ensure_repo():
    try:
        run(["git", "rev-parse", "--is-inside-work-tree"], capture=True)
    except Exception:
        print("ERROR: Not inside a git repository.", file=sys.stderr)
        sys.exit(1)


def cmd_baseline_create(args):
    if len(args) != 1:
        usage(); sys.exit(2)
    name = args[0]
    tag = f"baseline/{name}"
    # Check exists
    r = run(["git", "tag", "--list", tag], capture=True)
    if tag in (r.stdout or ""):
        print(f"ERROR: Baseline {tag} already exists.", file=sys.stderr)
        sys.exit(1)
    annotation = json.dumps({"reqstudio": {"baseline": name}})
    try:
        run(["git", "tag", "-s", tag, "-m", annotation])
    except RuntimeError as e:
        print("ERROR: Failed to create signed tag. Ensure git signing is configured.", file=sys.stderr)
        print(str(e), file=sys.stderr)
        sys.exit(1)
    print(f"Created {tag}")


def extract_matrix():
    # get last 500 commits subject and sha
    r = run(["git", "log", "-n", "500", "--pretty=%H\x01%s"], capture=True)
    rows = []
    strict = re.compile(STRICT_SRS)
    relaxed = re.compile(RELAXED_SRS)
    for line in (r.stdout or "").splitlines():
        if not line.strip():
            continue
        sha, subj = line.split("\x01", 1)
        ids = list(set(strict.findall(subj)))
        relaxed_only = False
        if not ids:
            ids = list(set(relaxed.findall(subj)))
            if ids:
                relaxed_only = True
        if ids:
            rows.append({"commit": sha, "ids": ids, **({"relaxed": True} if relaxed_only else {})})
    return rows


def cmd_matrix(args):
    if len(args) != 1:
        usage(); sys.exit(2)
    out = Path(args[0])
    out.parent.mkdir(parents=True, exist_ok=True)
    data = extract_matrix()
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {out}")


def cmd_verify(args):
    # HEAD has strict SRS-ID
    r = run(["git", "log", "-n", "1", "--pretty=%s"], capture=True)
    subj = (r.stdout or "").strip()
    if not re.search(STRICT_SRS, subj):
        print("ERROR: HEAD commit message must contain a strict SRS-ID.", file=sys.stderr)
        sys.exit(1)
    # Latest baseline tag
    r = run(["git", "for-each-ref", "--sort=-taggerdate", "--format=%(refname:short)", "refs/tags/baseline"], capture=True, check=False)
    tag = None
    for line in (r.stdout or "").splitlines():
        if line.startswith("baseline/"):
            tag = line; break
    if not tag:
        print("ERROR: No baseline/* tag found.", file=sys.stderr)
        sys.exit(1)
    # Check ancestor
    rc = subprocess.run(["git", "merge-base", "--is-ancestor", tag, "HEAD"]).returncode
    if rc != 0:
        print(f"ERROR: Latest baseline {tag} is not an ancestor of HEAD.", file=sys.stderr)
        sys.exit(1)
    print("verify: OK")


def cmd_notes_add(args):
    if len(args) < 2:
        usage(); sys.exit(2)
    commit = args[0]
    payload = " ".join(args[1:])
    # Validate JSON
    try:
        json.loads(payload)
    except Exception as e:
        print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    run(["git", "notes", "--ref=reqstudio", "add", "-m", payload, commit])
    print("notes: added")


def cmd_notes_show(args):
    if len(args) != 1:
        usage(); sys.exit(2)
    commit = args[0]
    r = run(["git", "notes", "--ref=reqstudio", "show", commit], capture=True, check=False)
    print((r.stdout or "").strip())


def cmd_notes_push(args):
    if len(args) != 1:
        usage(); sys.exit(2)
    remote = args[0]
    run(["git", "push", remote, "refs/notes/reqstudio"], check=True)
    print(f"Pushed notes to {remote}")


def cmd_notes_fetch(args):
    if len(args) != 1:
        usage(); sys.exit(2)
    remote = args[0]
    run(["git", "fetch", remote, "refs/notes/reqstudio:refs/notes/reqstudio"], check=True)
    print(f"Fetched notes from {remote}")


HOOK_CONTENT = """#!/usr/bin/env bash
MSG_FILE="$1"
if [ -z "$MSG_FILE" ]; then
  echo "ERROR: commit-msg hook: missing message file" >&2
  exit 1
fi
if ! grep -E -q 'Y10K-[A-Z0-9]+-[A-Z0-9]+-(HL|LL|CMP|API|DB|TST)-[0-9]{3}' "$MSG_FILE"; then
  echo 'ERROR: Commit message must contain a valid SRS-ID (Y10K-*-NNN).' >&2
  exit 1
fi
exit 0
"""


def cmd_install_hook(args):
    # write .git/hooks/commit-msg
    r = run(["git", "rev-parse", "--git-path", "hooks"], capture=True)
    hooks_dir = Path((r.stdout or "").strip())
    hooks_dir.mkdir(parents=True, exist_ok=True)
    path = hooks_dir / "commit-msg"
    path.write_text(HOOK_CONTENT, encoding="utf-8")
    try:
        os.chmod(path, 0o755)
    except Exception:
        pass
    print(f"Installed hook: {path}")


SERVER_PRE_RECEIVE = """#!/usr/bin/env bash
set -euo pipefail
STRICT='Y10K-[A-Z0-9]+-[A-Z0-9]+-(HL|LL|CMP|API|DB|TST)-[0-9]{3}'
protected_branch() { [[ "$1" == refs/heads/main || "$1" =~ ^refs/heads/release/ ]]; }
logf() {
  dir=$(git rev-parse --git-path hooks)
  f="$dir/reqstudio-server.log"
  # rotate if >100KB
  if [ -f "$f" ] && [ $(wc -c <"$f") -gt 102400 ]; then mv "$f" "$f.1"; fi
  echo "[$(date -Iseconds)] $*" >> "$f"
}
while read old new ref; do
  if protected_branch "$ref"; then
    # ensure each new commit has strict SRS-ID
    for c in $(git rev-list "$old..$new"); do
      msg=$(git log -n1 --pretty=%s "$c")
      if ! [[ "$msg" =~ $STRICT ]]; then
        echo "REJECT: Commit $c to $ref lacks strict SRS-ID" >&2
        logf "reject $ref $c no-srs"
        echo "Hint: Add Y10K-<PROJ>-<AREA>-<TYPE>-NNN to commit message or use --no-verify for local bypass." >&2
        exit 1
      fi
    done
  fi
done
exit 0
"""

SERVER_UPDATE = """#!/usr/bin/env bash
set -euo pipefail
refname="$1" old="$2" new="$3"
if [[ "$refname" == refs/heads/main ]]; then
  # Require that a new baseline/* tag exists since the previous main tip
  last_tag=$(git for-each-ref --sort=-taggerdate --format='%(refname:short)' refs/tags/baseline | head -n1)
  if [ -z "$last_tag" ]; then
    echo "REJECT: No baseline/* tag exists for main" >&2
    echo "Hint: Create a baseline tag: git req baseline-create <NAME>" >&2
    dir=$(git rev-parse --git-path hooks); echo "[$(date -Iseconds)] reject main no-baseline" >> "$dir/reqstudio-server.log"
    exit 1
  fi
  if ! git merge-base --is-ancestor "$last_tag" "$new"; then
    echo "REJECT: Latest baseline $last_tag is not ancestor of new main tip" >&2
    echo "Hint: Create a baseline tag: git req baseline-create <NAME>" >&2
    dir=$(git rev-parse --git-path hooks); echo "[$(date -Iseconds)] reject main baseline-ancestor" >> "$dir/reqstudio-server.log"
    exit 1
  fi
fi
exit 0
"""


def cmd_install_server_hooks(args):
    if len(args) != 1:
        usage(); sys.exit(2)
    d = Path(args[0]); d.mkdir(parents=True, exist_ok=True)
    (d / "pre-receive").write_text(SERVER_PRE_RECEIVE, encoding="utf-8"); os.chmod(d / "pre-receive", 0o755)
    (d / "update").write_text(SERVER_UPDATE, encoding="utf-8"); os.chmod(d / "update", 0o755)
    print(f"Installed server hooks under {d}")


def cmd_matrix_store(args):
    # Generate matrix and store as a namespaced ref pointing to a tree with reqstudio/matrix.json
    data = extract_matrix()
    payload = json.dumps(data, indent=2)
    # hash-object
    p = subprocess.Popen(["git", "hash-object", "-w", "--stdin"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    out, _ = p.communicate(payload)
    if p.returncode != 0:
        print("ERROR: failed to hash object", file=sys.stderr); sys.exit(1)
    blob = out.strip()
    # mktree input
    tree_input = f"100644 blob {blob}\treqstudio/matrix.json\n"
    p2 = subprocess.Popen(["git", "mktree"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    out2, _ = p2.communicate(tree_input)
    if p2.returncode != 0:
        print("ERROR: mktree failed", file=sys.stderr); sys.exit(1)
    tree = out2.strip()
    # commit-tree
    r = run(["git", "commit-tree", "-m", "reqstudio: matrix artifact", tree], capture=True)
    commit = (r.stdout or "").strip()
    # update ref
    run(["git", "update-ref", "refs/reqstudio/matrix", commit])
    print("Stored matrix at refs/reqstudio/matrix")


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help", "help"):
        usage(); return 0
    ensure_repo()
    cmd = argv[1]
    args = argv[2:]
    try:
        if cmd == "baseline-create":
            cmd_baseline_create(args)
        elif cmd == "matrix":
            cmd_matrix(args)
        elif cmd == "matrix-store":
            cmd_matrix_store(args)
        elif cmd == "verify":
            cmd_verify(args)
        elif cmd == "notes-add":
            cmd_notes_add(args)
        elif cmd == "notes-show":
            cmd_notes_show(args)
        elif cmd == "notes-push":
            cmd_notes_push(args)
        elif cmd == "notes-fetch":
            cmd_notes_fetch(args)
        elif cmd == "install-hook":
            cmd_install_hook(args)
        elif cmd == "install-server-hooks":
            cmd_install_server_hooks(args)
        else:
            usage(); return 2
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
