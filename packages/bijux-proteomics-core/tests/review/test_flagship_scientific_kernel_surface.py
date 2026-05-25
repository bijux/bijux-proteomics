# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review.flagship_kernel import (
    ScientificCoverageBoundaryState,
    build_flagship_scientific_kernel_report,
)
from bijux_proteomics.review.scientific_story import WorkflowScientificSnapshot


def test_build_flagship_scientific_kernel_report_exposes_narrow_scope_boundaries() -> (
    None
):
    report = build_flagship_scientific_kernel_report(
        WorkflowScientificSnapshot(
            workflow_id="flagship-a",
            digested_peptide_count=18,
            identified_protein_ids=("P11111", "P22222"),
            shared_peptide_group_count=0,
            quant_support_protein_ids=("P11111",),
            quant_missingness_fraction=0.25,
            quant_readiness_state="decision_ready",
            ptm_protein_ids=("P11111",),
            ambiguous_ptm_site_count=0,
            review_candidate_ids=("candidate-1",),
            target_decoy_collision_count=0,
            external_engine_disagreement_count=0,
        )
    )

    assert report.kernel_ready is True
    assert report.artifact_path.startswith("artifacts/")
    assert {
        entry.capability_id: entry.state for entry in report.coverage_boundaries
    } == {
        "glycopeptide_support": ScientificCoverageBoundaryState.BOUNDARY_ONLY,
        "library_search_support": ScientificCoverageBoundaryState.BOUNDARY_ONLY,
        "external_engine_behavior": ScientificCoverageBoundaryState.BOUNDARY_ONLY,
    }
    assert "narrow workflow family" in report.note


def test_build_flagship_scientific_kernel_report_collects_blocking_reasons() -> None:
    report = build_flagship_scientific_kernel_report(
        WorkflowScientificSnapshot(
            workflow_id="flagship-b",
            digested_peptide_count=0,
            identified_protein_ids=("P11111",),
            shared_peptide_group_count=1,
            quant_support_protein_ids=("P11111", "Q99999"),
            quant_missingness_fraction=0.7,
            quant_readiness_state="review_only",
            quant_blocking_reasons=("multi_batch_shift",),
            ptm_protein_ids=("P11111",),
            ambiguous_ptm_site_count=1,
            qc_blocking_issue_codes=("identification_rate",),
            target_decoy_collision_count=1,
            external_engine_disagreement_count=0,
            decision_grade_requested=True,
        )
    )

    assert report.kernel_ready is False
    assert {
        "empty_digestion_space",
        "quant_support_outside_identification",
        "decision_grade_with_qc_blockers",
        "decision_grade_with_quant_blockers",
        "decision_grade_with_high_missingness",
        "decision_grade_with_ambiguous_ptm",
        "target_decoy_collision",
    } <= set(report.blocked_reasons)
