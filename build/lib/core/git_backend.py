from __future__ import annotations
import os
from pathlib import Path
from typing import List, Optional

from git import Repo, GitCommandError, InvalidGitRepositoryError, NoSuchPathError


class GitError(Exception):
    pass


class GitFacade:
    def __init__(self):
        self._repo: Optional[Repo] = None
        self._root: Optional[Path] = None

    def open(self, root: Path):
        try:
            self._repo = Repo(str(root))
            self._root = Path(root)
        except (InvalidGitRepositoryError, NoSuchPathError) as e:
            raise GitError(f"Inget Git-repo i {root}") from e

    def init(self, root: Path):
        try:
            self._repo = Repo.init(str(root))
            self._root = Path(root)
        except Exception as e:
            raise GitError(f"Misslyckades initiera repo: {e}") from e

    def is_open(self) -> bool:
        return self._repo is not None

    def current_branch(self) -> str:
        if not self._repo:
            raise GitError("Repo ej öppet")
        try:
            return self._repo.active_branch.name
        except TypeError:
            # detached HEAD
            return "(detached)"

    def relpath(self, abspath: str | Path) -> str:
        if not self._root:
            raise GitError("Repo ej öppet")
        return os.path.relpath(str(abspath), str(self._root))

    def commit(self, paths: Optional[List[Path]] = None, message: str = ""):
        if not self._repo:
            raise GitError("Repo ej öppet")
        try:
            if paths is None:
                self._repo.git.add("--all")
            else:
                for p in paths:
                    self._repo.git.add(str(p))
            if not message:
                message = "update"
            if not self._repo.is_dirty(index=True, working_tree=True, untracked_files=True):
                raise GitError("Inga ändringar att committa.")
            self._repo.index.commit(message)
        except GitCommandError as e:
            raise GitError(str(e)) from e

    def list_branches(self) -> List[str]:
        if not self._repo:
            raise GitError("Repo ej öppet")
        return [h.name for h in self._repo.heads]

    def create_branch(self, name: str, checkout: bool = True):
        if not self._repo:
            raise GitError("Repo ej öppet")
        try:
            new_head = self._repo.create_head(name)
            if checkout:
                new_head.checkout()
        except GitCommandError as e:
            raise GitError(str(e)) from e

    def checkout(self, name: str):
        if not self._repo:
            raise GitError("Repo ej öppet")
        try:
            self._repo.git.checkout(name)
        except GitCommandError as e:
            raise GitError(str(e)) from e

    def log_file(self, relpath: str, max_count: int = 100):
        if not self._repo:
            raise GitError("Repo ej öppet")
        commits = list(self._repo.iter_commits(paths=relpath, max_count=max_count))
        out = []
        for c in commits:
            out.append({
                "hash": c.hexsha,
                "short": c.hexsha[:8],
                "author": c.author.name if c.author else "?",
                "when": c.committed_datetime.strftime("%Y-%m-%d %H:%M"),
                "msg": (c.message or "").strip().splitlines()[0]
            })
        return out

    def get_file_at_commit(self, commit_hash: str, relpath: str) -> str:
        if not self._repo:
            raise GitError("Repo ej öppet")
        try:
            commit = self._repo.commit(commit_hash)
            tree = commit.tree
            blob = tree / relpath
            data = blob.data_stream.read()
            return data.decode("utf-8", errors="replace")
        except Exception as e:
            raise GitError(f"Kunde inte läsa {relpath} @ {commit_hash[:8]}: {e}") from e

    def push(self) -> str | None:
        if not self._repo:
            raise GitError("Repo ej öppet")
        if not self._repo.remotes:
            raise GitError("Inget remote konfigurerat (lägg till origin).")
        try:
            res = self._repo.remotes[0].push()
            return "; ".join([str(r) for r in res])
        except GitCommandError as e:
            raise GitError(str(e)) from e

    def pull(self) -> str | None:
        if not self._repo:
            raise GitError("Repo ej öppet")
        if not self._repo.remotes:
            raise GitError("Inget remote konfigurerat (lägg till origin).")
        try:
            res = self._repo.remotes[0].pull()
            return "; ".join([str(r) for r in res])
        except GitCommandError as e:
            raise GitError(str(e)) from e
