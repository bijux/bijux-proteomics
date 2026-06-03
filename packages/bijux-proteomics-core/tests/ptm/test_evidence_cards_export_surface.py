# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
from typing import cast

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import (
    PtmEvidenceCardPolicy,
    PtmEvidenceCardReport,
    PtmPhosphositeSelectionPolicy,
    PtmProteinCorrectionMode,
    PtmRegulatorEnrichmentPolicy,
    build_ptm_differential_analysis_report,
    build_ptm_evidence_card_report,
    build_ptm_localization_scoring_report,
    build_ptm_mechanism_classification_report,
    build_ptm_ortholog_conservation_report,
    build_ptm_phosphosite_motif_enrichment_report,
    build_ptm_regulator_enrichment_report,
    build_ptm_site_annotation_mapping_report,
    build_ptm_site_quantification_report,
    build_ptm_site_table,
    export_ptm_evidence_card_summary_tsv,
    export_ptm_evidence_card_tsv,
    export_ptm_evidence_claim_tsv,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
    parse_ptm_ortholog_site_tsv,
    parse_ptm_site_annotation_tsv,
)
from bijux_proteomics.quantification import NormalizationMethod, parse_ms1_feature_table
from bijux_proteomics.sequences import (
    FastaParseMode,
    FastaParseReport,
    parse_fasta_document,
    parse_protein_region_context_tsv,
)


def _ptm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _protein_sequences() -> dict[str, str]:
    report = _protein_report()
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def _protein_report() -> FastaParseReport:
    fasta = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "fasta"
        / "ptm_sites.fasta"
    )
    return parse_fasta_document(fasta.read_text(), mode=FastaParseMode.STRICT)


def _build_evidence_card_report() -> PtmEvidenceCardReport:
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
    )
    annotations = parse_ptm_site_annotation_tsv(
        _ptm_fixture("ptm_site_annotations.tsv")
    )
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
    ortholog_sites = parse_ptm_ortholog_site_tsv(_ptm_fixture("ptm_ortholog_sites.tsv"))
    return cast(
        PtmEvidenceCardReport,
        build_ptm_evidence_card_report(
            evidence.accepted_records,
            site_table,
            localization,
        differential,
        site_quantification=site_quantification,
        motif_enrichment=motif_enrichment,
        regulator_enrichment=regulator_enrichment,
        annotation_mapping_report=annotation_mapping,
        mechanism_classification_report=build_ptm_mechanism_classification_report(
            differential
        ),
        ortholog_conservation_report=build_ptm_ortholog_conservation_report(
            site_table,
            ortholog_sites.accepted_records,
            source_species="Homo sapiens",
            target_species="Mus musculus",
        ),
        protein_records=_protein_report().accepted_records,
        protein_sequences=_protein_sequences(),
        protein_region_context_records=protein_regions.accepted_records,
            policy=PtmEvidenceCardPolicy(max_adjusted_p_value=1.0),
        ),
    )


def test_ptm_evidence_card_exports_preserve_cards_and_claim_links(
    tmp_path: Path,
) -> None:
    report = _build_evidence_card_report()

    summary_path = tmp_path / "ptm.evidence_cards.summary.tsv"
    cards_path = tmp_path / "ptm.evidence_cards.tsv"
    claims_path = tmp_path / "ptm.evidence_claims.tsv"
    export_ptm_evidence_card_summary_tsv(report, summary_path)
    export_ptm_evidence_card_tsv(report, cards_path)
    export_ptm_evidence_claim_tsv(report, claims_path)

    assert "functional_context_card_count" in summary_path.read_text()
    assert "crosstalk_supported_card_count" in summary_path.read_text()
    assert "mechanism_classified_card_count" in summary_path.read_text()
    assert "ortholog_context_card_count" in summary_path.read_text()
    assert "functional_regions" in cards_path.read_text()
    assert "mechanism_class" in cards_path.read_text()
    assert "crosstalk_partner_site_keys" in cards_path.read_text()
    assert "ortholog_conservation_status" in cards_path.read_text()
    assert "identity_level" in cards_path.read_text()
    assert (
        claims_path.read_text().splitlines()[0]
        == "claim_id\tcard_id\tsite_key\tclaim_kind\ttext\tsource_row_refs\tderived_no_source_reason"
    )
