# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.judgment.benchmark_corpora import (
    BenchmarkDisposition,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_lab.benchmarks import (
    FlagshipFollowUpOutcomeBasis,
    FlagshipFollowUpOutcomeImpact,
    build_flagship_assay_worth_ledger,
    build_flagship_follow_up_outcome_dossier,
    build_flagship_follow_up_outcome_dossier_family,
    build_flagship_justified_but_low_yield_report,
    build_flagship_recommendation_revision_report,
    build_flagship_underestimated_but_useful_report,
)


def test_follow_up_outcome_dossier_family_covers_all_five_flagship_workflows() -> None:
    family = build_flagship_follow_up_outcome_dossier_family()

    assert family.family_id == "flagship-follow-up-outcome-dossiers"
    assert family.artifact_path.startswith("artifacts/")
    assert tuple(dossier.workflow_family for dossier in family.dossiers) == (
        KnowledgeWorkflowFamily.DDA,
        KnowledgeWorkflowFamily.DIA,
        KnowledgeWorkflowFamily.LFQ,
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.TARGETED,
    )


def test_targeted_outcome_dossier_keeps_requested_vs_observed_value_visible() -> None:
    dossier = build_flagship_follow_up_outcome_dossier(KnowledgeWorkflowFamily.TARGETED)

    assert dossier.outcome_basis is FlagshipFollowUpOutcomeBasis.BENCHMARK_SIMULATED
    assert dossier.requested_assay_ids == ("prm-assay", "orthogonal-assay")
    assert dossier.observed_assay_ids == ("prm-assay", "orthogonal-assay")
    assert dossier.matched_assay_ids == ("prm-assay", "orthogonal-assay")
    assert dossier.missing_requested_assay_ids == ()
    assert dossier.promoted_evidence_ids
    assert (
        dossier.initial_recommendation_disposition
        is BenchmarkDisposition.DO_NOT_RECOMMEND
    )
    assert (
        dossier.revised_recommendation_disposition
        is BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE
    )
    assert dossier.recommendation_changed is True
    assert dossier.worth_it is True
    assert dossier.final_decision_impact is FlagshipFollowUpOutcomeImpact.CALIBRATED


def test_dia_outcome_dossier_marks_low_yield_follow_up_honestly() -> None:
    dossier = build_flagship_follow_up_outcome_dossier(KnowledgeWorkflowFamily.DIA)

    assert dossier.blocked_assay_ids == ("dia-library-bridge",)
    assert dossier.missing_requested_assay_ids == ("dia-library-bridge",)
    assert dossier.weakened_assay_ids == ("dia-matrix-shift-repeat",)
    assert (
        dossier.revised_recommendation_disposition
        is BenchmarkDisposition.DO_NOT_RECOMMEND
    )
    assert dossier.worth_it is False
    assert dossier.looked_justified_initially is True
    assert dossier.early_block_signals


def test_assay_worth_ledger_ranks_useful_loops_ahead_of_low_yield_work() -> None:
    ledger = build_flagship_assay_worth_ledger()

    assert ledger.ledger_id == "flagship-assay-worth-ledger"
    assert ledger.artifact_path.startswith("artifacts/")
    assert ledger.entries[0].workflow_family is KnowledgeWorkflowFamily.TARGETED
    assert ledger.entries[0].worth_it is True
    assert {
        entry.workflow_family for entry in ledger.entries if entry.worth_it is False
    } == {
        KnowledgeWorkflowFamily.DIA,
        KnowledgeWorkflowFamily.LFQ,
    }
    assert all(
        ledger.entries[index].overall_value_score
        >= ledger.entries[index + 1].overall_value_score
        for index in range(len(ledger.entries) - 1)
    )


def test_revision_and_signal_reports_cover_strengthening_and_waste_cases() -> None:
    revisions = build_flagship_recommendation_revision_report()
    low_yield = build_flagship_justified_but_low_yield_report()
    underestimated = build_flagship_underestimated_but_useful_report()

    assert {entry.workflow_family for entry in revisions.entries} == {
        KnowledgeWorkflowFamily.DIA,
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.TARGETED,
    }
    assert {entry.workflow_family for entry in low_yield.entries} == {
        KnowledgeWorkflowFamily.DIA,
    }
    assert {entry.workflow_family for entry in underestimated.entries} == {
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.TARGETED,
    }
