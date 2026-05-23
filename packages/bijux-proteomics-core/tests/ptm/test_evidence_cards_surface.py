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
    build_ptm_report_bundle,
    parse_ptm_localization_tsv,
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


def test_ptm_evidence_cards_preserve_card_ids_claim_links_and_warnings() -> None:
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    design_entries = parse_experimental_design_table(
        _ptm_fixture("ptm.design.tsv")
    ).accepted_entries
    annotations = parse_ptm_site_annotation_tsv(
        _ptm_fixture("ptm_site_annotations.tsv")
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
        motif_comparison_policy=PtmMotifComparisonPolicy(),
        annotation_records=annotations.accepted_records,
        annotation_target_species="Homo sapiens",
        regulator_enrichment_policy=PtmRegulatorEnrichmentPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.0,
        ),
        evidence_card_policy=PtmEvidenceCardPolicy(max_adjusted_p_value=1.0),
    )

    assert report.evidence_cards is not None
    assert report.summary.evidence_card_count == 3
    assert report.summary.narrative_claim_count == 3
    assert all(card.card_id.startswith("ptm-card-") for card in report.evidence_cards.cards)
    assert all(card.claim_ids for card in report.evidence_cards.cards)
    claim_card_ids = {claim.card_id for claim in report.evidence_cards.narrative_claims}
    assert claim_card_ids == {card.card_id for card in report.evidence_cards.cards}

    annotated = next(
        card
        for card in report.evidence_cards.cards
        if card.site_key == "P11111:S5:Phospho"
    )
    low_localization = next(
        card
        for card in report.evidence_cards.cards
        if card.site_key == "Q9DEC1:S5:Phospho"
    )

    assert annotated.motif_evidence.centered_windows
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
