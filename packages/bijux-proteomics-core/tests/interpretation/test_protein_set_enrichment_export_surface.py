# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import (
    ProteinSetEnrichmentMissingBackgroundPolicy,
    ProteinSetEnrichmentPolicy,
    build_protein_set_enrichment_report,
    parse_protein_reference_table,
    parse_protein_set_table,
    render_protein_set_enrichment_summary_tsv,
    render_protein_set_enrichment_tsv,
    render_protein_set_universe_gap_tsv,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_protein_set_enrichment_renderers_emit_summary_result_and_universe_gap_ledgers() -> (
    None
):
    foreground = parse_protein_reference_table(
        _fixture_path("protein_set_enrichment_foreground.tsv")
    )
    protein_sets = parse_protein_set_table(_fixture_path("protein_set_enrichment.tsv"))
    report = build_protein_set_enrichment_report(
        foreground.accepted_entries,
        protein_sets.accepted_records,
        policy=ProteinSetEnrichmentPolicy(
            missing_background_policy=ProteinSetEnrichmentMissingBackgroundPolicy.MEMBERSHIP_UNIVERSE,
            max_adjusted_p_value=1.0,
            min_enrichment_ratio=0.0,
        ),
    )

    summary_tsv = render_protein_set_enrichment_summary_tsv(report)
    result_tsv = render_protein_set_enrichment_tsv(report)
    universe_gap_tsv = render_protein_set_universe_gap_tsv(report)

    assert summary_tsv.splitlines()[0].startswith("foreground_size\tbackground_size")
    assert "membership_universe" in summary_tsv
    assert "set_category" in result_tsv.splitlines()[0]
    assert "stress_panel" in result_tsv
    assert "foreground\tP999\tprotein was not present in the membership universe" in (
        universe_gap_tsv
    )
