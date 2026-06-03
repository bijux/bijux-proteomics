# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.quantification import (
    DifferentialAbundanceAssumptionReport,
    DifferentialAbundanceEntry,
    DifferentialAbundanceReport,
    DifferentialAbundanceTestType,
    DifferentialReplicatePolicy,
    ImputationMethod,
    NormalizationMethod,
    QuantEntityLevel,
    QuantMethodDifferentialResult,
    QuantRollupMethod,
    compare_quant_methods,
    render_quant_method_agreement_tsv,
)


def _report(
    *,
    normalization_method: NormalizationMethod,
    entries: tuple[DifferentialAbundanceEntry, ...],
) -> DifferentialAbundanceReport:
    return DifferentialAbundanceReport(
        entity_level=QuantEntityLevel.PROTEIN,
        normalization_method=normalization_method,
        imputation_method=ImputationMethod.NONE,
        condition_a="case",
        condition_b="ctrl",
        contrast_name="case_vs_ctrl",
        assumption_report=DifferentialAbundanceAssumptionReport(
            test_type=DifferentialAbundanceTestType.WELCH_T_TEST,
            variance_assumption="unequal_variance",
            multiple_testing_scope="contrast",
            replicate_policy=DifferentialReplicatePolicy(),
        ),
        entries=entries,
    )


def _entry(
    entity_id: str,
    *,
    log2_fold_change: float,
    adjusted_p_value: float,
) -> DifferentialAbundanceEntry:
    return DifferentialAbundanceEntry(
        entity_id=entity_id,
        condition_a="case",
        condition_b="ctrl",
        observations_a=3,
        observations_b=3,
        mean_log2_abundance_a=10.0,
        mean_log2_abundance_b=8.0,
        log2_fold_change=log2_fold_change,
        p_value=min(adjusted_p_value, 0.99),
        adjusted_p_value=adjusted_p_value,
    )


def test_compare_quant_methods_separates_stable_and_method_sensitive_hits() -> None:
    median_sum = QuantMethodDifferentialResult(
        method_id="sum_median",
        rollup_method=QuantRollupMethod.SUM,
        differential_report=_report(
            normalization_method=NormalizationMethod.MEDIAN,
            entries=(
                _entry("PSTABLE", log2_fold_change=1.02, adjusted_p_value=0.001),
                _entry("PSIGLOSS", log2_fold_change=1.18, adjusted_p_value=0.004),
                _entry("PRANGE", log2_fold_change=0.82, adjusted_p_value=0.010),
                _entry("PFLIP", log2_fold_change=-1.05, adjusted_p_value=0.020),
            ),
        ),
    )
    median_top_n = QuantMethodDifferentialResult(
        method_id="top_n_median",
        rollup_method=QuantRollupMethod.TOP_N,
        differential_report=_report(
            normalization_method=NormalizationMethod.MEDIAN,
            entries=(
                _entry("PSTABLE", log2_fold_change=0.96, adjusted_p_value=0.002),
                _entry("PSIGLOSS", log2_fold_change=0.46, adjusted_p_value=0.220),
                _entry("PRANGE", log2_fold_change=2.35, adjusted_p_value=0.013),
                _entry("PFLIP", log2_fold_change=1.12, adjusted_p_value=0.018),
            ),
        ),
    )
    quantile_sum = QuantMethodDifferentialResult(
        method_id="sum_quantile",
        rollup_method=QuantRollupMethod.SUM,
        differential_report=_report(
            normalization_method=NormalizationMethod.QUANTILE,
            entries=(
                _entry("PSTABLE", log2_fold_change=1.08, adjusted_p_value=0.001),
                _entry("PSIGLOSS", log2_fold_change=1.24, adjusted_p_value=0.003),
                _entry("PRANGE", log2_fold_change=2.02, adjusted_p_value=0.011),
                _entry("PFLIP", log2_fold_change=1.06, adjusted_p_value=0.017),
            ),
        ),
    )

    report = compare_quant_methods(
        (median_sum, median_top_n, quantile_sum),
        effect_range_tolerance=1.0,
    )
    by_entity = {entry.entity_id: entry for entry in report.entries}

    assert by_entity["PSTABLE"].methods_significant_count == 3
    assert by_entity["PSTABLE"].direction_agreement == 1.0
    assert by_entity["PSTABLE"].effect_range < 0.15
    assert by_entity["PSTABLE"].method_sensitive is False

    assert by_entity["PSIGLOSS"].methods_significant_count == 2
    assert by_entity["PSIGLOSS"].direction_agreement == 1.0
    assert by_entity["PSIGLOSS"].method_sensitive is True

    assert by_entity["PRANGE"].methods_significant_count == 3
    assert by_entity["PRANGE"].direction_agreement == 1.0
    assert by_entity["PRANGE"].effect_range > 1.5
    assert by_entity["PRANGE"].method_sensitive is True

    assert by_entity["PFLIP"].methods_significant_count == 3
    assert by_entity["PFLIP"].direction_agreement == 0.666667
    assert by_entity["PFLIP"].method_sensitive is True

    assert report.stable_hit_count == 1
    assert report.method_sensitive_count == 3


def test_render_quant_method_agreement_tsv_exposes_required_surface() -> None:
    report = compare_quant_methods(
        (
            QuantMethodDifferentialResult(
                method_id="sum_median",
                rollup_method=QuantRollupMethod.SUM,
                differential_report=_report(
                    normalization_method=NormalizationMethod.MEDIAN,
                    entries=(
                        _entry("P001", log2_fold_change=1.0, adjusted_p_value=0.01),
                    ),
                ),
            ),
            QuantMethodDifferentialResult(
                method_id="top_n_quantile",
                rollup_method=QuantRollupMethod.TOP_N,
                differential_report=_report(
                    normalization_method=NormalizationMethod.QUANTILE,
                    entries=(
                        _entry("P001", log2_fold_change=0.4, adjusted_p_value=0.20),
                    ),
                ),
            ),
        )
    )
    rendered = render_quant_method_agreement_tsv(report)

    assert rendered.startswith(
        "entity_id\tmethods_significant_count\tdirection_agreement\teffect_range\tmethod_sensitive\n"
    )
    assert "\nP001\t1\t1.000000\t0.000000\ttrue\n" in rendered


def test_compare_quant_methods_rejects_mixed_contrasts() -> None:
    case_vs_ctrl = QuantMethodDifferentialResult(
        method_id="sum_median",
        rollup_method=QuantRollupMethod.SUM,
        differential_report=_report(
            normalization_method=NormalizationMethod.MEDIAN,
            entries=(_entry("P001", log2_fold_change=1.0, adjusted_p_value=0.01),),
        ),
    )
    rescue_vs_ctrl = QuantMethodDifferentialResult(
        method_id="top_n_median",
        rollup_method=QuantRollupMethod.TOP_N,
        differential_report=_report(
            normalization_method=NormalizationMethod.MEDIAN,
            entries=(_entry("P001", log2_fold_change=1.1, adjusted_p_value=0.02),),
        ).model_copy(
            update={
                "condition_a": "rescue",
                "contrast_name": "rescue_vs_ctrl",
                "entries": (
                    _entry(
                        "P001", log2_fold_change=1.1, adjusted_p_value=0.02
                    ).model_copy(update={"condition_a": "rescue"}),
                ),
            }
        ),
    )

    with pytest.raises(ValueError, match="matching condition_a labels"):
        compare_quant_methods((case_vs_ctrl, rescue_vs_ctrl))
