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


def test_core_public_imports_do_not_require_blocked_heavy_packages() -> None:
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


class BlockHeavyImports(importlib.abc.MetaPathFinder):
    def __init__(self, blocked):
        self._blocked = blocked

    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] in self._blocked:
            raise ModuleNotFoundError(fullname)
        return None


sys.meta_path.insert(0, BlockHeavyImports({"pandas", "sklearn", "networkx"}))
sys.path[:] = os.environ["PYTHONPATH"].split(":") + sys.path

import bijux_proteomics as core
from bijux_proteomics import (
    build_fdr_audit_trail,
    build_normalized_run_bundle,
    parse_experimental_design_table,
    parse_fasta_document,
)
import bijux_proteomics.identification
import bijux_proteomics.io.formats
import bijux_proteomics.sequences

assert core.__all__
assert callable(parse_fasta_document)
assert callable(parse_experimental_design_table)
assert callable(build_normalized_run_bundle)
assert callable(build_fdr_audit_trail)
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
