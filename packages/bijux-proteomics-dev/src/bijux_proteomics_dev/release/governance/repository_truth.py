from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.governance.package_shape.package_readme_maturity import (
    PACKAGE_README_MATURITY_PATH,
    build_package_readme_maturity_report,
)
from bijux_proteomics_dev.governance.package_shape.package_reopened_completion_claims import (
    PACKAGE_REOPENED_COMPLETION_CLAIMS_PATH,
    build_package_reopened_completion_claim_report,
)
from bijux_proteomics_dev.governance.package_shape.package_scorecard import (
    PACKAGE_SCORECARD_PATH,
    build_package_scorecard_report,
)
from bijux_proteomics_dev.release.governance.generated_governance_freshness import (
    validate_generated_governance_freshness,
)
from bijux_proteomics_dev.release.governance.package_family_readiness import (
    build_package_family_readiness_reports,
)
from bijux_proteomics_dev.release.governance.scientific_readiness import (
    scientific_release_manifest_path,
    validate_scientific_release_dossier,
)
from bijux_proteomics_intelligence.candidates.ranking_benchmarks import (
    build_flagship_ranking_policy,
    build_legacy_ranking_policy,
    compare_ranking_policies_against_benchmark_corpus,
)
from bijux_proteomics_runtime.workflows.manifest import (
    CANONICAL_WORKFLOW_MANIFEST_PATH,
    validate_canonical_workflow_manifest,
)

__all__ = [
    "RepositoryTruthIssue",
    "RepositoryTruthReport",
    "build_repository_truth_report",
    "validate_repository_truth_report",
]


@dataclass(frozen=True)
class RepositoryTruthIssue:
    """One blocker on reference-grade or elite truth claims."""

    code: str
    detail: str


@dataclass(frozen=True)
class RepositoryTruthReport:
    """Repository-level truth posture for stronger scientific maturity claims."""

    canonical_workflow_undeniable: bool
    reference_grade_claim_allowed: bool
    elite_claim_allowed: bool
    architecturally_ready_package_count: int
    reopened_completion_claim_package_names: tuple[str, ...]
    completion_claim_package_names: tuple[str, ...]
    evidence_paths: tuple[str, ...]
    blockers: tuple[RepositoryTruthIssue, ...]


