# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics.interpretation import (
    ProteinSetEnrichmentMissingBackgroundPolicy,
    ProteinSetEnrichmentPolicy,
    build_protein_set_enrichment_report,
    parse_protein_reference_table,
    parse_protein_set_table,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_protein_set_enrichment_requires_explicit_background_by_default() -> None:
    foreground = parse_protein_reference_table(
        _fixture_path("protein_set_enrichment_foreground.tsv")
    )
    protein_sets = parse_protein_set_table(_fixture_path("protein_set_enrichment.tsv"))

    with pytest.raises(
        ValueError,
        match="explicit background protein set is required",
    ):
        build_protein_set_enrichment_report(
            foreground.accepted_entries,
            protein_sets.accepted_records,
        )


def test_protein_set_enrichment_can_use_membership_universe_background_policy() -> None:
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

    assert report.summary.background_source.value == "membership_universe"
    assert report.summary.foreground_size == 3
    assert report.summary.background_size == 6
    assert report.summary.foreground_universe_gap_count == 1
    assert report.summary.enriched_set_count >= 1
    top_entry = report.entries[0]
    assert top_entry.set_id == "nucleus"
    assert top_entry.set_category == "compartment"
    assert top_entry.source_accession == "SL-0191"
    assert top_entry.supporting_protein_refs == ("P001", "P004")
    assert any(
        entry.set_role == "foreground" and entry.protein_ref == "P999"
        for entry in report.universe_gap_entries
    )


def test_protein_set_enrichment_respects_explicit_background_sets() -> None:
    foreground = parse_protein_reference_table(
        _fixture_path("protein_set_enrichment_foreground.tsv")
    )
    background = parse_protein_reference_table(
        _fixture_path("protein_set_enrichment_background.tsv")
    )
    protein_sets = parse_protein_set_table(_fixture_path("protein_set_enrichment.tsv"))

    report = build_protein_set_enrichment_report(
        foreground.accepted_entries[:-1],
        protein_sets.accepted_records,
        background_entries=background.accepted_entries,
        policy=ProteinSetEnrichmentPolicy(
            max_adjusted_p_value=1.0,
            min_enrichment_ratio=0.0,
        ),
    )

    assert report.summary.background_source.value == "explicit_input"
    assert report.summary.foreground_universe_gap_count == 0
    assert report.summary.background_universe_gap_count == 1
    assert any(
        entry.set_role == "background" and entry.protein_ref == "P006"
        for entry in report.universe_gap_entries
    )
