from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_intelligence.reviews.external_review_kits import (
    build_workflow_external_review_kit_family,
)
from bijux_proteomics_intelligence.reviews.public_scrutiny import (
    build_public_artifact_index,
    build_trust_break_page,
    build_trust_next_page,
)
from bijux_proteomics_dev.release.governance.benchmark_rerun_governance import (
    validate_black_box_benchmark_language,
)
from bijux_proteomics_dev.release.governance.public_language import (
    validate_public_language,
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


def validate_workflow_public_scrutiny(
    repo_root: Path,
) -> tuple[WorkflowPublicScrutinyIssue, ...]:
    """Validate public scrutiny surfaces and stronger release language boundaries."""

    issues: list[WorkflowPublicScrutinyIssue] = []
    index = build_public_artifact_index()
    break_page = build_trust_break_page()
    next_page = build_trust_next_page()
    kit_family = build_workflow_external_review_kit_family()

    if len(index.entries) < 17:
        issues.append(
            WorkflowPublicScrutinyIssue(
                code="public-artifact-index-too-thin",
                detail=(
                    "public artifact index is thinner than the current flagship outsider surface requires"
                ),
            )
        )
    if len({entry.entry_id for entry in index.entries}) != len(index.entries):
        issues.append(
            WorkflowPublicScrutinyIssue(
                code="public-artifact-index-duplicate-entry-id",
                detail="public artifact index contains duplicate entry identifiers",
            )
        )
    if not break_page.entries:
        issues.append(
            WorkflowPublicScrutinyIssue(
                code="trust-break-page-empty",
                detail="the trust-break page must name concrete fragility conditions",
            )
        )
    if not next_page.entries:
        issues.append(
            WorkflowPublicScrutinyIssue(
                code="trust-next-page-empty",
                detail="the trust-next page must name concrete strengthening paths",
            )
        )
    for kit in kit_family.kits:
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
    for issue in validate_black_box_benchmark_language():
        issues.append(
            WorkflowPublicScrutinyIssue(code=issue.code, detail=issue.detail)
        )
    for issue in validate_public_language(repo_root):
        issues.append(
            WorkflowPublicScrutinyIssue(code=issue.code, detail=issue.detail)
        )
    return tuple(issues)
