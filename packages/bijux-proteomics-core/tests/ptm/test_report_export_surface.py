# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import (
    PtmEvidenceCardPolicy,
    PtmPhosphositeSelectionPolicy,
    PtmProteinCorrectionMode,
    PtmRegulatorEnrichmentPolicy,
    build_ptm_report_bundle,
    export_ptm_report_bundle,
    parse_ptm_localization_tsv,
    parse_ptm_ortholog_site_tsv,
    parse_ptm_site_annotation_tsv,
)
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _ptm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _protein_sequences() -> dict[str, str]:
    fasta = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "fasta"
        / "ptm_sites.fasta"
    )
    report = parse_fasta_document(fasta.read_text(), mode=FastaParseMode.STRICT)
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def test_ptm_report_export_writes_required_tables_and_manifest(tmp_path: Path) -> None:
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    annotations = parse_ptm_site_annotation_tsv(_ptm_fixture("ptm_site_annotations.tsv"))
    ortholog_sites = parse_ptm_ortholog_site_tsv(_ptm_fixture("ptm_ortholog_sites.tsv"))
    design_entries = tuple(
        entry.model_copy(update={"batch": None})
        for entry in parse_experimental_design_table(
            _ptm_fixture("ptm.design.tsv")
        ).accepted_entries
    )
    report = build_ptm_report_bundle(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
        feature_records=features.accepted_records,
        design_entries=design_entries,
        protein_correction_mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
        batch_field="",
        motif_selection_policy=PtmPhosphositeSelectionPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.0,
        ),
        annotation_records=annotations.accepted_records,
        annotation_target_species="Homo sapiens",
        regulator_enrichment_policy=PtmRegulatorEnrichmentPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.0,
        ),
        ortholog_site_records=ortholog_sites.accepted_records,
        ortholog_source_species="Homo sapiens",
        ortholog_target_species="Mus musculus",
        evidence_card_policy=PtmEvidenceCardPolicy(max_adjusted_p_value=1.0),
    )

    manifest = export_ptm_report_bundle(report, tmp_path / "ptm_report")
    output_dir = tmp_path / "ptm_report"

    assert manifest.summary.accepted_evidence_count == 8
    assert manifest.summary.quantified_site_row_count == 3
    assert manifest.summary.differential_site_count == 3
    assert manifest.summary.ambiguous_group_row_count == 2
    assert manifest.summary.mechanism_classification_count == 3
    assert manifest.summary.ortholog_conservation_entry_count == 5
    assert manifest.motif_summary_included is True
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "inputs").is_dir()
    assert (output_dir / "qc").is_dir()
    assert (output_dir / "evidence").is_dir()
    assert (output_dir / "matrices").is_dir()
    assert (output_dir / "stats").is_dir()
    assert (output_dir / "biology").is_dir()
    assert (output_dir / "cards").is_dir()
    assert (output_dir / "reports").is_dir()
    assert (output_dir / "reports" / manifest.artifacts.summary_tsv).exists()
    assert (output_dir / "cards" / manifest.artifacts.evidence_card_tsv).exists()
    assert (output_dir / "matrices" / manifest.artifacts.site_quant_matrix_tsv).exists()
    assert (output_dir / "stats" / manifest.artifacts.differential_tsv).exists()
    assert (output_dir / manifest.artifacts.summary_tsv).exists()
    assert (output_dir / manifest.artifacts.peptide_tsv).exists()
    assert (output_dir / manifest.artifacts.site_tsv).exists()
    assert (output_dir / manifest.artifacts.localization_tsv).exists()
    assert (output_dir / manifest.artifacts.site_quant_matrix_tsv).exists()
    assert (output_dir / manifest.artifacts.site_group_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.site_group_matrix_tsv).exists()
    assert (output_dir / manifest.artifacts.site_group_missingness_tsv).exists()
    assert (output_dir / manifest.artifacts.differential_tsv).exists()
    assert (output_dir / manifest.artifacts.motif_term_tsv).exists()
    assert (output_dir / manifest.artifacts.regulator_enrichment_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.regulator_enrichment_tsv).exists()
    assert (output_dir / manifest.artifacts.mechanism_classification_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.mechanism_classification_tsv).exists()
    assert (output_dir / manifest.artifacts.ortholog_conservation_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.ortholog_conservation_tsv).exists()
    assert (output_dir / manifest.artifacts.evidence_card_tsv).exists()
    assert (output_dir / manifest.artifacts.evidence_claim_tsv).exists()
    assert (output_dir / manifest.artifacts.evidence_aware_ranking_tsv).exists()
    assert "S[Phospho]PEPTIDEK" in (
        output_dir / manifest.artifacts.peptide_tsv
    ).read_text()
    assert "P11111:S5:Phospho" in (
        output_dir / manifest.artifacts.site_tsv
    ).read_text()
    assert "probability_source" in (
        output_dir / manifest.artifacts.localization_tsv
    ).read_text()
    assert "P11111:S5:Phospho" in (
        output_dir / manifest.artifacts.site_quant_matrix_tsv
    ).read_text()
    assert "group_row_count" in (
        output_dir / manifest.artifacts.site_group_summary_tsv
    ).read_text()
    assert "group_key" in (
        output_dir / manifest.artifacts.site_group_matrix_tsv
    ).read_text()
    assert "sample_id" in (
        output_dir / manifest.artifacts.site_group_missingness_tsv
    ).read_text()
    assert "corrected_log2_fold_change" in (
        output_dir / manifest.artifacts.differential_tsv
    ).read_text()
    assert "exclusive_to_regulated" in (
        output_dir / manifest.artifacts.motif_term_tsv
    ).read_text()
    assert "evaluated_regulator_count" in (
        output_dir / manifest.artifacts.regulator_enrichment_summary_tsv
    ).read_text()
    assert "supporting_sites" in (
        output_dir / manifest.artifacts.regulator_enrichment_tsv
    ).read_text()
    assert "site_specific_count" in (
        output_dir / manifest.artifacts.mechanism_classification_summary_tsv
    ).read_text()
    assert "corrected_log2_fold_change" in (
        output_dir / manifest.artifacts.mechanism_classification_tsv
    ).read_text()
    assert "unmapped_site_count" in (
        output_dir / manifest.artifacts.ortholog_conservation_summary_tsv
    ).read_text()
    assert "status" in (
        output_dir / manifest.artifacts.ortholog_conservation_tsv
    ).read_text()
    assert "card_id" in (output_dir / manifest.artifacts.evidence_card_tsv).read_text()
    assert "claim_id" in (output_dir / manifest.artifacts.evidence_claim_tsv).read_text()
    assert "ptm_site" in (
        output_dir / manifest.artifacts.evidence_aware_ranking_tsv
    ).read_text()
