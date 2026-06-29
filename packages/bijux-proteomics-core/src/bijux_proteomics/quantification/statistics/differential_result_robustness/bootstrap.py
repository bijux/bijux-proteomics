# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Bootstrap stability surfaces for differential abundance."""

from __future__ import annotations

import csv
from io import StringIO

import numpy as np

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts.input_models import (
    MissingValueKind,
)
from bijux_proteomics.quantification.contracts.matrix_building import (
    _condition_lookup,
    _matrix_value_index,
)
from bijux_proteomics.quantification.contracts.matrix_models import (
    LabelFreeQuantTable,
    QuantValue,
)
from bijux_proteomics.quantification.statistics.differential_result_robustness.models import (
    BootstrapEffectRobustnessTier,
    BootstrapEffectStabilityEntry,
    BootstrapEffectStabilityReport,
)
from bijux_proteomics.study import (
    SampleRunAnalysisPolicy,
    resolve_sample_run_analysis_entries,
)


def bootstrap_effect_stability(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str | None = None,
    condition_b: str | None = None,
    n_resamples: int = 200,
    significance_threshold: float = 0.05,
    random_seed: int = 0,
    sample_run_policy: SampleRunAnalysisPolicy = (
        SampleRunAnalysisPolicy.COMBINE_TECHNICAL_RUNS
    ),
) -> BootstrapEffectStabilityReport:
    """Bootstrap one two-condition effect report over resampled biological observations."""

    from bijux_proteomics.quantification.statistics.differential_abundance import (
        build_differential_abundance_report,
    )

    base_report = build_differential_abundance_report(
        table,
        design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
        sample_run_policy=sample_run_policy,
    )
    active_design_entries = resolve_sample_run_analysis_entries(
        design_entries,
        policy=sample_run_policy,
    )
    _require_table_sample_ids(
        table,
        design_entries=active_design_entries,
        sample_run_policy=sample_run_policy,
    )
    design_by_sample = {entry.sample_id: entry for entry in active_design_entries}
    rng = np.random.default_rng(random_seed)
    condition_by_sample = _condition_lookup(active_design_entries)
    sample_ids_a = _sample_ids_for_condition(
        condition_by_sample, base_report.condition_a
    )
    sample_ids_b = _sample_ids_for_condition(
        condition_by_sample, base_report.condition_b
    )
    bootstrap_log2fc: dict[str, list[float]] = {
        entry.entity_id: [] for entry in base_report.entries
    }
    bootstrap_q_values: dict[str, list[float]] = {
        entry.entity_id: [] for entry in base_report.entries
    }

    for resample_index in range(n_resamples):
        resampled_sample_ids, resampled_design_entries = _bootstrap_resampled_design(
            rng=rng,
            sample_ids_a=sample_ids_a,
            sample_ids_b=sample_ids_b,
            condition_a=base_report.condition_a,
            condition_b=base_report.condition_b,
            design_by_sample=design_by_sample,
            resample_index=resample_index,
        )
        resampled_table = _bootstrap_resampled_table(
            table=table,
            resampled_sample_ids=resampled_sample_ids,
        )
        resampled_report = build_differential_abundance_report(
            resampled_table,
            resampled_design_entries,
            condition_a=base_report.condition_a,
            condition_b=base_report.condition_b,
            sample_run_policy=sample_run_policy,
        )
        adjusted_lookup = {
            entry.entity_id: float(entry.adjusted_p_value or entry.p_value)
            for entry in resampled_report.entries
        }
        for entry in resampled_report.entries:
            bootstrap_log2fc[entry.entity_id].append(float(entry.log2_fold_change))
            bootstrap_q_values[entry.entity_id].append(adjusted_lookup[entry.entity_id])

    entries = tuple(
        _build_bootstrap_effect_stability_entry(
            entity_id=entry.entity_id,
            log2_fold_changes=tuple(bootstrap_log2fc[entry.entity_id]),
            q_values=tuple(bootstrap_q_values[entry.entity_id]),
            significance_threshold=significance_threshold,
        )
        for entry in base_report.entries
    )
    return BootstrapEffectStabilityReport(
        condition_a=base_report.condition_a,
        condition_b=base_report.condition_b,
        n_resamples=n_resamples,
        significance_threshold=significance_threshold,
        entries=entries,
        stable_entry_count=sum(
            entry.robustness_tier is BootstrapEffectRobustnessTier.STABLE
            for entry in entries
        ),
        caution_entry_count=sum(
            entry.robustness_tier is BootstrapEffectRobustnessTier.CAUTION
            for entry in entries
        ),
        unstable_entry_count=sum(
            entry.robustness_tier is BootstrapEffectRobustnessTier.UNSTABLE
            for entry in entries
        ),
        note=(
            "bootstrap effect stability resamples biological observations within each "
            "condition and tracks fold-change direction plus adjusted-significance stability"
        ),
    )


