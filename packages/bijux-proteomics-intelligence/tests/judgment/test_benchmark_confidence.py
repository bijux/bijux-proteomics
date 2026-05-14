# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.judgment.benchmark_confidence import (
    build_workflow_overconfidence_audit,
    build_workflow_underconfidence_audit,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)


def test_overconfidence_audit_keeps_hidden_reveal_debt_visible() -> None:
    audit = build_workflow_overconfidence_audit()

    assert audit.audit_id == "flagship-workflow-overconfidence-audit"
    assert audit.artifact_path.startswith("artifacts/")
    targeted = next(
        entry
        for entry in audit.entries
        if entry.workflow_family is KnowledgeWorkflowFamily.TARGETED
    )
    assert targeted.overconfidence_rate == 2 / 3
    assert targeted.counterfactual_refusal_count == 3
    assert targeted.certainty_ahead_of_evidence is True


def test_underconfidence_audit_can_publish_zero_without_hiding_reason() -> None:
    audit = build_workflow_underconfidence_audit()

    assert audit.audit_id == "flagship-workflow-underconfidence-audit"
    assert audit.artifact_path.startswith("artifacts/")
    assert all(entry.underconfidence_rate == 0.0 for entry in audit.entries)
    assert all(entry.unnecessarily_weakened is False for entry in audit.entries)
