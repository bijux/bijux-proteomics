# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    PtmEvidenceCardPolicy,
    PtmPhosphositeSelectionPolicy,
    PtmProteinCorrectionMode,
    PtmRegulatorEnrichmentPolicy,
)
from bijux_proteomics.workflow.advanced_ptm import (
    AdvancedPtmWorkflowConfig,
    run_advanced_ptm_workflow,
)


def _ptm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _fasta_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "fasta" / name


def test_run_advanced_ptm_workflow_keeps_ambiguous_signal_out_of_exact_site_matrix(
    tmp_path: Path,
) -> None:
    report = run_advanced_ptm_workflow(
        AdvancedPtmWorkflowConfig(
            evidence_tsv_path=_ptm_fixture("localization_results.tsv"),
            proteins_fasta_path=_fasta_fixture("ptm_sites.fasta"),
            feature_tsv_path=_ptm_fixture("ptm_features.tsv"),
            design_tsv_path=_ptm_fixture("ptm.design.tsv"),
            output_dir=tmp_path / "advanced_ptm_review",
            annotation_tsv_path=_ptm_fixture("ptm_site_annotations.tsv"),
            annotation_target_species="Homo sapiens",
            protein_correction_mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
            batch_field="",
            condition_a="control",
            condition_b="treated",
            motif_selection_policy=PtmPhosphositeSelectionPolicy(
                max_adjusted_p_value=1.0,
                min_absolute_log2_fold_change=0.0,
            ),
            regulator_enrichment_policy=PtmRegulatorEnrichmentPolicy(
                max_adjusted_p_value=1.0,
                min_absolute_log2_fold_change=0.0,
            ),
            evidence_card_policy=PtmEvidenceCardPolicy(max_adjusted_p_value=1.0),
        )
    )

    output_dir = tmp_path / "advanced_ptm_review"
    exact_matrix_tsv = (
        output_dir / report.manifest.artifacts.exact_site_matrix_tsv
    ).read_text(encoding="utf-8")
    site_group_matrix_tsv = (
        output_dir / report.manifest.artifacts.ambiguity_group_matrix_tsv
    ).read_text(encoding="utf-8")
    excluded_tsv = (
        output_dir / report.manifest.artifacts.excluded_ambiguous_sites_tsv
    ).read_text(encoding="utf-8")
    occupancy_tsv = (
        output_dir / report.manifest.artifacts.occupancy_counterpart_tsv
    ).read_text(encoding="utf-8")
    differential_tsv = (
        output_dir / report.manifest.artifacts.differential_tsv
    ).read_text(encoding="utf-8")
    rejected_evidence_tsv = (
        output_dir / report.manifest.artifacts.rejected_evidence_tsv
    ).read_text(encoding="utf-8")

    assert report.summary.exact_site_row_count == 3
    assert report.summary.ambiguous_group_row_count == 2
    assert report.summary.excluded_ambiguous_row_count == 2
    assert report.summary.occupancy_entry_count == 10
    assert report.summary.motif_term_count >= 1
    assert report.summary.regulator_enrichment_entry_count >= 1
    assert report.summary.evidence_card_count >= 1
    assert report.summary.protein_correction_mode is (
        PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN
    )
    assert "P11111:S5:Phospho" in exact_matrix_tsv
    assert "P11111:S17:Phospho" not in exact_matrix_tsv
    assert "P11111:Phospho:17|18|19" in site_group_matrix_tsv
    assert "P11111:S17:Phospho\tP11111:Phospho:17|18|19" in excluded_tsv
    assert "counterpart_status" in occupancy_tsv
    assert "corrected_log2_fold_change" in differential_tsv
    assert "rejected_evidence_id\tsource_surface" in rejected_evidence_tsv
    assert report.manifest.artifacts.motif_term_tsv is not None
    assert report.manifest.artifacts.regulator_enrichment_tsv is not None
    assert report.manifest.artifacts.evidence_card_tsv is not None
    assert report.manifest.artifacts.evidence_claim_tsv is not None
    assert (output_dir / report.manifest.artifacts.site_mapping_tsv).exists()
    assert (output_dir / report.manifest.artifacts.localization_tsv).exists()
    assert (output_dir / report.manifest.artifacts.motif_term_tsv).exists()
    assert (output_dir / report.manifest.artifacts.regulator_enrichment_tsv).exists()
    assert (output_dir / report.manifest.artifacts.evidence_card_tsv).exists()
    assert (output_dir / report.manifest.artifacts.evidence_claim_tsv).exists()


def test_run_advanced_ptm_workflow_keeps_exclusion_audit_separate_from_group_quantification(
    tmp_path: Path,
) -> None:
    report = run_advanced_ptm_workflow(
        AdvancedPtmWorkflowConfig(
            evidence_tsv_path=_ptm_fixture("localization_results.tsv"),
            proteins_fasta_path=_fasta_fixture("ptm_sites.fasta"),
            feature_tsv_path=_ptm_fixture("ptm_features.tsv"),
            design_tsv_path=_ptm_fixture("ptm.design.tsv"),
            output_dir=tmp_path / "advanced_ptm_without_annotation",
            batch_field="",
            condition_a="control",
            condition_b="treated",
        )
    )

    assert report.ambiguity_group_quantification is not None
    assert report.exact_site_exclusion_audit.ambiguous_group_quantification is None
    assert report.exact_site_exclusion_audit.excluded_ambiguous_site_keys == (
        "P11111:S17:Phospho",
        "P22222:S4:Phospho",
    )
    assert report.manifest.artifacts.rejected_evidence_tsv == "rejected_evidence.tsv"
    assert report.manifest.artifacts.regulator_enrichment_tsv is None
    assert report.manifest.artifacts.ambiguity_group_summary_tsv is not None
    assert report.manifest.artifacts.ambiguity_group_matrix_tsv is not None
    assert report.manifest.artifacts.ambiguity_group_missingness_tsv is not None
