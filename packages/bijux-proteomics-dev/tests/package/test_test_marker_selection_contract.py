from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


pytestmark = pytest.mark.slow


def _pytest_collect_output(*args: str) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def test_unit_marker_selection_excludes_benchmark_and_external_data_surfaces() -> None:
    output = _pytest_collect_output(
        "-m",
        "unit",
        "packages/bijux-proteomics-core/tests/chemistry/test_chemistry_surface.py",
        "packages/bijux-proteomics-core/tests/benchmarks/test_external_dda_trial_surface.py",
        "packages/bijux-proteomics-runtime/tests/execution/test_external_quant_contract_surface.py",
    )

    assert "test_chemistry_surface.py" in output
    assert "test_external_dda_trial_surface.py" not in output
    assert "test_external_quant_contract_surface.py" not in output


def test_benchmark_and_external_data_markers_collect_corpus_backed_surfaces() -> None:
    output = _pytest_collect_output(
        "-m",
        "benchmark or external_data",
        "packages/bijux-proteomics-core/tests/chemistry/test_chemistry_surface.py",
        "packages/bijux-proteomics-core/tests/benchmarks/test_external_dda_trial_surface.py",
        "packages/bijux-proteomics-runtime/tests/execution/test_external_quant_contract_surface.py",
    )

    assert "test_chemistry_surface.py" not in output
    assert "test_external_dda_trial_surface.py" in output
    assert "test_external_quant_contract_surface.py" in output
