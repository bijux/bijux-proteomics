from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.release.governance.benchmark_rerun_governance import (
    validate_black_box_benchmark_language,
)
from bijux_proteomics_dev.release.governance.public_artifact_governance import (
    validate_public_artifact_governance,
)
from bijux_proteomics_dev.release.governance.public_language import (
    validate_public_language,
)
from bijux_proteomics_intelligence.reviews.workflow_authority import (
    WorkflowAuthorityKind,
    build_workflow_authority_matrix,
)
from bijux_proteomics_intelligence.reviews.external_review_kits import (
    build_workflow_external_review_kit_family,
)

__all__ = [
    "WorkflowPublicScrutinyIssue",
    "validate_workflow_public_scrutiny",
]


@dataclass(frozen=True)
class WorkflowPublicScrutinyIssue:
    """One mismatch between public scrutiny surfaces and release language."""

    code: str
    detail: str


_BANNED_RELEASE_PHRASES: tuple[str, ...] = (
    "scientifically credible",
    "scientifically reliable",
    "reliable scientific authority",
)

_PUBLIC_LANGUAGE_PATHS: tuple[Path, ...] = (
    Path("README.md"),
    Path("docs/01-bijux-proteomics/foundation/flagship-release-candidate.md"),
    Path("docs/01-bijux-proteomics/foundation/elite-readiness-scorecard.md"),
    Path("docs/08-bijux-proteomics-maintain/bijux-proteomics-dev/release-support.md"),
)


def _read_target_doc(repo_root: Path, relative_path: Path) -> str:
    return (repo_root / relative_path).read_text(encoding="utf-8")


def _earned_outsider_auditable_workflow_families() -> frozenset[str]:
    matrix = build_workflow_authority_matrix()
    return frozenset(
        row.workflow_family.value
        for row in matrix.rows
        if any(
            cell.authority_kind == WorkflowAuthorityKind.OUTSIDER_AUDITABLE
            and cell.earned
            for cell in row.cells
        )
    )


def validate_workflow_public_scrutiny(
    repo_root: Path,
) -> tuple[WorkflowPublicScrutinyIssue, ...]:
    """Validate public scrutiny surfaces and stronger release language boundaries."""

    issues: list[WorkflowPublicScrutinyIssue] = []
    kit_family = build_workflow_external_review_kit_family()
    outsider_auditable_workflow_families = _earned_outsider_auditable_workflow_families()
    for issue in validate_public_artifact_governance():
        issues.append(WorkflowPublicScrutinyIssue(code=issue.code, detail=issue.detail))
    for kit in kit_family.kits:
        if kit.workflow_family.value not in outsider_auditable_workflow_families:
            continue
        if not kit.standalone_verifier_report.verified:
            issues.append(
                WorkflowPublicScrutinyIssue(
                    code="external-review-kit-not-standalone-verifiable",
                    detail=(
                        f"{kit.workflow_family.value} external review kit does not survive standalone verification"
                    ),
                )
            )
        if not kit.ready_for_outsider_review:
            issues.append(
                WorkflowPublicScrutinyIssue(
                    code="external-review-kit-not-ready",
                    detail=(
                        f"{kit.workflow_family.value} external review kit is not ready for outsider review"
                    ),
                )
            )
    for relative_path in _PUBLIC_LANGUAGE_PATHS:
        text = _read_target_doc(repo_root, relative_path).lower()
        for phrase in _BANNED_RELEASE_PHRASES:
            if phrase in text:
                issues.append(
                    WorkflowPublicScrutinyIssue(
                        code="banned-strong-release-language",
                        detail=(
                            f"{relative_path.as_posix()} still uses banned stronger language: {phrase}"
                        ),
                    )
                )
    for benchmark_language_issue in validate_black_box_benchmark_language():
        issues.append(
            WorkflowPublicScrutinyIssue(
                code=benchmark_language_issue.code,
                detail=benchmark_language_issue.detail,
            )
        )
    for public_language_issue in validate_public_language(repo_root):
        issues.append(
            WorkflowPublicScrutinyIssue(
                code=public_language_issue.code,
                detail=public_language_issue.detail,
            )
        )
    return tuple(issues)
