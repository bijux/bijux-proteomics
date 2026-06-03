# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def _source_pythonpath() -> str:
    repo_root = Path(__file__).resolve().parents[4]
    src_roots = sorted(repo_root.glob("packages/*/src"))
    return ":".join(str(path) for path in src_roots)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_agentic_root_import_succeeds_from_package_source_paths() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import agentic_proteins"],
        capture_output=True,
        text=True,
        cwd=_repository_root(),
        env={"PYTHONPATH": _source_pythonpath()},
        check=False,
    )

    assert result.returncode == 0, result.stderr
