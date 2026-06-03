# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import (
    PtmMotifBackgroundMode,
    PtmMotifComparisonPolicy,
    PtmMotifRegulationDirection,
    PtmPhosphositeSelectionPolicy,
    build_ptm_differential_analysis_report,
    build_ptm_phosphosite_motif_enrichment_report,
    build_ptm_site_quantification_report,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.quantification import NormalizationMethod, parse_ms1_feature_table
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _fixture_path(name: str) -> Path:
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


def test_phosphosite_motif_enrichment_selects_regulated_sites_and_centered_windows() -> (
    None
):
    evidence = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(_fixture_path("ptm_features.tsv"))
    site_quantification = build_ptm_site_quantification_report(
        site_table,
        feature_records=features.accepted_records,
    )
    design = parse_experimental_design_table(_fixture_path("ptm.design.tsv"))
    differential = build_ptm_differential_analysis_report(
        site_quantification,
        design.accepted_entries,
        normalization_method=NormalizationMethod.MEDIAN,
        batch_field="",
    )

    report = build_ptm_phosphosite_motif_enrichment_report(
        differential,
        protein_sequences=_protein_sequences(),
        flank_size=3,
        selection_policy=PtmPhosphositeSelectionPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.5,
            direction=PtmMotifRegulationDirection.UPREGULATED,
        ),
    )

    assert report.condition_a == "control"
    assert report.condition_b == "treated"
    assert report.background_mode is PtmMotifBackgroundMode.OBSERVED_SITE_BACKGROUND
    assert report.regulated_site_count == 1
    assert report.background_site_count >= 1
    regulated = report.regulated_windows[0]
    assert regulated.site_key == "P11111:S5:Phospho"
    assert regulated.centered_window == "AAASPEP"
    assert regulated.direction is PtmMotifRegulationDirection.UPREGULATED
    assert any(
        term.position_offset == 1
        and term.residue == "P"
        and term.exclusive_to_regulated
        for term in report.enriched_terms
    )
    assert any(
        datum.window_role == "regulated"
        and datum.position_offset == 1
        and datum.residue == "P"
        for datum in report.logo_data
    )


def test_phosphosite_motif_enrichment_separates_observed_and_whole_proteome_backgrounds() -> (
    None
):
    evidence = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(_fixture_path("ptm_features.tsv"))
    site_quantification = build_ptm_site_quantification_report(
        site_table,
        feature_records=features.accepted_records,
    )
    design = parse_experimental_design_table(_fixture_path("ptm.design.tsv"))
    differential = build_ptm_differential_analysis_report(
        site_quantification,
        design.accepted_entries,
        normalization_method=NormalizationMethod.MEDIAN,
        batch_field="",
    )

    observed_background = build_ptm_phosphosite_motif_enrichment_report(
        differential,
        protein_sequences=_protein_sequences(),
        flank_size=3,
        selection_policy=PtmPhosphositeSelectionPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.5,
            direction=PtmMotifRegulationDirection.UPREGULATED,
        ),
        comparison_policy=PtmMotifComparisonPolicy(
            background_mode=PtmMotifBackgroundMode.OBSERVED_SITE_BACKGROUND,
        ),
    )
    proteome_background = build_ptm_phosphosite_motif_enrichment_report(
        differential,
        protein_sequences=_protein_sequences(),
        flank_size=3,
        selection_policy=PtmPhosphositeSelectionPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.5,
            direction=PtmMotifRegulationDirection.UPREGULATED,
        ),
        comparison_policy=PtmMotifComparisonPolicy(
            background_mode=PtmMotifBackgroundMode.WHOLE_PROTEOME_BACKGROUND,
        ),
    )

    assert (
        observed_background.background_mode
        is PtmMotifBackgroundMode.OBSERVED_SITE_BACKGROUND
    )
    assert (
        proteome_background.background_mode
        is PtmMotifBackgroundMode.WHOLE_PROTEOME_BACKGROUND
    )
    assert (
        observed_background.background_site_count
        != proteome_background.background_site_count
    )
    assert (
        proteome_background.background_site_count
        > observed_background.background_site_count
    )
