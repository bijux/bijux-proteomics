# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics.benchmarks.flagship_acceptance import (
    AcceptanceReleaseLanguage,
    AcceptanceThresholdChangeDirection,
    build_flagship_acceptance_dashboard,
    build_flagship_acceptance_history_ledger,
    build_flagship_acceptance_rationale_dossier,
    build_flagship_acceptance_sheet,
    list_flagship_acceptance_sheets,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_flagship_acceptance_surface_starts_with_dda_and_dia() -> None:
    sheets = list_flagship_acceptance_sheets()
    sheet_by_family = {sheet.workflow_family: sheet for sheet in sheets}

    assert tuple(sheet.workflow_family for sheet in sheets) == (
        KnowledgeWorkflowFamily.DDA,
        KnowledgeWorkflowFamily.DIA,
        KnowledgeWorkflowFamily.LFQ,
        KnowledgeWorkflowFamily.MULTIPLEX,
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.TARGETED,
    )
    assert sheet_by_family[KnowledgeWorkflowFamily.DDA].acceptance_passed is True
    assert sheet_by_family[KnowledgeWorkflowFamily.DIA].acceptance_passed is True
    assert sheet_by_family[KnowledgeWorkflowFamily.LFQ].acceptance_passed is False
    assert sheet_by_family[KnowledgeWorkflowFamily.MULTIPLEX].acceptance_passed is False
    assert sheet_by_family[KnowledgeWorkflowFamily.PTM].acceptance_passed is True
    assert sheet_by_family[KnowledgeWorkflowFamily.TARGETED].acceptance_passed is True
    assert (
        sheet_by_family[KnowledgeWorkflowFamily.DDA].earned_release_language
        is AcceptanceReleaseLanguage.OUTSIDER_AUDITABLE_BOUNDED
    )
    assert (
        sheet_by_family[KnowledgeWorkflowFamily.DIA].earned_release_language
        is AcceptanceReleaseLanguage.OUTSIDER_AUDITABLE_BOUNDED
    )
    assert (
        sheet_by_family[KnowledgeWorkflowFamily.LFQ].earned_release_language
        is AcceptanceReleaseLanguage.REVIEW_GRADE_BOUNDED
    )
    assert (
        sheet_by_family[KnowledgeWorkflowFamily.MULTIPLEX].earned_release_language
        is AcceptanceReleaseLanguage.INTERNAL_SUPPORT_ONLY
    )
    assert (
        sheet_by_family[KnowledgeWorkflowFamily.PTM].earned_release_language
        is AcceptanceReleaseLanguage.OUTSIDER_AUDITABLE_BOUNDED
    )
    assert (
        sheet_by_family[KnowledgeWorkflowFamily.TARGETED].earned_release_language
        is AcceptanceReleaseLanguage.OUTSIDER_AUDITABLE_BOUNDED
    )


def test_dda_acceptance_sheet_keeps_decoy_and_comparator_thresholds_explicit() -> None:
    sheet = build_flagship_acceptance_sheet(KnowledgeWorkflowFamily.DDA)
    criteria = {criterion.criterion_id: criterion for criterion in sheet.criteria}

    assert sheet.claim_ahead_of_evidence is False
    assert criteria["dda_search_coverage"].observed_value == "2"
    assert criteria["dda_calibration_sanity"].observed_value == "1"
    assert criteria["dda_comparator_divergence_tolerance"].observed_value == "advisory"


def test_dia_acceptance_sheet_keeps_library_and_absent_expected_thresholds_explicit() -> (
    None
):
    sheet = build_flagship_acceptance_sheet(KnowledgeWorkflowFamily.DIA)
    criteria = {criterion.criterion_id: criterion for criterion in sheet.criteria}

    assert sheet.claim_ahead_of_evidence is False
    assert criteria["dia_library_dependence"].observed_value == "0.67"
    assert criteria["dia_peptide_evidence_coverage"].observed_value == "4"
    assert criteria["dia_quantitative_coherence"].observed_value == "0.33"


def test_lfq_acceptance_sheet_keeps_repeatability_and_promotion_thresholds_explicit() -> (
    None
):
    sheet = build_flagship_acceptance_sheet(KnowledgeWorkflowFamily.LFQ)
    criteria = {criterion.criterion_id: criterion for criterion in sheet.criteria}

    assert sheet.acceptance_passed is False
    assert sheet.claim_ahead_of_evidence is True
    assert (
        sheet.earned_release_language is AcceptanceReleaseLanguage.REVIEW_GRADE_BOUNDED
    )
    assert criteria["lfq_missingness_burden"].observed_value == "4"
    assert criteria["lfq_normalization_drift"].observed_value == "decision_grade"
    assert criteria["lfq_differential_reproducibility"].observed_value == "24"


