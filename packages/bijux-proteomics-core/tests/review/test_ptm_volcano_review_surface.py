# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import (
    PtmProteinCorrectionMode,
    build_ptm_differential_analysis_report,
    build_ptm_site_quantification_report,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.quantification import NormalizationMethod, parse_ms1_feature_table
from bijux_proteomics.review import VolcanoReviewPolicy, build_ptm_volcano_review
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


def test_build_ptm_volcano_review_preserves_raw_p_values_and_labels() -> None:
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
    report = build_ptm_differential_analysis_report(
        site_quantification,
        design.accepted_entries,
        normalization_method=NormalizationMethod.MEDIAN,
        feature_records=features.accepted_records,
        protein_correction_mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
        batch_field="",
    )

    review = build_ptm_volcano_review(
        report.volcano_plot,
        policy=VolcanoReviewPolicy(top_label_count=1),
    )

    assert review.source_kind.value == "ptm"
    assert review.labeled_point_count == 1
    assert any(point.raw_p_value > 0.0 for point in review.points)
    assert sum(1 for point in review.points if point.top_labeled) == 1
