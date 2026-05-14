# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.evidence_sufficiency import (
    WorkflowEvidenceTrustTier,
    build_workflow_evidence_sufficiency_rubric,
    list_workflow_evidence_sufficiency_rubrics,
)


def test_workflow_evidence_sufficiency_rubrics_cover_each_family() -> None:
    rubrics = list_workflow_evidence_sufficiency_rubrics()

    assert {rubric.workflow_family for rubric in rubrics} == set(
        KnowledgeWorkflowFamily
    )


def test_workflow_evidence_sufficiency_rubric_marks_targeted_cross_check_as_blocked() -> (
    None
):
    rubric = build_workflow_evidence_sufficiency_rubric(
        KnowledgeWorkflowFamily.TARGETED
    )

    cross_check = next(
        check
        for check in rubric.checks
        if check.tier is WorkflowEvidenceTrustTier.EXTERNALLY_CROSS_CHECKED
    )

    assert cross_check.satisfied is True
    assert cross_check.missing_requirements == ()


def test_workflow_evidence_sufficiency_rubric_keeps_current_authorized_tier_bounded() -> (
    None
):
    rubric = build_workflow_evidence_sufficiency_rubric(KnowledgeWorkflowFamily.DDA)

    assert rubric.current_authorized_tier in {
        WorkflowEvidenceTrustTier.BENCHMARK_BACKED,
        WorkflowEvidenceTrustTier.EXTERNALLY_CROSS_CHECKED,
        WorkflowEvidenceTrustTier.DECISION_GRADE,
    }
    assert "release wording" in rubric.note.lower()


def test_dda_evidence_sufficiency_rubric_no_longer_demands_mini_study_replacement() -> (
    None
):
    rubric = build_workflow_evidence_sufficiency_rubric(KnowledgeWorkflowFamily.DDA)

    benchmark_backed = next(
        check
        for check in rubric.checks
        if check.tier is WorkflowEvidenceTrustTier.BENCHMARK_BACKED
    )

    assert benchmark_backed.satisfied is True
    assert benchmark_backed.missing_requirements == ()
