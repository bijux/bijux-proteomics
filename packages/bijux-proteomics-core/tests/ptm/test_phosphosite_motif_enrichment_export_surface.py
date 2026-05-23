# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import (
    PtmMotifComparisonPolicy,
    PtmMotifRegulationDirection,
    PtmPhosphositeSelectionPolicy,
    build_ptm_differential_analysis_report,
    build_ptm_phosphosite_motif_enrichment_report,
    build_ptm_site_quantification_report,
    build_ptm_site_table,
    export_ptm_phosphosite_motif_enriched_term_tsv,
    export_ptm_phosphosite_motif_frequency_tsv,
    export_ptm_phosphosite_motif_logo_tsv,
    export_ptm_phosphosite_motif_window_tsv,
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


def test_ptm_phosphosite_motif_export_surfaces_preserve_windows_terms_and_logo() -> (
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
        comparison_policy=PtmMotifComparisonPolicy(
            min_frequency_difference=0.1,
            min_enrichment_ratio=1.0,
            max_reported_term_count=10,
        ),
    )

    export_ptm_phosphosite_motif_window_tsv(report, Path("ptm.motif.windows.tsv"))
    export_ptm_phosphosite_motif_frequency_tsv(report, Path("ptm.motif.frequency.tsv"))
    export_ptm_phosphosite_motif_enriched_term_tsv(
        report,
        Path("ptm.motif.terms.tsv"),
    )
    export_ptm_phosphosite_motif_logo_tsv(report, Path("ptm.motif.logo.tsv"))

    assert Path("ptm.motif.windows.tsv").read_text().splitlines()[0] == (
        "site_key\tprotein_ref\tresidue\tposition\tmodification_name\twindow_role\t"
        "direction\tcentered_window\tflank_size\tplotted_log2_fold_change\t"
        "adjusted_p_value\tambiguous\tprotein_correction_mode"
    )
    assert Path("ptm.motif.frequency.tsv").read_text().splitlines()[0] == (
        "position_offset\tresidue\tregulated_window_count\tbackground_window_count\t"
        "regulated_frequency\tbackground_frequency"
    )
    assert "1\tP\t1\t0" in Path("ptm.motif.terms.tsv").read_text()
    assert "regulated\t1\tP\t1\t1\t1" in Path("ptm.motif.logo.tsv").read_text()