def build_repository_truth_report(repo_root: Path) -> RepositoryTruthReport:
    """Build the repository-level truth posture for stronger maturity claims."""

    scorecard = build_package_scorecard_report()
    reopened = build_package_reopened_completion_claim_report()
    maturity = build_package_readme_maturity_report()
    family_reports = build_package_family_readiness_reports(repo_root)
    workflow_manifest_issues = validate_canonical_workflow_manifest(repo_root=repo_root)
    scientific_dossier_issues = validate_scientific_release_dossier(repo_root)
    freshness_issues = validate_generated_governance_freshness()
    ranking_improvement = compare_ranking_policies_against_benchmark_corpus(
        build_legacy_ranking_policy(),
        build_flagship_ranking_policy(),
    )

    architecturally_ready_package_count = sum(
        entry.architectural_ready for entry in scorecard.entries
    )
    reopened_packages = tuple(
        entry.distribution_name
        for entry in reopened.entries
        if entry.reopened_completion_claim
    )
    completion_claim_packages = tuple(
        entry.distribution_name
        for entry in maturity.entries
        if entry.completion_claims_while_not_ready
    )
    canonical_workflow_undeniable = (
        not workflow_manifest_issues and ranking_improvement.decision_improved
    )

    blockers: list[RepositoryTruthIssue] = []
    for issue in workflow_manifest_issues:
        blockers.append(
            RepositoryTruthIssue(
                code=f"canonical-workflow-{issue.code}",
                detail=issue.detail,
            )
        )
    for issue in scientific_dossier_issues:
        blockers.append(
            RepositoryTruthIssue(
                code=f"scientific-release-{issue.code}",
                detail=issue.detail,
            )
        )
    for issue in freshness_issues:
        blockers.append(
            RepositoryTruthIssue(
                code=f"governance-freshness-{issue.code}",
                detail=issue.detail,
            )
        )
    if reopened_packages:
        blockers.append(
            RepositoryTruthIssue(
                code="reopened-completion-claims-block-reference-grade",
                detail=(
                    "reference-grade posture remains blocked by reopened completion claims in "
                    + ", ".join(reopened_packages)
                ),
            )
        )
    if completion_claim_packages:
        blockers.append(
            RepositoryTruthIssue(
                code="completion-claims-while-not-ready",
                detail=(
                    "packages still claim completion while architectural-ready is false: "
                    + ", ".join(completion_claim_packages)
                ),
            )
        )
    if architecturally_ready_package_count < len(scorecard.entries):
        blockers.append(
            RepositoryTruthIssue(
                code="architectural-ready-floor-not-met",
                detail=(
                    f"only {architecturally_ready_package_count}/{len(scorecard.entries)} packages are architectural-ready"
                ),
            )
        )
    if any(not report.ready for report in family_reports):
        blocked_families = tuple(
            report.family_id for report in family_reports if not report.ready
        )
        blockers.append(
            RepositoryTruthIssue(
                code="release-family-readiness-blocked",
                detail="release families still blocked: " + ", ".join(blocked_families),
            )
        )
    if not ranking_improvement.decision_improved:
        blockers.append(
            RepositoryTruthIssue(
                code="ranking-benchmark-proof-missing",
                detail=(
                    "flagship ranking policy does not yet outperform the legacy baseline "
                    f"on corpus {ranking_improvement.corpus_id}"
                ),
            )
        )

    reference_grade_claim_allowed = canonical_workflow_undeniable and not blockers
    elite_claim_allowed = (
        reference_grade_claim_allowed
        and architecturally_ready_package_count == len(scorecard.entries)
    )
    return RepositoryTruthReport(
        canonical_workflow_undeniable=canonical_workflow_undeniable,
        reference_grade_claim_allowed=reference_grade_claim_allowed,
        elite_claim_allowed=elite_claim_allowed,
        architecturally_ready_package_count=architecturally_ready_package_count,
        reopened_completion_claim_package_names=reopened_packages,
        completion_claim_package_names=completion_claim_packages,
        evidence_paths=(
            CANONICAL_WORKFLOW_MANIFEST_PATH.relative_to(repo_root).as_posix(),
            PACKAGE_SCORECARD_PATH.relative_to(repo_root).as_posix(),
            PACKAGE_REOPENED_COMPLETION_CLAIMS_PATH.relative_to(repo_root).as_posix(),
            PACKAGE_README_MATURITY_PATH.relative_to(repo_root).as_posix(),
            scientific_release_manifest_path(repo_root).relative_to(repo_root).as_posix(),
            "artifacts/intelligence/ranking-benchmarks/reviewable-ranking-corpus.json",
            "artifacts/intelligence/ranking-benchmarks/flagship-reviewable-ranking.json",
        ),
        blockers=tuple(blockers),
    )


def validate_repository_truth_report(
    repo_root: Path,
) -> tuple[RepositoryTruthIssue, ...]:
    """Validate repository truth posture for stronger release language."""

    report = build_repository_truth_report(repo_root)
    issues: list[RepositoryTruthIssue] = []
    if report.reference_grade_claim_allowed and not report.canonical_workflow_undeniable:
        issues.append(
            RepositoryTruthIssue(
                code="reference-grade-without-undeniable-workflow",
                detail=(
                    "reference-grade posture must not be allowed before one workflow is undeniable"
                ),
            )
        )
    if report.elite_claim_allowed and not report.reference_grade_claim_allowed:
        issues.append(
            RepositoryTruthIssue(
                code="elite-without-reference-grade",
                detail="elite posture must remain stricter than reference-grade posture",
            )
        )
    return tuple(issues)