def render_bootstrap_effect_stability_tsv(
    report: BootstrapEffectStabilityReport,
) -> str:
    """Render one bootstrap effect-stability report as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_id",
            "median_log2fc",
            "sign_consistency",
            "q_value_stability",
            "robustness_tier",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.entity_id,
                entry.median_log2fc,
                entry.sign_consistency,
                entry.q_value_stability,
                entry.robustness_tier.value,
            )
        )
    return buffer.getvalue()


def _build_bootstrap_effect_stability_entry(
    *,
    entity_id: str,
    log2_fold_changes: tuple[float, ...],
    q_values: tuple[float, ...],
    significance_threshold: float,
) -> BootstrapEffectStabilityEntry:
    fold_change_array = np.array(log2_fold_changes, dtype=float)
    q_value_array = np.array(q_values, dtype=float)
    median_log2fc = float(np.median(fold_change_array))
    sign_consistency = _sign_consistency(
        fold_change_array,
        median_log2fc=median_log2fc,
    )
    q_value_stability = _q_value_stability(
        q_value_array,
        significance_threshold=significance_threshold,
    )
    robustness_tier = _bootstrap_robustness_tier(
        sign_consistency=sign_consistency,
        q_value_stability=q_value_stability,
    )
    return BootstrapEffectStabilityEntry(
        entity_id=entity_id,
        median_log2fc=round(median_log2fc, 6),
        sign_consistency=round(sign_consistency, 4),
        q_value_stability=round(q_value_stability, 4),
        robustness_tier=robustness_tier,
    )


def _sign_consistency(
    fold_changes: np.ndarray,
    *,
    median_log2fc: float,
    zero_tolerance: float = 1e-9,
) -> float:
    if fold_changes.size == 0:
        return 0.0
    if median_log2fc > zero_tolerance:
        return float(np.mean(fold_changes > zero_tolerance))
    if median_log2fc < -zero_tolerance:
        return float(np.mean(fold_changes < -zero_tolerance))
    return float(np.mean(np.abs(fold_changes) <= zero_tolerance))


def _q_value_stability(
    q_values: np.ndarray,
    *,
    significance_threshold: float,
) -> float:
    if q_values.size == 0:
        return 0.0
    significant_fraction = float(np.mean(q_values <= significance_threshold))
    return max(significant_fraction, 1.0 - significant_fraction)


def _bootstrap_robustness_tier(
    *,
    sign_consistency: float,
    q_value_stability: float,
) -> BootstrapEffectRobustnessTier:
    if sign_consistency < 0.75:
        return BootstrapEffectRobustnessTier.UNSTABLE
    if sign_consistency < 0.9 or q_value_stability < 0.8:
        return BootstrapEffectRobustnessTier.CAUTION
    return BootstrapEffectRobustnessTier.STABLE


def _bootstrap_resampled_design(
    *,
    rng: np.random.Generator,
    sample_ids_a: tuple[str, ...],
    sample_ids_b: tuple[str, ...],
    condition_a: str,
    condition_b: str,
    design_by_sample: dict[str, ExperimentalDesignEntry],
    resample_index: int,
) -> tuple[tuple[tuple[str, str], ...], tuple[ExperimentalDesignEntry, ...]]:
    sampled_pairs: list[tuple[str, str]] = []
    sampled_entries: list[ExperimentalDesignEntry] = []
    for condition, source_sample_ids in (
        (condition_a, sample_ids_a),
        (condition_b, sample_ids_b),
    ):
        drawn_indices = rng.integers(
            0,
            len(source_sample_ids),
            size=len(source_sample_ids),
        )
        for draw_index, source_index in enumerate(drawn_indices, start=1):
            source_sample_id = source_sample_ids[int(source_index)]
            resampled_sample_id = (
                f"{condition}__bootstrap_{resample_index:04d}_{draw_index:02d}"
            )
            sampled_pairs.append((resampled_sample_id, source_sample_id))
            source_entry = design_by_sample[source_sample_id]
            sampled_entries.append(
                source_entry.model_copy(
                    update={
                        "sample_id": resampled_sample_id,
                        "replicate": draw_index,
                        "metadata": {
                            **source_entry.metadata,
                            "bootstrap_source_sample_id": source_sample_id,
                            "bootstrap_iteration": str(resample_index),
                        },
                    }
                )
            )
    return tuple(sampled_pairs), tuple(sampled_entries)


def _bootstrap_resampled_table(
    *,
    table: LabelFreeQuantTable,
    resampled_sample_ids: tuple[tuple[str, str], ...],
) -> LabelFreeQuantTable:
    lookup = _matrix_value_index(table)
    values: list[QuantValue] = []
    normalization_factors: dict[str, float] = {}
    for resampled_sample_id, source_sample_id in resampled_sample_ids:
        normalization_factors[resampled_sample_id] = table.normalization_factors.get(
            source_sample_id,
            1.0,
        )
        for entity_id in table.entity_ids:
            cell = lookup.get((entity_id, source_sample_id))
            if cell is None:
                values.append(
                    QuantValue(
                        sample_id=resampled_sample_id,
                        entity_id=entity_id,
                        abundance=None,
                        missing_value_kind=MissingValueKind.NOT_OBSERVED,
                        source_feature_count=0,
                    )
                )
                continue
            values.append(cell.model_copy(update={"sample_id": resampled_sample_id}))
    return LabelFreeQuantTable(
        entity_level=table.entity_level,
        measure_kind=table.measure_kind,
        aggregation_method=table.aggregation_method,
        normalization_method=table.normalization_method,
        imputation_method=table.imputation_method,
        sample_ids=tuple(
            resampled_sample_id for resampled_sample_id, _ in resampled_sample_ids
        ),
        entity_ids=table.entity_ids,
        values=tuple(values),
        normalization_factors=normalization_factors,
        entity_protein_refs=table.entity_protein_refs,
        entity_member_peptides=table.entity_member_peptides,
    )


def _require_table_sample_ids(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    sample_run_policy: SampleRunAnalysisPolicy,
) -> None:
    missing_sample_ids = tuple(
        sorted(
            {
                entry.sample_id
                for entry in design_entries
                if entry.sample_id not in table.sample_ids
            }
        )
    )
    if not missing_sample_ids:
        return
    raise ValueError(
        "quantification table sample ids do not cover the resolved analysis design "
        f"for sample/run policy {sample_run_policy.value!r}; missing sample ids: "
        + ", ".join(missing_sample_ids)
    )


def _sample_ids_for_condition(
    condition_by_sample: dict[str, str],
    condition: str,
) -> tuple[str, ...]:
    return tuple(
        sample_id
        for sample_id, sample_condition in condition_by_sample.items()
        if sample_condition == condition
    )


__all__ = [
    "bootstrap_effect_stability",
    "render_bootstrap_effect_stability_tsv",
]
