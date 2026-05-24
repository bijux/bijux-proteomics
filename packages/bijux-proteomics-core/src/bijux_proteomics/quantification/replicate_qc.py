# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned replicate-consistency and batch-aware QC surfaces."""

from __future__ import annotations

import csv
import math
from io import StringIO

import numpy as np

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.batch_effect import (
    build_batch_effect_estimator_report,
)
from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    MissingValueKind,
    QcOutlierSampleEntry,
    ReplicateAndBatchQcReport,
    ReplicateCvConditionEntry,
    ReplicateCvReport,
    ReplicateCorrelationReport,
    SampleReliabilityQcEntry,
    SampleReliabilityQcStatus,
    SampleReliabilityWeightEntry,
    SampleReliabilityWeightReport,
    build_replicate_correlation_report,
    _condition_lookup,
    _matrix_value_index,
)
from bijux_proteomics.quantification.sample_exploration import (
    build_sample_exploration_report,
)


def build_replicate_cv_report(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    high_cv_threshold: float = 0.3,
) -> ReplicateCvReport:
    """Summarize within-condition replicate spread using entity-level CV."""
    condition_by_sample = _condition_lookup(design_entries)
    sample_ids_by_condition: dict[str, list[str]] = {}
    for sample_id in table.sample_ids:
        condition = condition_by_sample.get(sample_id)
        if condition:
            sample_ids_by_condition.setdefault(condition, []).append(sample_id)
    lookup = _matrix_value_index(table)
    entries: list[ReplicateCvConditionEntry] = []
    for condition in sorted(sample_ids_by_condition):
        sample_ids = tuple(sample_ids_by_condition[condition])
        entity_cvs: list[float] = []
        for entity_id in table.entity_ids:
            abundances = np.array(
                [
                    float(cell.abundance)
                    for sample_id in sample_ids
                    if (cell := lookup[(entity_id, sample_id)]).abundance is not None
                ],
                dtype=float,
            )
            if abundances.size < 2:
                continue
            mean_abundance = float(np.mean(abundances))
            if mean_abundance <= 0.0:
                continue
            cv = float(np.std(abundances, ddof=1) / mean_abundance)
            if math.isfinite(cv):
                entity_cvs.append(cv)
        high_cv_entity_count = sum(cv > high_cv_threshold for cv in entity_cvs)
        median_cv = float(np.median(entity_cvs)) if entity_cvs else None
        entries.append(
            ReplicateCvConditionEntry(
                condition=condition,
                replicate_count=len(sample_ids),
                evaluated_entity_count=len(entity_cvs),
                mean_entity_cv=float(np.mean(entity_cvs)) if entity_cvs else None,
                median_entity_cv=median_cv,
                high_cv_entity_count=high_cv_entity_count,
                flagged=(median_cv is not None and median_cv > high_cv_threshold),
            )
        )
    flagged_conditions = sum(entry.flagged for entry in entries)
    note = (
        "replicate cv indicates one or more conditions with unstable within-condition spread"
        if flagged_conditions > 0
        else "replicate cv did not detect unstable within-condition spread under the current threshold"
    )
    return ReplicateCvReport(
        entity_level=table.entity_level,
        high_cv_threshold=high_cv_threshold,
        entries=tuple(entries),
        note=note,
    )

