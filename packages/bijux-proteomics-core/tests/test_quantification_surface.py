# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import numpy as np

from bijux_proteomics import (
    LabelFreeQuantTable,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    apply_benjamini_hochberg,
    build_batch_effect_advisory,
    build_differential_abundance_report,
    build_label_free_intensity_table,
    build_replicate_correlation_report,
    build_spectral_count_table,
    normalize_label_free_table,
    parse_experimental_design_table,
    parse_ms1_feature_table,
    summarize_missing_values,
)


def _quant_fixture(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "quant" / name


def test_ms1_feature_parser_accepts_quant_fixture_and_preserves_missing_states() -> (
    None
):
    report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))

    assert report.total_rows == 32
    assert len(report.accepted_records) == 32
    zero_feature = next(
        record for record in report.accepted_records if record.feature_id == "f008"
    )
    filtered_feature = next(
        record for record in report.accepted_records if record.feature_id == "f006"
    )
    missing_feature = next(
        record for record in report.accepted_records if record.feature_id == "f007"
    )

    assert zero_feature.missing_value_kind.value == "zero"
    assert filtered_feature.missing_value_kind.value == "filtered"
    assert missing_feature.missing_value_kind.value == "missing_not_observed"


def test_ms1_feature_parser_rejects_invalid_rows() -> None:
    report = parse_ms1_feature_table(_quant_fixture("malformed_ms1_features.tsv"))

    assert len(report.accepted_records) == 0
    assert len(report.rejected_rows) == 4
    codes = {issue.code for row in report.rejected_rows for issue in row.issues}
    assert {
        "missing_sample_id",
        "negative_intensity",
        "invalid_intensity",
        "invalid_charge",
    } <= codes


def test_label_free_intensity_rollups_cover_sum_median_and_top_n() -> None:
    report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))

    summed = build_label_free_intensity_table(
        report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    median = build_label_free_intensity_table(
        report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.MEDIAN,
    )
    top_n = build_label_free_intensity_table(
        report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.TOP_N,
        top_n=2,
    )
    lookup_sum = {(value.entity_id, value.sample_id): value for value in summed.values}
    lookup_median = {
        (value.entity_id, value.sample_id): value for value in median.values
    }
    lookup_top_n = {(value.entity_id, value.sample_id): value for value in top_n.values}

    assert lookup_sum[("P001", "C1")].abundance == 2200.0
    assert lookup_median[("P001", "C1")].abundance == 900.0
    assert lookup_top_n[("P001", "C1")].abundance == 1900.0


def test_spectral_count_table_and_missing_summary_distinguish_zero_filtered_and_missing() -> (
    None
):
    report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))
    table = build_spectral_count_table(
        report.accepted_records,
        entity_level=QuantEntityLevel.PEPTIDE,
    )
    summary = summarize_missing_values(table)
    lookup = {(value.entity_id, value.sample_id): value for value in table.values}
    summary_lookup = {entry.sample_id: entry for entry in summary.entries}

    assert lookup[("ZEROPEP", "C1")].abundance == 1.0
    assert lookup[("FILTERPEP", "C1")].abundance is None
    assert lookup[("MISSPEP", "C1")].abundance is None
    assert summary_lookup["C1"].zero_count == 1
    assert summary_lookup["C1"].filtered_count == 1
    assert summary_lookup["C1"].not_observed_count == 1


def test_normalization_methods_align_sample_totals_medians_and_rank_profiles() -> None:
    report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))
    table = build_label_free_intensity_table(
        report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )

    tic = normalize_label_free_table(table, method=NormalizationMethod.TIC)
    median = normalize_label_free_table(table, method=NormalizationMethod.MEDIAN)
    quantile = normalize_label_free_table(table, method=NormalizationMethod.QUANTILE)

    def sample_values(active_table: LabelFreeQuantTable, sample_id: str) -> np.ndarray:
        values = [
            value.abundance
            for value in active_table.values
            if value.sample_id == sample_id and value.abundance is not None
        ]
        return np.array(values, dtype=float)

    tic_totals = [
        float(np.sum(sample_values(tic, sample_id))) for sample_id in tic.sample_ids
    ]
    assert max(tic_totals) - min(tic_totals) < 1e-6

    median_values = [
        float(np.median(sample_values(median, sample_id)))
        for sample_id in median.sample_ids
    ]
    assert max(median_values) - min(median_values) < 1e-6

    quantile_sorted = [
        tuple(np.round(np.sort(sample_values(quantile, sample_id)), 6))
        for sample_id in quantile.sample_ids
    ]
    assert len(set(quantile_sorted)) == 1


def test_batch_effect_and_replicate_correlation_reports_are_stable() -> None:
    feature_report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))
    design_report = parse_experimental_design_table(_quant_fixture("quant.design.tsv"))
    table = normalize_label_free_table(
        build_label_free_intensity_table(
            feature_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.SUM,
        ),
        method=NormalizationMethod.MEDIAN,
    )

    batch_report = build_batch_effect_advisory(table, design_report.accepted_entries)
    replicate_report = build_replicate_correlation_report(
        table, design_report.accepted_entries
    )

    assert batch_report.disposition.value == "ADVISORY"
    assert len(batch_report.batches) == 2
    assert {entry.batch_id for entry in batch_report.batches} == {"batch-a", "batch-b"}
    assert replicate_report.within_condition_mean is not None
    assert len(replicate_report.entries) >= 2
    assert all(entry.shared_entity_count >= 2 for entry in replicate_report.entries)


def test_differential_abundance_and_bh_correction_surface_signal() -> None:
    feature_report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))
    design_report = parse_experimental_design_table(_quant_fixture("quant.design.tsv"))
    table = normalize_label_free_table(
        build_label_free_intensity_table(
            feature_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.TOP_N,
            top_n=2,
        ),
        method=NormalizationMethod.MEDIAN,
    )

    differential = apply_benjamini_hochberg(
        build_differential_abundance_report(
            table,
            design_report.accepted_entries,
            condition_a="control",
            condition_b="treatment",
        )
    )
    first = differential.entries[0]
    p001 = next(entry for entry in differential.entries if entry.entity_id == "P001")
    p002 = next(entry for entry in differential.entries if entry.entity_id == "P002")

    assert first.adjusted_p_value is not None
    assert all(entry.adjusted_p_value is not None for entry in differential.entries)
    assert p001.log2_fold_change > 0
    assert p002.log2_fold_change < 0
