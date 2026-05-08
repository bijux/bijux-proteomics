from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics_dev.release.governance.workflow_intelligence_confidence import (
    WorkflowIntelligenceConfidenceIssue,
    validate_workflow_intelligence_confidence,
)

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_workflow_intelligence_confidence_allows_current_docs_and_packets() -> None:
    assert validate_workflow_intelligence_confidence(REPO_ROOT) == ()


def test_workflow_intelligence_confidence_blocks_missing_audits_for_claimed_family(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.workflow_intelligence_confidence._doc_contains_decision_grade_intelligence",
        lambda repo_root, workflow_family: workflow_family.value == "dda",
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.workflow_intelligence_confidence._packet_contains_decision_grade_intelligence",
        lambda workflow_family: False,
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.workflow_intelligence_confidence.build_workflow_overconfidence_audit",
        lambda: type("Audit", (), {"entries": ()})(),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.workflow_intelligence_confidence.build_workflow_underconfidence_audit",
        lambda: type("Audit", (), {"entries": ()})(),
    )

    issues = validate_workflow_intelligence_confidence(REPO_ROOT)

    assert WorkflowIntelligenceConfidenceIssue(
        code="decision-grade-intelligence-without-overconfidence-audit",
        detail=(
            "dda uses decision-grade intelligence language without a published "
            "overconfidence audit row"
        ),
    ) in issues
    assert WorkflowIntelligenceConfidenceIssue(
        code="decision-grade-intelligence-without-underconfidence-audit",
        detail=(
            "dda uses decision-grade intelligence language without a published "
            "underconfidence audit row"
        ),
    ) in issues
