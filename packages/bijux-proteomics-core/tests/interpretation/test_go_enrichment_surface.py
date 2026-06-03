# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import (
    build_go_enrichment_report,
    parse_go_annotation_table,
    parse_protein_reference_table,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_build_go_enrichment_report_evaluates_term_overlap_against_background() -> None:
    foreground = parse_protein_reference_table(_fixture_path("go_foreground.tsv"))
    background = parse_protein_reference_table(_fixture_path("go_background.tsv"))
    annotations = parse_go_annotation_table(_fixture_path("go_annotations.tsv"))

    report = build_go_enrichment_report(
        foreground.accepted_entries,
        background.accepted_entries,
        annotations.accepted_records,
    )

    assert report.summary.foreground_size == 3
    assert report.summary.background_size == 6
    assert report.summary.evaluated_term_count == 3
    assert report.summary.foreground_annotated_count == 3
    assert report.summary.background_annotated_count == 5
    assert report.summary.unannotated_background_count == 1

    top_entry = report.term_entries[0]
    assert top_entry.go_term_id == "GO:0006915"
    assert top_entry.foreground_overlap_count == 2
    assert top_entry.background_term_count == 2
    assert top_entry.foreground_protein_refs == ("P04637", "Q99999")
    assert top_entry.enrichment_ratio is not None
    assert top_entry.enrichment_ratio > 1.0
    assert top_entry.p_value < 1.0
    assert any(
        entry.set_role == "background" and entry.protein_ref == "Q88888"
        for entry in report.unannotated_proteins
    )
