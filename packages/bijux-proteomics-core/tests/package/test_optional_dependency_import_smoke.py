from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_core_imports_succeed_without_optional_pyarrow() -> None:
    pythonpath = ":".join(
        [
            str(REPO_ROOT / "packages" / "bijux-proteomics-foundation" / "src"),
            str(REPO_ROOT / "packages" / "bijux-proteomics-core" / "src"),
        ]
    )
    script = """
import importlib.abc
import os
import sys


class BlockOptionalImports(importlib.abc.MetaPathFinder):
    def __init__(self, blocked):
        self._blocked = blocked

    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] in self._blocked:
            raise ModuleNotFoundError(fullname)
        return None


sys.meta_path.insert(0, BlockOptionalImports({"pyarrow"}))
sys.path[:] = os.environ["PYTHONPATH"].split(":") + sys.path

import bijux_proteomics
from bijux_proteomics.sequences.digestion import export_peptides_parquet

assert bijux_proteomics.__all__
assert callable(export_peptides_parquet)
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PYTHONPATH": pythonpath,
        },
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
