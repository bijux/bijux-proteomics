"""Curated fast gate for the minimum cross-surface proteomics baseline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys

__all__ = [
    "FastGateTarget",
    "default_fast_gate_targets",
    "render_fast_gate_pytest_args",
    "run_fast_gate",
    "validate_fast_gate_targets",
]


@dataclass(frozen=True)
class FastGateTarget:
    """One curated fast-gate target."""

    surface: str
    test_path: str
    rationale: str


def default_fast_gate_targets() -> tuple[FastGateTarget, ...]:
    """Return the curated fast-gate targets for baseline repository integrity."""
    return (
        FastGateTarget(
            surface="digest",
            test_path="packages/bijux-proteomics-core/tests/test_digestion_engine_surface.py",
            rationale="prove digestion basics remain correct",
        ),
        FastGateTarget(
            surface="identification",
            test_path="packages/bijux-proteomics-core/tests/test_identification_surface.py",
            rationale="prove identification confidence and FDR basics remain intact",
        ),
        FastGateTarget(
            surface="format",
            test_path="packages/bijux-proteomics-core/tests/test_format_ingestion_surface.py",
            rationale="prove format detection and ingestion basics remain intact",
        ),
        FastGateTarget(
            surface="qc",
            test_path="packages/bijux-proteomics-core/tests/test_qc_surface.py",
            rationale="prove QC policy and reporting basics remain intact",
        ),
        FastGateTarget(
            surface="runtime-artifact",
            test_path="packages/bijux-proteomics-core/tests/test_production_run_surface.py",
            rationale="prove runtime artifact bundle basics remain intact",
        ),
        FastGateTarget(
            surface="evidence",
            test_path="packages/bijux-proteomics-knowledge/tests/test_evidence_bundle.py",
            rationale="prove evidence trust and bundle basics remain intact",
        ),
    )


def validate_fast_gate_targets(repo_root: Path) -> list[str]:
    """Validate the curated fast-gate target list."""
    failures: list[str] = []
    expected_surfaces = {
        "digest",
        "identification",
        "format",
        "qc",
        "runtime-artifact",
        "evidence",
    }
    surfaces = {target.surface for target in default_fast_gate_targets()}
    if surfaces != expected_surfaces:
        failures.append(
            f"fast gate surfaces changed from {sorted(expected_surfaces)} to {sorted(surfaces)}"
        )
    for target in default_fast_gate_targets():
        path = repo_root / target.test_path
        if not path.exists():
            failures.append(f"missing fast gate target: {target.test_path}")
    return failures


def render_fast_gate_pytest_args(repo_root: Path) -> list[str]:
    """Render the absolute pytest target list for the curated fast gate."""
    return [str(repo_root / target.test_path) for target in default_fast_gate_targets()]


def run_fast_gate(repo_root: Path, *, execute: bool = False) -> int:
    """Validate or execute the curated fast gate."""
    failures = validate_fast_gate_targets(repo_root)
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    if not execute:
        return 0
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *render_fast_gate_pytest_args(repo_root)],
        cwd=repo_root,
        check=False,
    )
    return result.returncode
