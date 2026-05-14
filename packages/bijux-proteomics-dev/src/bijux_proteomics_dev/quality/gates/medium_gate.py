"""Curated medium gate for integrated reproducibility and governance checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess  # nosec B404
import sys

from bijux_proteomics_dev.quality.artifacts.artifact_schemas import (
    validate_high_value_artifact_schemas,
)
from bijux_proteomics_dev.quality.artifacts.benchmark_artifacts import (
    validate_benchmark_artifact_definitions,
)
from bijux_proteomics_dev.quality.artifacts.bundle_verification import (
    validate_bundle_verification_profiles,
)
from bijux_proteomics_dev.quality.dependencies.dependency_boundaries import (
    validate_workspace_dependency_boundaries,
)
from bijux_proteomics_dev.release.governance.package_family_readiness import (
    validate_package_family_readiness,
)

__all__ = [
    "MediumGateTarget",
    "default_medium_gate_targets",
    "render_medium_gate_pytest_args",
    "run_medium_gate",
    "validate_medium_gate",
]


@dataclass(frozen=True)
class MediumGateTarget:
    """One curated medium-gate target spanning multiple package seams."""

    surface: str
    test_path: str
    rationale: str


def default_medium_gate_targets() -> tuple[MediumGateTarget, ...]:
    """Return the curated medium-gate targets for integrated repository integrity."""
    return (
        MediumGateTarget(
            surface="workflow-reproducibility",
            test_path="packages/bijux-proteomics-runtime/tests/workflows/test_workflow_runs_surface.py",
            rationale="prove runtime export, archive, and rerun contracts stay reproducible",
        ),
        MediumGateTarget(
            surface="evidence-integrity",
            test_path="packages/bijux-proteomics-knowledge/tests/memory/test_evidence_bundle.py",
            rationale="prove governed evidence and trust surfaces remain coherent",
        ),
        MediumGateTarget(
            surface="runtime-service",
            test_path="packages/bijux-proteomics-runtime/tests/api/test_document_contract_surfaces.py",
            rationale="prove runtime contract publication and service surfaces stay aligned",
        ),
        MediumGateTarget(
            surface="package-boundaries",
            test_path="packages/bijux-proteomics-dev/tests/quality/dependencies/test_dependency_boundaries.py",
            rationale="prove package-boundary discipline does not drift under integration pressure",
        ),
    )


def validate_medium_gate(repo_root: Path) -> list[str]:
    """Validate medium-gate test targets and integrated governance prerequisites."""
    failures: list[str] = []
    expected_surfaces = {
        "workflow-reproducibility",
        "evidence-integrity",
        "runtime-service",
        "package-boundaries",
    }
    surfaces = {target.surface for target in default_medium_gate_targets()}
    if surfaces != expected_surfaces:
        failures.append(
            f"medium gate surfaces changed from {sorted(expected_surfaces)} to {sorted(surfaces)}"
        )
    for target in default_medium_gate_targets():
        if not (repo_root / target.test_path).exists():
            failures.append(f"missing medium gate target: {target.test_path}")
    failures.extend(
        issue.detail for issue in validate_workspace_dependency_boundaries(repo_root)
    )
    failures.extend(
        issue.detail for issue in validate_high_value_artifact_schemas(repo_root)
    )
    failures.extend(
        issue.detail for issue in validate_bundle_verification_profiles(repo_root)
    )
    failures.extend(
        issue.detail for issue in validate_benchmark_artifact_definitions(repo_root)
    )
    failures.extend(
        issue.detail for issue in validate_package_family_readiness(repo_root)
    )
    return failures


def render_medium_gate_pytest_args(repo_root: Path) -> list[str]:
    """Render the absolute pytest target list for the curated medium gate."""
    return [
        str(repo_root / target.test_path) for target in default_medium_gate_targets()
    ]


def run_medium_gate(repo_root: Path, *, execute: bool = False) -> int:
    """Validate or execute the curated medium gate."""
    failures = validate_medium_gate(repo_root)
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    if not execute:
        return 0
    result = subprocess.run(  # nosec B603
        [sys.executable, "-m", "pytest", *render_medium_gate_pytest_args(repo_root)],
        cwd=repo_root,
        check=False,
    )
    return result.returncode