def build_replicate_and_batch_qc_report(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    within_condition_warning_threshold: float = 0.8,
    batch_shift_threshold: float = 0.5,
) -> ReplicateAndBatchQcReport:
    """Build integrated replicate-correlation and batch-shift QC diagnostics."""
    replicate = build_replicate_correlation_report(table, design_entries)
    replicate_cv = build_replicate_cv_report(table, design_entries)
    sample_exploration = build_sample_exploration_report(table, design_entries)
    batch = build_batch_effect_estimator_report(
        table,
        design_entries,
        shift_threshold=batch_shift_threshold,
    )
    design_by_sample = {entry.sample_id: entry for entry in design_entries}
    flagged_samples: dict[str, set[str]] = {}
    for entry in replicate.entries:
        if (
            entry.condition_a == entry.condition_b
            and entry.correlation < within_condition_warning_threshold
        ):
            flagged_samples.setdefault(entry.sample_a, set()).add(
                "low within-condition replicate correlation"
            )
            flagged_samples.setdefault(entry.sample_b, set()).add(
                "low within-condition replicate correlation"
            )
    batch_lookup = {
        batch_entry.batch_id: batch_entry
        for batch_entry in batch.batches
        if batch_entry.flagged
    }
    for sample_id, design in design_by_sample.items():
        if design.batch and design.batch in batch_lookup:
            flagged_samples.setdefault(sample_id, set()).add(
                "sample belongs to a batch with flagged global-abundance shift"
            )
    outlier_reasons_by_sample = {
        entry.sample_id: entry.outlier_reasons
        for entry in sample_exploration.sample_outlier_report.entries
    }
    for entry in sample_exploration.sample_pca_report.entries:
        if entry.outlier:
            for reason in outlier_reasons_by_sample.get(entry.sample_id, ()):
                flagged_samples.setdefault(entry.sample_id, set()).add(
                    f"sample exploration flagged {reason}"
                )
    outliers = tuple(
        sorted(
            (
                QcOutlierSampleEntry(
                    sample_id=sample_id,
                    condition=design_by_sample[sample_id].condition,
                    batch=design_by_sample[sample_id].batch,
                    instrument=design_by_sample[sample_id].instrument,
                    spectra_file=design_by_sample[sample_id].spectra_file,
                    reasons=tuple(sorted(reasons)),
                )
                for sample_id, reasons in flagged_samples.items()
                if sample_id in design_by_sample
            ),
            key=lambda entry: entry.sample_id,
        )
    )
    note = (
        "replicate and batch qc detected one or more outlier samples requiring review"
        if outliers
        else "replicate and batch qc did not detect sample-level outlier signals under configured thresholds"
    )
    return ReplicateAndBatchQcReport(
        batch_effect_report=batch,
        replicate_correlation_report=replicate,
        replicate_cv_report=replicate_cv,
        replicate_correlation_count=len(replicate.entries),
        flagged_batch_count=sum(1 for entry in batch.batches if entry.flagged),
        sample_pca_report=sample_exploration.sample_pca_report,
        condition_clustering_report=sample_exploration.condition_clustering_report,
        outlier_samples=outliers,
        note=note,
    )


