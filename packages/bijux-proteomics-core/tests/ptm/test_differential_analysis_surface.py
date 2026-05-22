# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import (
    build_ptm_differential_analysis_report,
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


def _site_quantification():
    evidence = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(_fixture_path("ptm_features.tsv"))
    return build_ptm_site_quantification_report(
        site_table,
        feature_records=features.accepted_records,
    )


def test_ptm_differential_analysis_reports_regulated_site_changes() -> None:
    site_quantification = _site_quantification()
    design = parse_experimental_design_table(_fixture_path("ptm.design.tsv"))

    report = build_ptm_differential_analysis_report(
        site_quantification,
        design.accepted_entries,
        normalization_method=NormalizationMethod.MEDIAN,
    )

    assert report.design_matrix.sample_count == 4
    assert report.differential_report.condition_a == "control"
    assert report.differential_report.condition_b == "treated"
    target = next(
        entry
        for entry in report.differential_report.entries
        if entry.site_key == "P11111:S5:Phospho"
    )

    assert target.observations_a == 2
    assert target.observations_b == 2
    assert target.log2_fold_change > 0.0
    assert target.adjusted_p_value is not None
    assert target.localized_peptides == ("S[Phospho]PEPTIDEK",)
    volcano_target = next(
        point
        for point in report.volcano_plot.points
        if point.site_key == "P11111:S5:Phospho"
    )
    assert report.volcano_plot.condition_a == "control"
    assert report.volcano_plot.condition_b == "treated"
    assert volcano_target.log2_fold_change == target.log2_fold_change
    assert volcano_target.negative_log10_adjusted_p_value >= 0.0
