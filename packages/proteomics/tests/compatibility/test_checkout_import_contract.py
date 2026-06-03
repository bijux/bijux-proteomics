from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

pytestmark = pytest.mark.unit


def _source_pythonpath() -> str:
    repo_root = Path(__file__).resolve().parents[4]
    src_roots = sorted(repo_root.glob("packages/*/src"))
    return ":".join(str(path) for path in src_roots)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_proteomics_cli_import_succeeds_from_package_source_paths() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "from proteomics.cli import main"],
        capture_output=True,
        text=True,
        cwd=_repository_root(),
        env={"PYTHONPATH": _source_pythonpath()},
        check=False,
    )

    assert result.returncode == 0, result.stderr
