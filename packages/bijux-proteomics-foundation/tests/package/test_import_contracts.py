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


def test_foundation_root_import_contract_avoids_pydantic_at_import_time() -> None:
    code = """
import builtins
import sys

original_import = builtins.__import__

def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "pydantic" or name.startswith("pydantic."):
        raise ModuleNotFoundError("blocked import: pydantic")
    return original_import(name, globals, locals, fromlist, level)

for module_name in list(sys.modules):
    if module_name == "pydantic" or module_name.startswith("pydantic."):
        sys.modules.pop(module_name, None)

builtins.__import__ = guarded_import
import bijux_proteomics_foundation
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": _source_pythonpath()},
        check=False,
    )

    assert result.returncode == 0, result.stderr
