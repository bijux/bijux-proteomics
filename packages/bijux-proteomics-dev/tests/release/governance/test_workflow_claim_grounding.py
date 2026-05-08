from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from bijux_proteomics_knowledge.references.workflows.claim_grounding import (
    ScientificClaimSeverity,
)
from bijux_proteomics_dev.release.governance.workflow_claim_grounding import (
    WorkflowClaimGroundingIssue,
    validate_workflow_claim_grounding,
)

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_workflow_claim_grounding_matches_current_docs_and_packets() -> None:
    assert validate_workflow_claim_grounding(REPO_ROOT) == ()


def test_workflow_claim_grounding_blocks_threshold_exceeding_unsupported_claims(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.workflow_claim_grounding.build_workflow_unsupported_claim_ledger",
        lambda workflow_family: SimpleNamespace(
            threshold_blocking_severities=(
                ScientificClaimSeverity.MEDIUM,
                ScientificClaimSeverity.HIGH,
            ),
            entries=(
                SimpleNamespace(
                    scientific_severity=ScientificClaimSeverity.HIGH,
                    claim_text="dangerously unsupported public claim",
                ),
            ),
        ),
    )

    issues = validate_workflow_claim_grounding(REPO_ROOT)

    assert WorkflowClaimGroundingIssue(
        code="unsupported-claim-threshold-exceeded",
        detail=(
            "dda still has high unsupported claim language: "
            "dangerously unsupported public claim"
        ),
    ) in issues
