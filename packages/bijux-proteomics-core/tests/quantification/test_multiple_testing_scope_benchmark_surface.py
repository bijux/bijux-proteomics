# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification import (
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    build_multiple_testing_scope_benchmark_report,
    normalize_label_free_table,
    parse_ms1_feature_table,
)


def _quant_fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parents[4]
        / "packages"
        / "bijux-proteomics-core"
        / "tests"
        / "fixtures"
        / "quant"
        / name
    )


def test_multiple_testing_scope_benchmark_distinguishes_supported_and_refused_scopes() -> (
    None
):
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

    report = build_multiple_testing_scope_benchmark_report(
        table,
        design_entries=design_report.accepted_entries,
        condition_a="control",
        condition_b="treatment",
    )

    by_scope = {entry.scope: entry for entry in report.entries}
    assert by_scope["global_per_analysis"].status.value == "supported"
    assert by_scope["global_per_analysis"].adjusted_p_values_complete is True
    assert by_scope["global_per_analysis"].adjusted_p_values_monotonic is True
    assert by_scope["per_contrast"].status.value == "supported"
    assert by_scope["hierarchical"].status.value == "refused"
    assert "hierarchical correction engine" in by_scope["hierarchical"].note
