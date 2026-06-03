# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import (
    GoEnrichmentCorrectionPolicy,
    apply_go_enrichment_multiple_testing,
    build_go_enrichment_report,
    parse_go_annotation_table,
    parse_protein_reference_table,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_apply_go_enrichment_multiple_testing_preserves_monotonic_adjusted_p_values() -> (
    None
):
    foreground = parse_protein_reference_table(_fixture_path("go_foreground.tsv"))
    background = parse_protein_reference_table(_fixture_path("go_background.tsv"))
    annotations = parse_go_annotation_table(_fixture_path("go_annotations.tsv"))

    report = apply_go_enrichment_multiple_testing(
        build_go_enrichment_report(
            foreground.accepted_entries,
            background.accepted_entries,
            annotations.accepted_records,
        ),
        policy=GoEnrichmentCorrectionPolicy(max_adjusted_p_value=0.6),
    )

    adjusted = [entry.adjusted_p_value for entry in report.term_entries]
    assert all(value is not None for value in adjusted)
    assert adjusted == sorted(adjusted)
    assert report.summary.enriched_term_count >= 1
    assert report.term_entries[0].adjusted_p_value is not None
