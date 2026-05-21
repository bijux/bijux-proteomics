# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned replicate-consistency and batch-aware QC surfaces."""

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    QcOutlierSampleEntry,
    ReplicateAndBatchQcReport,
    build_batch_effect_advisory,
    build_replicate_correlation_report,
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
    batch = build_batch_effect_advisory(
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
        replicate_correlation_count=len(replicate.entries),
        flagged_batch_count=sum(1 for entry in batch.batches if entry.flagged),
        outlier_samples=outliers,
        note=note,
    )


__all__ = ["build_replicate_and_batch_qc_report"]
