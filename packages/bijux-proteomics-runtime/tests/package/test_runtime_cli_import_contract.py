# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import importlib
import os
from pathlib import Path
import subprocess
import sys


def _source_pythonpath() -> str:
    repo_root = Path(__file__).resolve().parents[4]
    src_roots = sorted(repo_root.glob("packages/*/src"))
    return ":".join(str(path) for path in src_roots)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_runtime_cli_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics_runtime.api.cli")

    assert module.cli is not None


def test_runtime_cli_import_contract_succeeds_from_clean_checkout() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "from bijux_proteomics_runtime.api.cli import cli"],
        capture_output=True,
        text=True,
        cwd=_repository_root(),
        env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_runtime_cli_import_contract_avoids_click_and_pydantic_at_import_time() -> None:
    code = """
import builtins
import sys

blocked = ("click", "pydantic")
original_import = builtins.__import__

def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    for blocked_name in blocked:
        if name == blocked_name or name.startswith(blocked_name + "."):
            raise ModuleNotFoundError(f"blocked import: {blocked_name}")
    return original_import(name, globals, locals, fromlist, level)

for module_name in list(sys.modules):
    for blocked_name in blocked:
        if module_name == blocked_name or module_name.startswith(blocked_name + "."):
            sys.modules.pop(module_name, None)

builtins.__import__ = guarded_import
from bijux_proteomics_runtime.api.cli import cli
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": _source_pythonpath()},
        check=False,
    )

    assert result.returncode == 0, result.stderr
