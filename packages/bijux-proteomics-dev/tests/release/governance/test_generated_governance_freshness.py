from __future__ import annotations

from bijux_proteomics_dev.release.governance.generated_governance_freshness import (
    build_generated_governance_freshness_report,
    validate_generated_governance_freshness,
)


def test_generated_governance_freshness_report_covers_generated_reports() -> None:
    report = build_generated_governance_freshness_report()

    assert report.entries
    by_path = {entry.relative_path: entry for entry in report.entries}
    assert by_path["configs/package-governance/foundation-root-api.toml"].fresh is True
    assert (
        by_path["configs/package-governance/flagship-workflow-manifest.toml"].fresh
        is True
    )
    assert any(not entry.fresh for entry in report.entries)


def test_generated_governance_freshness_surfaces_release_blockers() -> None:
    issues = validate_generated_governance_freshness()

    assert issues
    assert not any(issue.code == "missing-regenerate-command" for issue in issues)
    assert any(issue.code == "stale-generated-governance-report" for issue in issues)
