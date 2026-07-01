"""Repository cache-hygiene helpers for package-tree cleanup."""

from __future__ import annotations

from pathlib import Path
import shutil

FORBIDDEN_CACHE_DIR_NAMES = (
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
)


def find_forbidden_cache_dirs(root: Path) -> tuple[Path, ...]:
    """Return live cache directories under a repository root."""

    matches: list[Path] = []
    for cache_dir_name in FORBIDDEN_CACHE_DIR_NAMES:
        matches.extend(path for path in root.rglob(cache_dir_name) if path.is_dir())
    return tuple(sorted(dict.fromkeys(matches)))


def purge_forbidden_cache_dirs(root: Path) -> tuple[Path, ...]:
    """Remove live cache directories and return the removed paths."""

    removed = find_forbidden_cache_dirs(root)
    for path in removed:
        try:
            shutil.rmtree(path)
        except FileNotFoundError:
            continue
    return removed
