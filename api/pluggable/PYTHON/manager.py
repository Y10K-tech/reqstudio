"""
Lightweight plugin support for ReqStudio (Python side).

Usage (future GUI/API integration):
 - Place user plugins as Python files/modules on a search path.
 - Each plugin should define a `register(plugin_registry)` function.
 - The registry exposes `add_action(name, callable)` and `actions` mapping.

This module intentionally lives under api/pluggable/PYTHON per project layout.
"""
from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Callable, Dict, List, Optional


@dataclass
class PluginRegistry:
    actions: Dict[str, Callable] = field(default_factory=dict)

    def add_action(self, name: str, fn: Callable) -> None:
        self.actions[name] = fn


def discover_plugin_modules(search_dirs: List[Path]) -> List[str]:
    mods = []
    for d in search_dirs:
        if not d.exists():
            continue
        for p in d.glob("*.py"):
            if p.stem.startswith("_"):
                continue
            # Add a synthetic module spec using importlib
            mods.append(p.as_posix())
    return mods


def load_plugins(search_dirs: Optional[List[Path]] = None) -> PluginRegistry:
    registry = PluginRegistry()
    search_dirs = search_dirs or [Path.cwd() / "plugins"]

    # Ensure dirs are importable
    for d in search_dirs:
        if d.exists() and d.as_posix() not in sys.path:
            sys.path.insert(0, d.as_posix())

    for d in search_dirs:
        if not d.exists():
            continue
        for py in d.glob("*.py"):
            mod_name = py.stem
            try:
                mod: ModuleType = importlib.import_module(mod_name)
                if hasattr(mod, "register"):
                    mod.register(registry)
            except Exception as e:
                # In production, log this via structured logger
                print(f"[plugin] failed loading {py}: {e}")
    return registry