def test_multiplex_acceptance_sheet_fails_and_keeps_internal_support_only_honest() -> (
    None
):
    sheet = build_flagship_acceptance_sheet(KnowledgeWorkflowFamily.MULTIPLEX)
    criteria = {criterion.criterion_id: criterion for criterion in sheet.criteria}

    assert sheet.acceptance_passed is False
    assert sheet.claim_ahead_of_evidence is False
    assert (
        sheet.earned_release_language is AcceptanceReleaseLanguage.INTERNAL_SUPPORT_ONLY
    )
    assert criteria["multiplex_interference"].observed_value == "2"
    assert criteria["multiplex_channel_dropout"].observed_value == "1"
    assert criteria["multiplex_ratio_compression"].observed_value == "2"
    assert criteria["multiplex_downstream_review_promotion"].observed_value == "refused"


def test_ptm_acceptance_sheet_keeps_ambiguity_and_family_scope_thresholds_explicit() -> (
    None
):
    sheet = build_flagship_acceptance_sheet(KnowledgeWorkflowFamily.PTM)
    criteria = {criterion.criterion_id: criterion for criterion in sheet.criteria}

    assert sheet.acceptance_passed is True
    assert sheet.claim_ahead_of_evidence is False
    assert criteria["ptm_localization_quality"].observed_value == "5"
    assert criteria["ptm_ambiguity_burden"].observed_value == "2"
    assert criteria["ptm_motif_credibility"].observed_value == "2"
    assert criteria["ptm_occupancy_stability"].observed_value == "4"


def test_targeted_acceptance_sheet_keeps_follow_up_promotion_thresholds_explicit() -> (
    None
):
    sheet = build_flagship_acceptance_sheet(KnowledgeWorkflowFamily.TARGETED)
    criteria = {criterion.criterion_id: criterion for criterion in sheet.criteria}

    assert sheet.acceptance_passed is True
    assert sheet.claim_ahead_of_evidence is False
    assert criteria["targeted_calibration_quality"].observed_value == "1"
    assert criteria["targeted_transition_interference"].observed_value == "1"
    assert criteria["targeted_heavy_light_coherence"].observed_value == "1"
    assert criteria["targeted_carryover_posture"].observed_value == "0"
    assert criteria["targeted_follow_up_promotion"].observed_value == "supported"


def test_published_acceptance_json_matches_live_surface() -> None:
    for sheet in list_flagship_acceptance_sheets():
        payload = json.loads(
            (REPO_ROOT / sheet.artifact_path).read_text(encoding="utf-8")
        )
        assert payload["sheet_id"] == sheet.sheet_id
        assert payload["workflow_family"] == sheet.workflow_family.value
        assert payload["acceptance_passed"] is sheet.acceptance_passed


def test_acceptance_dashboard_marks_multiplex_as_internal_support_only() -> None:
    dashboard = build_flagship_acceptance_dashboard()
    rows = {row.workflow_family: row for row in dashboard.rows}

    assert dashboard.artifact_path.endswith("acceptance_dashboard.json")
    assert rows[KnowledgeWorkflowFamily.DDA].claim_ahead_of_evidence is False
    assert rows[KnowledgeWorkflowFamily.MULTIPLEX].acceptance_passed is False
    assert rows[KnowledgeWorkflowFamily.MULTIPLEX].earned_release_language is (
        AcceptanceReleaseLanguage.INTERNAL_SUPPORT_ONLY
    )
    assert rows[KnowledgeWorkflowFamily.MULTIPLEX].failing_criteria


def test_acceptance_history_ledger_tracks_initial_threshold_publication() -> None:
    ledger = build_flagship_acceptance_history_ledger()

    assert ledger.artifact_path.endswith("benchmark_history_ledger.json")
    assert len(ledger.entries) == 30
    assert all(
        entry.change_direction is AcceptanceThresholdChangeDirection.INITIAL_PUBLISHED
        for entry in ledger.entries
    )


def test_acceptance_rationale_dossier_ties_thresholds_to_real_evidence() -> None:
    dossier = build_flagship_acceptance_rationale_dossier()

    assert dossier.artifact_path.endswith("acceptance_rationale_dossier.json")
    assert len(dossier.entries) == 30
    assert any(
        "challenge evidence is part of this threshold"
        in entry.benchmark_difficulty_basis
        for entry in dossier.entries
        if entry.workflow_family is not KnowledgeWorkflowFamily.MULTIPLEX
    )
    assert all(entry.evidence_paths for entry in dossier.entries)
