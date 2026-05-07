# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.comparator_confrontations import (
    ComparatorConfrontationOutcome,
    build_workflow_comparator_confrontation,
    build_workflow_comparator_confrontation_report,
)


def test_comparator_confrontation_report_currently_covers_dda_and_dia() -> None:
    report = build_workflow_comparator_confrontation_report()

    assert {entry.workflow_family for entry in report.entries} == {
        KnowledgeWorkflowFamily.DDA,
        KnowledgeWorkflowFamily.DIA,
        KnowledgeWorkflowFamily.LFQ,
        KnowledgeWorkflowFamily.MULTIPLEX,
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.TARGETED,
    }


def test_dda_comparator_confrontation_keeps_peptide_protein_calibration_and_review_axes() -> (
    None
):
    confrontation = build_workflow_comparator_confrontation(KnowledgeWorkflowFamily.DDA)

    assert confrontation.benchmark_id == "benchmark:dda_search_reproducibility"
    assert len(confrontation.findings) == 4
    assert {
        finding.axis for finding in confrontation.findings
    } == {
        "peptide-level evidence",
        "protein-level evidence",
        "calibration and live-engine parity",
        "downstream review behavior",
    }
    assert any(
        finding.outcome is ComparatorConfrontationOutcome.REPO_WEAKER
        for finding in confrontation.findings
    )


def test_dia_comparator_confrontation_keeps_missingness_behavior_explicit() -> None:
    confrontation = build_workflow_comparator_confrontation(KnowledgeWorkflowFamily.DIA)

    missingness = next(
        finding
        for finding in confrontation.findings
        if finding.axis == "missingness and absent-expected-peptide behavior"
    )

    assert missingness.outcome is ComparatorConfrontationOutcome.REPO_WEAKER
    assert "missing expected peptides" in missingness.repository_position.lower()
    assert confrontation.artifact_refs


def test_lfq_comparator_confrontation_keeps_normalization_differential_and_loss_axes() -> (
    None
):
    confrontation = build_workflow_comparator_confrontation(KnowledgeWorkflowFamily.LFQ)

    assert {finding.axis for finding in confrontation.findings} == {
        "normalization behavior",
        "differential interpretation",
        "evidence-loss behavior",
    }
    assert any(
        finding.outcome is ComparatorConfrontationOutcome.REPO_STRICTER
        for finding in confrontation.findings
    )


def test_multiplex_comparator_confrontation_keeps_blocked_channel_path_visible() -> (
    None
):
    confrontation = build_workflow_comparator_confrontation(
        KnowledgeWorkflowFamily.MULTIPLEX
    )

    blocked = next(
        finding
        for finding in confrontation.findings
        if finding.axis == "channel-level evidence"
    )

    assert blocked.outcome is ComparatorConfrontationOutcome.BLOCKED
    assert "blocked" in blocked.scientific_difference.lower()


def test_ptm_comparator_confrontation_keeps_localization_and_ambiguity_split() -> (
    None
):
    confrontation = build_workflow_comparator_confrontation(KnowledgeWorkflowFamily.PTM)

    assert {finding.axis for finding in confrontation.findings} == {
        "localization agreement",
        "ambiguity divergence",
        "downstream consequence differences",
    }
    assert any(
        finding.outcome is ComparatorConfrontationOutcome.REPO_STRICTER
        for finding in confrontation.findings
    )


def test_targeted_comparator_confrontation_admits_calibration_and_interference_loss() -> (
    None
):
    confrontation = build_workflow_comparator_confrontation(
        KnowledgeWorkflowFamily.TARGETED
    )

    weaker_axes = {
        finding.axis
        for finding in confrontation.findings
        if finding.outcome is ComparatorConfrontationOutcome.REPO_WEAKER
    }

    assert weaker_axes == {
        "calibration behavior",
        "interference conclusions",
    }
    assert "Skyline-class" in confrontation.next_escalation
