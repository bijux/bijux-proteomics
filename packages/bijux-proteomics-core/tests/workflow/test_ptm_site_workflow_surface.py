# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    PtmEvidenceCardPolicy,
    PtmProteinCorrectionMode,
    PtmRegulatorEnrichmentPolicy,
)
from bijux_proteomics.workflow import build_ptm_site_workflow_bundle


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _ptm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _fasta_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "fasta" / name


def test_build_ptm_site_workflow_bundle_preserves_site_biology_from_file_inputs() -> (
    None
):
    report = build_ptm_site_workflow_bundle(
        _ptm_fixture("localization_results.tsv"),
        _fasta_fixture("ptm_sites.fasta"),
        feature_tsv_path=_ptm_fixture("ptm_features.tsv"),
        design_path=_ptm_fixture("ptm.design.tsv"),
        annotation_tsv_path=_ptm_fixture("ptm_site_annotations.tsv"),
        annotation_target_species="Homo sapiens",
        protein_correction_mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
        batch_field="",
        condition_a="control",
        condition_b="treated",
        regulator_enrichment_policy=PtmRegulatorEnrichmentPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.0,
        ),
        evidence_card_policy=PtmEvidenceCardPolicy(max_adjusted_p_value=1.0),
    )

    assert report.summary.total_evidence_row_count == 8
    assert report.summary.accepted_evidence_count == 8
    assert report.summary.rejected_evidence_count == 0
    assert report.experiment_design.summary.run_count == 4
    assert report.summary.protein_sequence_count == 3
    assert report.summary.feature_row_count == 12
    assert report.summary.design_row_count == 4
    assert report.summary.site_row_count == 5
    assert report.summary.localization_entry_count == 8
    assert report.summary.quantified_site_row_count == 3
    assert report.summary.differential_site_count == 3
    assert report.summary.motif_term_count >= 0
    assert report.summary.evidence_card_count == 3
    assert report.summary.narrative_claim_count == 3
    assert report.report.site_quantification is not None
    assert report.report.differential_analysis is not None
    assert report.report.evidence_cards is not None
    assert report.report.differential_analysis.protein_correction_mode.value == (
        "subtract_unmodified_protein"
    )


def test_build_ptm_site_workflow_bundle_preserves_rejected_evidence_review() -> None:
    report = build_ptm_site_workflow_bundle(
        _workflow_fixture("ptm_site_parse_issues.tsv"),
        _fasta_fixture("ptm_sites.fasta"),
        feature_tsv_path=_ptm_fixture("ptm_features.tsv"),
        design_path=_ptm_fixture("ptm.design.tsv"),
        batch_field="",
        condition_a="control",
        condition_b="treated",
    )

    assert report.summary.total_evidence_row_count == 2
    assert report.summary.accepted_evidence_count == 1
    assert report.summary.rejected_evidence_count == 1
    assert report.experiment_design.summary.condition_count == 2
    assert report.evidence_parse_report.rejected_rows[0].row_number == 3
    assert {
        issue.code for issue in report.evidence_parse_report.rejected_rows[0].issues
    } == {
        "invalid_charge",
        "missing_protein_refs",
    }
