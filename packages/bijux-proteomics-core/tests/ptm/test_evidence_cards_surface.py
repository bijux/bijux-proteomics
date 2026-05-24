# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import (
    PtmEvidenceCardPolicy,
    PtmMotifComparisonPolicy,
    PtmPhosphositeSelectionPolicy,
    PtmProteinCorrectionMode,
    PtmRegulatorEnrichmentPolicy,
    build_ptm_differential_analysis_report,
    build_ptm_evidence_card_report,
    build_ptm_localization_scoring_report,
    build_ptm_phosphosite_motif_enrichment_report,
    build_ptm_regulator_enrichment_report,
    build_ptm_site_annotation_mapping_report,
    build_ptm_site_quantification_report,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
    parse_ptm_site_annotation_tsv,
)
from bijux_proteomics.quantification import NormalizationMethod, parse_ms1_feature_table
from bijux_proteomics.sequences import (
    FastaParseMode,
    parse_fasta_document,
    parse_protein_region_context_tsv,
)


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


def _build_evidence_card_report():
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    localization = build_ptm_localization_scoring_report(evidence.accepted_records)
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    site_quantification = build_ptm_site_quantification_report(
        site_table,
        feature_records=features.accepted_records,
    )
    design_entries = tuple(
        entry.model_copy(update={"batch": None})
        for entry in parse_experimental_design_table(
            _ptm_fixture("ptm.design.tsv")
        ).accepted_entries
    )
    differential = build_ptm_differential_analysis_report(
        site_quantification,
        design_entries,
        normalization_method=NormalizationMethod.MEDIAN,
        batch_field="",
        protein_correction_mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
        feature_records=features.accepted_records,
    )
    motif_enrichment = build_ptm_phosphosite_motif_enrichment_report(
        differential,
        protein_sequences=_protein_sequences(),
        selection_policy=PtmPhosphositeSelectionPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.0,
        ),
        comparison_policy=PtmMotifComparisonPolicy(),
    )
    annotations = parse_ptm_site_annotation_tsv(_ptm_fixture("ptm_site_annotations.tsv"))
    annotation_mapping = build_ptm_site_annotation_mapping_report(
        site_table,
        annotations.accepted_records,
        target_species="Homo sapiens",
    )
    regulator_enrichment = build_ptm_regulator_enrichment_report(
        differential.differential_report,
        annotation_mapping,
        policy=PtmRegulatorEnrichmentPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.0,
        ),
    )
    protein_regions = parse_protein_region_context_tsv(
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "sequences"
        / "protein_region_context.tsv"
    )
    return build_ptm_evidence_card_report(
        evidence.accepted_records,
        site_table,
        localization,
        differential,
        site_quantification=site_quantification,
        motif_enrichment=motif_enrichment,
        regulator_enrichment=regulator_enrichment,
        protein_region_context_records=protein_regions.accepted_records,
        policy=PtmEvidenceCardPolicy(max_adjusted_p_value=1.0),
    )


def test_ptm_evidence_cards_preserve_card_ids_claim_links_and_warnings() -> None:
    report = _build_evidence_card_report()

    assert report.summary.card_count == 3
    assert report.summary.narrative_claim_count == 3
    assert all(card.card_id.startswith("ptm-card-") for card in report.cards)
    assert all(card.claim_ids for card in report.cards)
    claim_card_ids = {claim.card_id for claim in report.narrative_claims}
    assert claim_card_ids == {card.card_id for card in report.cards}

    annotated = next(
        card
        for card in report.cards
        if card.site_key == "P11111:S5:Phospho"
    )
    low_localization = next(
        card
        for card in report.cards
        if card.site_key == "Q9DEC1:S5:Phospho"
    )

    assert annotated.motif_evidence.centered_windows
    assert annotated.functional_regions
    assert any(
        region.region_kind.value == "signal_peptide"
        for region in annotated.functional_regions
    )
    assert any(
        regulator.regulator == "AKT1" for regulator in annotated.regulator_evidence
    )
    assert annotated.claim_ids
    assert any(
        warning.code.value == "low_localization" for warning in low_localization.warnings
    )
    assert any(
        warning.code.value == "decoy_site" for warning in low_localization.warnings
    )
