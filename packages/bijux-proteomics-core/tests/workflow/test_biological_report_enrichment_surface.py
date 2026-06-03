# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.workflow import build_biological_result_report_bundle


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_build_biological_result_report_bundle_preserves_annotation_and_enrichment() -> (
    None
):
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    report = build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        go_annotation_tsv_path=_fixture("biological_report_go.tsv"),
        pathway_membership_tsv_path=_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_fixture("biological_report_complexes.tsv"),
        condition_a="control",
        condition_b="treatment",
    )

    assert report.summary.annotation_entry_count == 5
    assert report.summary.annotation_unmapped_count == 0
    assert report.annotation_report.mapped_entries[0].gene_symbol is not None
    assert report.go_enrichment_report is not None
    assert report.go_enrichment_report.summary.enriched_term_count == 1
    assert report.pathway_activity_report is not None
    assert report.pathway_activity_report.summary.pathway_count == 1
    assert report.pathway_activity_report.summary.condition_comparison_count == 1
    assert report.pathway_enrichment_report is not None
    assert report.pathway_enrichment_report.summary.enriched_entry_count == 1
    assert report.complex_activity_report is not None
    assert report.complex_activity_report.summary.complex_count == 1
    assert report.complex_activity_report.summary.condition_comparison_count == 1
    assert report.complex_enrichment_report is not None
    assert report.complex_enrichment_report.summary.enriched_entry_count == 1
