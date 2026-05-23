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


def test_ptm_evidence_card_exports_preserve_cards_and_claim_links(tmp_path: Path) -> None:
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
        annotation_records=annotations.accepted_records,
        annotation_target_species="Homo sapiens",
        regulator_enrichment_policy=PtmRegulatorEnrichmentPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.0,
        ),
        evidence_card_policy=PtmEvidenceCardPolicy(max_adjusted_p_value=1.0),
    )

    manifest = export_ptm_report_bundle(report, tmp_path / "ptm_report")

    assert manifest.artifacts.evidence_card_summary_tsv is not None
    assert manifest.artifacts.evidence_card_tsv is not None
    assert manifest.artifacts.evidence_claim_tsv is not None
    assert "card_id" in (
        tmp_path / "ptm_report" / manifest.artifacts.evidence_card_tsv
    ).read_text()
    assert "claim_id\tcard_id\tsite_key\tclaim_kind\ttext" == (
        tmp_path / "ptm_report" / manifest.artifacts.evidence_claim_tsv
    ).read_text().splitlines()[0]
