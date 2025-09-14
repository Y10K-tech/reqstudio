"""
ReqStudio core package.

Exposes primary classes and utilities for the GUI app.
"""

__all__ = [
    "GitFacade",
    "GitError",
    "MarkdownHighlighter",
    "TEMPLATES",
    "detect_srs_ids",
    "normalize_newlines",
]

from .git_backend import GitFacade, GitError  # noqa: E402
from .highlighter import MarkdownHighlighter  # noqa: E402
from .templates import TEMPLATES  # noqa: E402
from .utils import detect_srs_ids, normalize_newlines  # noqa: E402

