# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import (
    TmtNormalizationMethod,
    TmtNormalizationPolicy,
    TmtSearchResultSourceKind,
    build_tmt_normalization_report,
    build_tmt_reporter_feature_bundle,
    parse_tmt_reporter_table,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_tmt_median_normalization_report_preserves_before_after_review() -> None:
    import_report = parse_tmt_reporter_table(
        _fixture("maxquant_tmt_evidence.tsv"),
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )
    design_report = parse_experimental_design_table(_fixture("tmt.design.tsv"))
    feature_bundle = build_tmt_reporter_feature_bundle(
        import_report,
        design_entries=tuple(design_report.accepted_entries),
    )

    report = build_tmt_normalization_report(feature_bundle)

    assert report.summary.method is TmtNormalizationMethod.MEDIAN
    assert report.summary.channel_count == 8
    assert report.summary.transform_count == 8
    assert report.summary.before_flagged_channel_count >= 1
    assert (
        report.summary.after_flagged_channel_count
        < report.summary.before_flagged_channel_count
    )
    assert report.before_report.summary.channel_total_count == 8
    assert report.after_report.summary.channel_total_count == 8
    assert len(report.channel_distributions) == 16
    assert all(entry.scale_factor is not None for entry in report.transforms)


def test_tmt_total_signal_normalization_equalizes_channel_totals_within_each_plex() -> (
    None
):
    import_report = parse_tmt_reporter_table(
        _fixture("maxquant_tmt_evidence.tsv"),
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )
    design_report = parse_experimental_design_table(_fixture("tmt.design.tsv"))
    feature_bundle = build_tmt_reporter_feature_bundle(
        import_report,
        design_entries=tuple(design_report.accepted_entries),
    )

    report = build_tmt_normalization_report(
        feature_bundle,
        policy=TmtNormalizationPolicy(method=TmtNormalizationMethod.TOTAL_SIGNAL),
    )

    plex_a_totals = {
        entry.sample_id: entry.total_abundance
        for entry in report.channel_distributions
        if entry.stage.value == "after" and entry.multiplex_group == "plex-a"
    }
    assert report.summary.method is TmtNormalizationMethod.TOTAL_SIGNAL
    assert round(plex_a_totals["plex_a_126"], 6) == round(
        plex_a_totals["plex_a_127N"], 6
    )
    assert round(plex_a_totals["plex_a_126"], 6) == round(
        plex_a_totals["plex_a_128N"], 6
    )


def test_tmt_reference_channel_normalization_uses_reference_ratios() -> None:
    import_report = parse_tmt_reporter_table(
        _fixture("maxquant_tmt_evidence.tsv"),
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )
    design_report = parse_experimental_design_table(_fixture("tmt.design.tsv"))
    feature_bundle = build_tmt_reporter_feature_bundle(
        import_report,
        design_entries=tuple(design_report.accepted_entries),
    )

    report = build_tmt_normalization_report(
        feature_bundle,
        policy=TmtNormalizationPolicy(method=TmtNormalizationMethod.REFERENCE_CHANNEL),
    )

    assert report.summary.method is TmtNormalizationMethod.REFERENCE_CHANNEL
    assert report.summary.reference_group_count == 2
    assert all(entry.scale_factor is None for entry in report.transforms)
    assert {
        (entry.multiplex_group, entry.reference_channel) for entry in report.transforms
    } == {("plex-a", "128N"), ("plex-b", "128N")}
    peptide_row = next(
        row
        for row in report.after_report.peptide_matrix.rows
        if row.entity_id == "PEPTIDE"
    )
    reference_value = next(
        value for value in peptide_row.values if value.sample_id == "plex_a_128N"
    )
    treatment_value = next(
        value for value in peptide_row.values if value.sample_id == "plex_a_127N"
    )
    assert round(reference_value.abundance or 0.0, 6) == 1.0
    assert round(treatment_value.abundance or 0.0, 6) == round(1400.0 / 6000.0, 6)
