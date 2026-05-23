# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned replicate-consistency and batch-aware QC surfaces."""

from __future__ import annotations

import math

import numpy as np

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.batch_effect import (
    build_batch_effect_estimator_report,
)
from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    QcOutlierSampleEntry,
    ReplicateAndBatchQcReport,
    ReplicateCvConditionEntry,
    ReplicateCvReport,
    build_replicate_correlation_report,
    _condition_lookup,
    _matrix_value_index,
)
from bijux_proteomics.quantification.sample_exploration import (
    build_condition_clustering_report,
    build_sample_pca_report,
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
    sample_pca = build_sample_pca_report(table, design_entries)
    condition_clustering = build_condition_clustering_report(table, design_entries)
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
    for entry in sample_pca.entries:
        if entry.outlier:
            flagged_samples.setdefault(entry.sample_id, set()).add(
                "principal-component profile lies far from the study centroid"
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
        sample_pca_report=sample_pca,
        condition_clustering_report=condition_clustering,
        outlier_samples=outliers,
        note=note,
    )


__all__ = [
    "build_condition_clustering_report",
    "build_replicate_and_batch_qc_report",
    "build_replicate_cv_report",
    "build_sample_pca_report",
]
