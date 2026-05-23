# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import importlib
from pathlib import Path
import subprocess
import sys


def _source_pythonpath() -> str:
    repo_root = Path(__file__).resolve().parents[4]
    src_roots = sorted(repo_root.glob("packages/*/src"))
    return ":".join(str(path) for path in src_roots)


def _assert_import_statement_succeeds_without_modules(
    statement: str, *blocked_modules: str
) -> None:
    blocked_list = ", ".join(repr(name) for name in blocked_modules)
    code = f"""
import builtins
import sys

blocked = ({blocked_list},)
original_import = builtins.__import__

def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    for blocked_name in blocked:
        if name == blocked_name or name.startswith(blocked_name + "."):
            raise ModuleNotFoundError(f"blocked import: {{blocked_name}}")
    return original_import(name, globals, locals, fromlist, level)

for module_name in list(sys.modules):
    for blocked_name in blocked:
        if module_name == blocked_name or module_name.startswith(blocked_name + "."):
            sys.modules.pop(module_name, None)

builtins.__import__ = guarded_import
{statement}
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": _source_pythonpath()},
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_core_package_import_contract() -> None:
    package = importlib.import_module("bijux_proteomics")

    assert package.__name__ == "bijux_proteomics"


def test_core_cli_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics.interfaces.cli")

    assert module.cli is not None


def test_core_package_import_contract_avoids_pydantic_at_root_import_time() -> None:
    _assert_import_statement_succeeds_without_modules(
        "import bijux_proteomics",
        "pydantic",
    )


def test_core_cli_import_contract_avoids_click_and_pydantic_at_import_time() -> None:
    _assert_import_statement_succeeds_without_modules(
        "from bijux_proteomics.interfaces.cli import cli",
        "click",
        "pydantic",
    )


def test_io_package_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics.io")

    assert hasattr(module, "parse_mzml")
    assert hasattr(module, "score_chromatographic_evidence")
    assert hasattr(module, "score_dia_fragment_trace_coelution")
    assert hasattr(module, "pick_chromatographic_peaks")
    assert hasattr(module, "align_chromatographic_peak_retention_times")
    assert hasattr(module, "extract_mzml_xic_traces")


def test_quantification_package_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics.quantification")

    assert hasattr(module, "build_label_free_intensity_table")


def test_study_package_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics.study")

    assert hasattr(module, "build_run_qc_assessment")


def test_interpretation_ppi_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics.interpretation")

    assert hasattr(module, "build_ppi_network_module_report")


def test_workflow_package_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics.workflow")

    assert hasattr(module, "run_proteomics_workflow")
