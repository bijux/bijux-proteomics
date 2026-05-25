from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.governance.package_shape.public_symbol_ownership import (
    validate_public_symbol_ownership,
)
from bijux_proteomics_dev.governance.package_shape.scientific_concept_owners import (
    validate_scientific_concept_ownership,
)
from bijux_proteomics_dev.quality.architecture.agentic_compatibility_inventory import (
    validate_agentic_compatibility_inventory,
)
from bijux_proteomics_dev.quality.architecture.duplicate_model_ownership import (
    validate_duplicate_model_ownership,
)
from bijux_proteomics_dev.quality.architecture.package_substance import (
    validate_package_substance,
)

__all__ = [
    "SsotReadinessCheckResult",
    "SsotReadinessIssue",
    "build_ssot_readiness_report",
    "validate_ssot_readiness",
]


@dataclass(frozen=True)
class SsotReadinessCheckResult:
    """One SSOT readiness check result."""

    check_id: str
    issue_count: int
    ready: bool


@dataclass(frozen=True)
class SsotReadinessIssue:
    """One release-blocking SSOT readiness issue."""

    code: str
    detail: str


def _check_failures(repo_root: Path) -> tuple[tuple[str, tuple[str, ...]], ...]:
    return (
        (
            "public-symbol-ownership",
            tuple(issue.detail for issue in validate_public_symbol_ownership()),
        ),
        (
            "scientific-concept-ownership",
            tuple(
                issue.detail
                for issue in validate_scientific_concept_ownership()
            ),
        ),
        (
            "duplicate-model-ownership",
            tuple(
                issue.detail for issue in validate_duplicate_model_ownership(repo_root)
            ),
        ),
        (
            "compatibility-bridge",
            tuple(
                issue.detail
                for issue in validate_agentic_compatibility_inventory(repo_root)
            ),
        ),
        (
            "package-substance",
            tuple(issue.detail for issue in validate_package_substance(repo_root)),
        ),
    )


def build_ssot_readiness_report(
    repo_root: Path,
) -> tuple[SsotReadinessCheckResult, ...]:
    """Build the SSOT readiness report across ownership-critical checks."""

    return tuple(
        SsotReadinessCheckResult(
            check_id=check_id,
            issue_count=len(failures),
            ready=not failures,
        )
        for check_id, failures in _check_failures(repo_root)
    )


def validate_ssot_readiness(repo_root: Path) -> tuple[SsotReadinessIssue, ...]:
    """Validate that the suite-level SSOT ownership checks are clean."""

    issues = [
        SsotReadinessIssue(code=check_id, detail=detail)
        for check_id, failures in _check_failures(repo_root)
        for detail in failures
    ]
    return tuple(sorted(issues, key=lambda issue: (issue.code, issue.detail)))
