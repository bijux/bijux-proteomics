# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import (
    apply_go_enrichment_multiple_testing,
    build_go_enrichment_report,
    parse_go_annotation_table,
    parse_protein_reference_table,
    render_go_enrichment_summary_tsv,
    render_go_enrichment_term_tsv,
    render_go_enrichment_unannotated_tsv,
    render_rejected_go_annotation_tsv,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_go_enrichment_renderers_emit_summary_term_and_unannotated_ledgers() -> None:
    foreground = parse_protein_reference_table(_fixture_path("go_foreground.tsv"))
    background = parse_protein_reference_table(_fixture_path("go_background.tsv"))
    annotations = parse_go_annotation_table(_fixture_path("go_annotations.tsv"))
    report = apply_go_enrichment_multiple_testing(
        build_go_enrichment_report(
            foreground.accepted_entries,
            background.accepted_entries,
            annotations.accepted_records,
        )
    )

    summary_tsv = render_go_enrichment_summary_tsv(report)
    term_tsv = render_go_enrichment_term_tsv(report)
    unannotated_tsv = render_go_enrichment_unannotated_tsv(report)
    rejected_tsv = render_rejected_go_annotation_tsv(annotations)

    assert summary_tsv.splitlines()[0].startswith("foreground_size\tbackground_size")
    assert "GO:0006915" in term_tsv
    assert "background\tQ88888" in unannotated_tsv
    assert "duplicate GO membership for P04637 and GO:0006915" in rejected_tsv