def estimate_sample_weights(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    qc_table: tuple[SampleReliabilityQcEntry, ...],
    *,
    low_weight_threshold: float = 0.75,
    exclusion_weight_threshold: float = 0.05,
    low_replicate_correlation_threshold: float = 0.8,
    relative_missingness_drop_threshold: float = 0.15,
) -> SampleReliabilityWeightReport:
    """Estimate sample-level reliability weights from replicate and sample QC evidence."""
    condition_by_sample = _condition_lookup(design_entries)
    missing_design = tuple(
        sorted(sample_id for sample_id in table.sample_ids if sample_id not in condition_by_sample)
    )
    if missing_design:
        raise ValueError(
            "replicate reliability weighting requires design entries for all quantification samples: "
            + ", ".join(missing_design)
        )
    if not 0.0 <= low_weight_threshold <= 1.0:
        raise ValueError("low_weight_threshold must be between zero and one")
    if not 0.0 <= exclusion_weight_threshold <= 1.0:
        raise ValueError("exclusion_weight_threshold must be between zero and one")
    if exclusion_weight_threshold > low_weight_threshold:
        raise ValueError(
            "exclusion_weight_threshold must not exceed low_weight_threshold"
        )

    replicate_qc = build_replicate_and_batch_qc_report(
        table,
        design_entries=design_entries,
    )
    observed_fraction_by_sample = _observed_fraction_by_sample(table)
    condition_median_observed_fraction = _condition_median_observed_fraction(
        observed_fraction_by_sample,
        condition_by_sample,
    )
    within_condition_correlation_by_sample = _within_condition_mean_correlations(
        replicate_qc.replicate_correlation_report
    )
    outlier_reasons_by_sample = {
        entry.sample_id: _normalize_outlier_reasons(entry)
        for entry in replicate_qc.outlier_samples
    }
    flagged_batch_ids = {
        entry.batch_id
        for entry in replicate_qc.batch_effect_report.batches
        if entry.flagged
    }
    design_by_sample = {entry.sample_id: entry for entry in design_entries}
    qc_by_sample = _merge_sample_qc_entries(qc_table)

    entries: list[SampleReliabilityWeightEntry] = []
    for sample_id in table.sample_ids:
        weight = 1.0
        reasons: set[str] = set()
        sample_qc = qc_by_sample.get(sample_id)
        if sample_qc is not None:
            weight, reasons = _apply_sample_qc_weight_caps(weight, reasons, sample_qc)

        if correlations := within_condition_correlation_by_sample.get(sample_id):
            mean_correlation = float(np.mean(np.array(correlations, dtype=float)))
            if mean_correlation < low_replicate_correlation_threshold:
                weight = min(weight, 0.6)
                reasons.add("low_replicate_correlation")

        if outlier_codes := outlier_reasons_by_sample.get(sample_id):
            weight = min(weight, 0.35)
            reasons.update(outlier_codes)

        batch_id = design_by_sample[sample_id].batch
        if batch_id and batch_id in flagged_batch_ids:
            weight = min(weight, 0.7)
            reasons.add("flagged_batch_shift")

        observed_fraction = observed_fraction_by_sample.get(sample_id, 0.0)
        condition = condition_by_sample[sample_id]
        condition_median = condition_median_observed_fraction.get(condition)
        if (
            condition_median is not None
            and condition_median - observed_fraction >= relative_missingness_drop_threshold
        ):
            weight = min(weight, 0.6)
            reasons.add("high_relative_missingness")

        entries.append(
            SampleReliabilityWeightEntry(
                sample_id=sample_id,
                reliability_weight=round(weight, 4),
                low_weight_reasons=tuple(sorted(reasons)) if weight < 1.0 else (),
            )
        )

    ordered_entries = tuple(sorted(entries, key=lambda entry: entry.sample_id))
    low_weight_sample_count = sum(
        entry.reliability_weight < low_weight_threshold for entry in ordered_entries
    )
    excluded_sample_count = sum(
        entry.reliability_weight <= exclusion_weight_threshold
        for entry in ordered_entries
    )
    note = (
        "sample reliability weighting downweights or excludes replicate outliers, flagged sample qc, flagged batch shifts, and strong relative missingness"
        if low_weight_sample_count > 0
        else "sample reliability weighting did not detect any sample-level reliability penalties under the configured thresholds"
    )
    return SampleReliabilityWeightReport(
        sample_count=len(ordered_entries),
        low_weight_threshold=low_weight_threshold,
        exclusion_weight_threshold=exclusion_weight_threshold,
        low_weight_sample_count=low_weight_sample_count,
        excluded_sample_count=excluded_sample_count,
        entries=ordered_entries,
        note=note,
    )


def render_sample_reliability_weights_tsv(
    report: SampleReliabilityWeightReport,
) -> str:
    """Render sample reliability weights as a stable TSV table."""
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(["sample_id", "reliability_weight", "low_weight_reasons"])
    for entry in report.entries:
        writer.writerow(
            [
                entry.sample_id,
                f"{entry.reliability_weight:.4f}",
                ";".join(entry.low_weight_reasons),
            ]
        )
    return buffer.getvalue()


def _observed_fraction_by_sample(table: LabelFreeQuantTable) -> dict[str, float]:
    sample_values: dict[str, list[object]] = {sample_id: [] for sample_id in table.sample_ids}
    for value in table.values:
        sample_values.setdefault(value.sample_id, []).append(value)
    observed_fraction_by_sample: dict[str, float] = {}
    for sample_id, values in sample_values.items():
        if not values:
            observed_fraction_by_sample[sample_id] = 0.0
            continue
        observed_count = sum(
            value.missing_value_kind in (MissingValueKind.OBSERVED, MissingValueKind.ZERO)
            for value in values
        )
        observed_fraction_by_sample[sample_id] = observed_count / len(values)
    return observed_fraction_by_sample


