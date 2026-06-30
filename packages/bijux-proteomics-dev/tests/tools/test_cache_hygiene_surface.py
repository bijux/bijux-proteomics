from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics_dev.tools.cache_hygiene import (
    find_forbidden_cache_dirs,
    purge_forbidden_cache_dirs,
)


def test_find_forbidden_cache_dirs_discovers_nested_cache_directories(
    tmp_path: Path,
) -> None:
    first = tmp_path / "package-a" / ".pytest_cache"
    second = tmp_path / "package-b" / "tests" / ".ruff_cache"
    third = tmp_path / "package-c" / ".ruff_cache"
    for path in (first, second, third):
        path.mkdir(parents=True)

    found = find_forbidden_cache_dirs(tmp_path)

    assert found == (first, second, third)


def test_purge_forbidden_cache_dirs_removes_live_cache_directories(
    tmp_path: Path,
) -> None:
    cache_dir = tmp_path / "package-a" / ".pytest_cache"
    cache_dir.mkdir(parents=True)
    (cache_dir / "module.cpython-311.pyc").write_text("compiled", encoding="utf-8")

    removed = purge_forbidden_cache_dirs(tmp_path)

    assert removed == (cache_dir,)
    assert find_forbidden_cache_dirs(tmp_path) == ()


def test_purge_forbidden_cache_dirs_tolerates_disappearing_cache_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache_dir = tmp_path / "package-a" / "__pycache__"
    cache_dir.mkdir(parents=True)

    def _disappearing_rmtree(path: Path) -> None:
        path.rmdir()
        raise FileNotFoundError(path)

    monkeypatch.setattr(
        "bijux_proteomics_dev.tools.cache_hygiene.shutil.rmtree",
        _disappearing_rmtree,
    )

    removed = purge_forbidden_cache_dirs(tmp_path)

    assert removed == (cache_dir,)
