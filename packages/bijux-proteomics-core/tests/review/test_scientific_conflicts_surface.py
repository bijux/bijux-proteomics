# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review import (
    ScientificConflictFindingCode,
    ScientificWorkflowFamily,
    WorkflowScientificSnapshot,
    build_scientific_untrustworthy_checklists,
    evaluate_domain_conflicts,
)


def _snapshot(**updates: object) -> WorkflowScientificSnapshot:
    payload = {
        "workflow_id": "wf-conflict",
        "digested_peptide_count": 8,
        "digestion_issue_codes": (),
        "identified_protein_ids": ("P11111", "P22222"),
        "shared_peptide_group_count": 2,
        "quant_support_protein_ids": ("P11111",),
        "quant_missingness_fraction": 0.75,
        "quant_readiness_state": "blocked",
        "quant_blocking_reasons": ("multi_batch_shift",),
        "ptm_protein_ids": ("P11111",),
        "ambiguous_ptm_site_count": 1,
        "qc_blocking_issue_codes": ("identification_rate",),
        "review_candidate_ids": ("candidate-1",),
        "target_decoy_collision_count": 1,
        "external_engine_disagreement_count": 2,
        "decision_grade_requested": True,
    }
    payload.update(updates)
    return WorkflowScientificSnapshot.model_validate(payload)


def test_build_scientific_untrustworthy_checklists_covers_biggest_families() -> None:
    checklists = build_scientific_untrustworthy_checklists()

    assert {checklist.family for checklist in checklists} == {
        ScientificWorkflowFamily.DIGESTION,
        ScientificWorkflowFamily.IDENTIFICATION,
        ScientificWorkflowFamily.QUANTIFICATION,
        ScientificWorkflowFamily.PTM,
        ScientificWorkflowFamily.QC,
        ScientificWorkflowFamily.REVIEW_PROJECTION,
    }
    assert all(checklist.entries for checklist in checklists)


def test_evaluate_domain_conflicts_surfaces_all_hard_scientific_pressures() -> None:
    report = evaluate_domain_conflicts(_snapshot())

    assert {finding.code for finding in report.findings} == {
        ScientificConflictFindingCode.TARGET_DECOY_COLLISION,
        ScientificConflictFindingCode.SHARED_PEPTIDE_PRESSURE,
        ScientificConflictFindingCode.MISSING_CHANNEL_PRESSURE,
        ScientificConflictFindingCode.AMBIGUOUS_PTM_LOCALIZATION,
        ScientificConflictFindingCode.EXTERNAL_ENGINE_DISAGREEMENT,
    }
