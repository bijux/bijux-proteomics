"""Tests for the curated medium gate contract."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.medium_gate import (
    default_medium_gate_targets,
    render_medium_gate_pytest_args,
    run_medium_gate,
    validate_medium_gate,
)


def test_medium_gate_targets_cover_expected_surfaces() -> None:
    targets = default_medium_gate_targets()

    assert {target.surface for target in targets} == {
        "workflow-reproducibility",
        "evidence-integrity",
        "runtime-service",
        "package-boundaries",
    }


def test_medium_gate_targets_exist_and_validate_repo_prerequisites() -> None:
    repo_root = Path(__file__).resolve().parents[3]

    assert validate_medium_gate(repo_root) == []
    assert all(
        Path(path).exists() for path in render_medium_gate_pytest_args(repo_root)
    )
    assert run_medium_gate(repo_root, execute=False) == 0
