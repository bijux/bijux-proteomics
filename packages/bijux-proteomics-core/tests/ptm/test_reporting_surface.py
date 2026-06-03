# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.io.formats.proteomics_formats import ExperimentalDesignEntry
from bijux_proteomics.ptm import (
    PtmEvidenceCardPolicy,
    PtmPhosphositeSelectionPolicy,
    PtmProteinCorrectionMode,
    PtmRegulatorEnrichmentPolicy,
    build_ptm_report_bundle,
    parse_ptm_localization_tsv,
    parse_ptm_ortholog_site_tsv,
    parse_ptm_site_annotation_tsv,
    render_ptm_report_differential_tsv,
    render_ptm_report_evidence_aware_ranking_tsv,
    render_ptm_report_localization_tsv,
    render_ptm_report_peptide_tsv,
    render_ptm_report_site_quant_matrix_tsv,
    render_ptm_report_summary_tsv,
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


def _design_entries() -> tuple[ExperimentalDesignEntry, ...]:
    return tuple(
        entry.model_copy(update={"batch": None})
        for entry in parse_experimental_design_table(
            _ptm_fixture("ptm.design.tsv")
        ).accepted_entries
    )


def test_ptm_report_bundle_builds_core_peptide_and_site_surfaces() -> None:
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))

    report = build_ptm_report_bundle(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )

    assert report.summary.accepted_evidence_count == 8
    assert report.summary.peptide_entry_count == 8
    assert report.summary.site_row_count == 5
    assert report.summary.ambiguous_site_count == 2
    assert report.summary.ambiguous_group_row_count == 0
    assert report.summary.modified_peptide_count == 3
    assert report.summary.localization_entry_count == 8
    assert report.summary.evidence_card_count == 0
    assert report.summary.narrative_claim_count == 0
    assert report.summary.mechanism_classification_count == 0
    assert report.summary.ortholog_conservation_entry_count == 0
    assert any(
        entry.localized_peptide == "S[Phospho]PEPTIDEK"
        for entry in report.peptide_entries
    )
    assert any(entry.site_key == "P11111:S5:Phospho" for entry in report.site_table)


def test_ptm_report_bundle_renderers_keep_peptide_and_localization_sections_explicit() -> (
    None
):
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))

    report = build_ptm_report_bundle(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
        fragment_ion_support_by_spectrum={
            "scan=ptm-001": ("b5", "y7"),
            "scan=ptm-005": ("b2",),
        },
    )

    summary_lines = render_ptm_report_summary_tsv(report).splitlines()
    peptide_lines = render_ptm_report_peptide_tsv(report).splitlines()
    localization_lines = render_ptm_report_localization_tsv(report).splitlines()

    assert summary_lines[0] == (
        "accepted_evidence_count\tpeptide_entry_count\tsite_row_count\t"
        "ambiguous_site_count\tambiguous_group_row_count\tmodified_peptide_count\tlocalization_entry_count\t"
        "quantified_site_row_count\tdifferential_site_count\tmotif_term_count\t"
        "evidence_card_count\tnarrative_claim_count\tmechanism_classification_count\tortholog_conservation_entry_count"
    )
    assert peptide_lines[0].startswith(
        "spectrum_id\tsample_id\tlocalized_peptide\tcanonical_peptide"
    )
    assert any("S[Phospho]PEPTIDEK" in line for line in peptide_lines)
    assert localization_lines[0].startswith(
        "spectrum_id\tsample_id\tlocalized_peptide\tcanonical_peptide\tmodification_name"
    )


def test_ptm_report_bundle_adds_quantified_and_differential_sections() -> None:
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    annotations = parse_ptm_site_annotation_tsv(
        _ptm_fixture("ptm_site_annotations.tsv")
    )
    ortholog_sites = parse_ptm_ortholog_site_tsv(_ptm_fixture("ptm_ortholog_sites.tsv"))

    report = build_ptm_report_bundle(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
        feature_records=features.accepted_records,
        design_entries=_design_entries(),
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

    assert report.summary.quantified_site_row_count == 3
    assert report.summary.differential_site_count == 3
    assert report.summary.ambiguous_group_row_count == 2
    assert report.summary.evidence_card_count == 3
    assert report.summary.narrative_claim_count == 3
    assert report.summary.mechanism_classification_count == 3
    assert report.summary.ortholog_conservation_entry_count == 5
    assert report.site_quantification is not None
    assert report.differential_analysis is not None
    assert report.mechanism_classification is not None
    assert report.evidence_cards is not None
    assert report.evidence_aware_ranking_report is not None
    assert report.mechanism_classification.summary.site_specific_count == 1
    assert report.ortholog_conservation is not None
    assert report.ortholog_conservation.summary.unmapped_site_count == 2
    assert report.evidence_cards.cards[0].mechanism_classification is not None
    assert report.evidence_cards.cards[0].ortholog_conservation is not None
    assert report.differential_analysis.protein_correction_mode.value == (
        "subtract_unmodified_protein"
    )
    assert "P11111:S5:Phospho" in render_ptm_report_site_quant_matrix_tsv(report)
    assert "P11111:S5:Phospho" in render_ptm_report_differential_tsv(report)
    assert "priority_rank" in render_ptm_report_evidence_aware_ranking_tsv(report)
