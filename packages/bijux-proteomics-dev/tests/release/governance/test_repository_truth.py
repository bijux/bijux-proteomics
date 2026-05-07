from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.release.governance.repository_truth import (
    build_repository_truth_report,
    validate_repository_truth_report,
)

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_repository_truth_report_blocks_reference_grade_and_elite_claims_honestly() -> None:
    report = build_repository_truth_report(REPO_ROOT)

    assert report.canonical_workflow_undeniable is True
    assert report.reference_grade_claim_allowed is False
    assert report.elite_claim_allowed is False
    assert report.reopened_completion_claim_package_names == ()
    assert report.completion_claim_package_names == ()
    assert report.evidence_paths
    assert any(
        issue.code == "architectural-ready-floor-not-met"
        for issue in report.blockers
    )
    assert any(
        issue.code == "governance-freshness-stale-generated-governance-report"
        for issue in report.blockers
    )


def test_repository_truth_report_has_no_internal_consistency_failures() -> None:
    assert validate_repository_truth_report(REPO_ROOT) == ()
