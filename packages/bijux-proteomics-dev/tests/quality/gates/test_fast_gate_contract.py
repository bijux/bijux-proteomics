"""Tests for the curated fast gate contract."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.gates.fast_gate import (
    default_fast_gate_targets,
    render_fast_gate_pytest_args,
    run_fast_gate,
    validate_fast_gate_targets,
)


def test_fast_gate_targets_cover_expected_surfaces() -> None:
    targets = default_fast_gate_targets()

    assert {target.surface for target in targets} == {
        "digest",
        "identification",
        "format",
        "qc",
        "runtime-artifact",
        "evidence",
    }


def test_fast_gate_targets_exist_and_render_pytest_args() -> None:
    repo_root = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "configs").is_dir()
    )

    assert validate_fast_gate_targets(repo_root) == []
    assert all(Path(path).exists() for path in render_fast_gate_pytest_args(repo_root))
    assert run_fast_gate(repo_root, execute=False) == 0
