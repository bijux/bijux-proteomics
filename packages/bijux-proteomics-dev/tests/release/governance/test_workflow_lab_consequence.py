from __future__ import annotations

from types import SimpleNamespace

import pytest

from bijux_proteomics_dev.release.governance.workflow_lab_consequence import (
    WorkflowLabConsequenceIssue,
    validate_workflow_lab_consequence,
)
from bijux_proteomics_intelligence.reviews.workflow_authority import (
    WorkflowAuthorityKind,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)


def test_workflow_lab_consequence_allows_current_shipped_evidence() -> None:
    assert validate_workflow_lab_consequence() == ()


def test_workflow_lab_consequence_blocks_missing_outcome_and_ledger_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.workflow_lab_consequence.build_workflow_authority_matrix",
        lambda: SimpleNamespace(
            rows=(
                SimpleNamespace(
                    workflow_family=KnowledgeWorkflowFamily.DDA,
                    cells=(
                        SimpleNamespace(
                            authority_kind=WorkflowAuthorityKind.LAB_CONSEQUENTIAL,
                            earned=True,
                            artifact_paths=(
                                "packages/bijux-proteomics-lab/src/bijux_proteomics_lab/benchmarks/follow_up.py",
                            ),
                        ),
                    ),
                ),
            )
        ),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.workflow_lab_consequence.build_flagship_follow_up_outcome_dossier_family",
        lambda: SimpleNamespace(dossiers=()),
    )
    monkeypatch.setattr(
        "bijux_proteomics_dev.release.governance.workflow_lab_consequence.build_flagship_assay_worth_ledger",
        lambda: SimpleNamespace(entries=(), artifact_path="artifacts/lab/flagship-follow-up-outcomes/assay_worth_ledger.json"),
    )

    issues = validate_workflow_lab_consequence()

    assert WorkflowLabConsequenceIssue(
        code="lab-consequential-without-outcome-dossier",
        detail=(
            "dda is called lab-consequential without a shipped requested-versus-observed outcome dossier"
        ),
    ) in issues
    assert WorkflowLabConsequenceIssue(
        code="lab-consequential-without-worth-ledger",
        detail=(
            "dda is called lab-consequential without a shipped assay-worth-it ledger row"
        ),
    ) in issues