def _condition_median_observed_fraction(
    observed_fraction_by_sample: dict[str, float],
    condition_by_sample: dict[str, str],
) -> dict[str, float]:
    fractions_by_condition: dict[str, list[float]] = {}
    for sample_id, observed_fraction in observed_fraction_by_sample.items():
        condition = condition_by_sample.get(sample_id)
        if condition is None:
            continue
        fractions_by_condition.setdefault(condition, []).append(observed_fraction)
    return {
        condition: float(np.median(np.array(fractions, dtype=float)))
        for condition, fractions in fractions_by_condition.items()
        if fractions
    }


def _within_condition_mean_correlations(
    report: ReplicateCorrelationReport,
) -> dict[str, tuple[float, ...]]:
    correlation_lists: dict[str, list[float]] = {}
    for entry in report.entries:
        if entry.condition_a != entry.condition_b:
            continue
        correlation_lists.setdefault(entry.sample_a, []).append(entry.correlation)
        correlation_lists.setdefault(entry.sample_b, []).append(entry.correlation)
    return {
        sample_id: tuple(values)
        for sample_id, values in correlation_lists.items()
        if values
    }


def _normalize_outlier_reasons(entry: QcOutlierSampleEntry) -> tuple[str, ...]:
    normalized: set[str] = set()
    for reason in entry.reasons:
        if reason == "low within-condition replicate correlation":
            normalized.add("low_replicate_correlation")
        elif reason == "sample belongs to a batch with flagged global-abundance shift":
            normalized.add("flagged_batch_shift")
        elif reason.startswith("sample exploration flagged "):
            normalized.add("sample_exploration_outlier")
        else:
            normalized.add("sample_qc_outlier")
    return tuple(sorted(normalized))


def _merge_sample_qc_entries(
    qc_table: tuple[SampleReliabilityQcEntry, ...],
) -> dict[str, SampleReliabilityQcEntry]:
    severity_rank = {
        SampleReliabilityQcStatus.PASS: 0,
        SampleReliabilityQcStatus.CAUTION: 1,
        SampleReliabilityQcStatus.FAIL: 2,
    }
    merged: dict[str, SampleReliabilityQcEntry] = {}
    for entry in qc_table:
        existing = merged.get(entry.sample_id)
        if existing is None:
            merged[entry.sample_id] = entry
            continue
        merged[entry.sample_id] = SampleReliabilityQcEntry(
            sample_id=entry.sample_id,
            qc_status=(
                entry.qc_status
                if severity_rank[entry.qc_status] >= severity_rank[existing.qc_status]
                else existing.qc_status
            ),
            blocked=existing.blocked or entry.blocked,
            status_reason_codes=tuple(
                sorted(set(existing.status_reason_codes) | set(entry.status_reason_codes))
            ),
        )
    return merged


def _apply_sample_qc_weight_caps(
    weight: float,
    reasons: set[str],
    sample_qc: SampleReliabilityQcEntry,
) -> tuple[float, set[str]]:
    if sample_qc.blocked or sample_qc.qc_status is SampleReliabilityQcStatus.FAIL:
        weight = min(weight, 0.0)
        reasons.add("failed_sample_qc")
    elif sample_qc.qc_status is SampleReliabilityQcStatus.CAUTION:
        weight = min(weight, 0.5)
        reasons.add("caution_sample_qc")
    for reason_code in sample_qc.status_reason_codes:
        reasons.add(f"sample_qc:{reason_code}")
    return weight, reasons


__all__ = [
    "build_replicate_and_batch_qc_report",
    "build_replicate_cv_report",
    "estimate_sample_weights",
    "render_sample_reliability_weights_tsv",
]
