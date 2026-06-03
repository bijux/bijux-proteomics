# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Laboratory-facing internal-standard tracking surfaces."""

from __future__ import annotations

from collections import defaultdict
import csv
from io import StringIO
from statistics import median, stdev

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.records import MissingValueState, QuantMatrix
from bijux_proteomics.quantification.contracts import (
    SampleReliabilityQcEntry,
    SampleReliabilityQcStatus,
)
from bijux_proteomics_foundation import JsonModel


class InternalStandardTrackingEntry(JsonModel):
    """One per-standard per-sample observation with drift posture."""

    model_config = ConfigDict(extra="forbid")

    standard_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    intensity: float = Field(..., ge=0.0)
    cv: float = Field(..., ge=0.0)
    missing: bool
    drift_flag: bool


def track_internal_standards(
    matrix: QuantMatrix,
    standard_list: tuple[str, ...],
    *,
    relative_drift_threshold: float = 0.35,
) -> tuple[InternalStandardTrackingEntry, ...]:
    """Track expected internal standards across all samples in one matrix."""

    standard_ids = tuple(
        dict.fromkeys(
            standard_id.strip() for standard_id in standard_list if standard_id.strip()
        )
    )
    if not standard_ids:
        raise ValueError("standard_list must include at least one standard_id")
    if not 0.0 < relative_drift_threshold < 1.0:
        raise ValueError("relative_drift_threshold must be between zero and one")

    entity_index_by_id = {
        entity_id: index for index, entity_id in enumerate(matrix.entity_ids)
    }
    missing_standard_ids = tuple(
        standard_id
        for standard_id in standard_ids
        if standard_id not in entity_index_by_id
    )
    if missing_standard_ids:
        raise ValueError(
            "standard_list must be present in matrix.entity_ids and is missing: "
            + ", ".join(missing_standard_ids)
        )

    rows: list[InternalStandardTrackingEntry] = []
    for standard_id in standard_ids:
        entity_index = entity_index_by_id[standard_id]
        observed_intensities = tuple(
            intensity
            for sample_index in range(len(matrix.sample_ids))
            for intensity, missing in (
                _matrix_intensity(matrix, entity_index, sample_index),
            )
            if not missing
        )
        standard_cv = _coefficient_of_variation(observed_intensities)
        baseline_intensity = (
            float(median(observed_intensities)) if observed_intensities else 0.0
        )
        for sample_index, sample_id in enumerate(matrix.sample_ids):
            intensity, missing = _matrix_intensity(matrix, entity_index, sample_index)
            rows.append(
                InternalStandardTrackingEntry(
                    standard_id=standard_id,
                    sample_id=sample_id,
                    intensity=round(intensity, 4),
                    cv=round(standard_cv, 4),
                    missing=missing,
                    drift_flag=_drift_flag(
                        intensity=intensity,
                        missing=missing,
                        baseline_intensity=baseline_intensity,
                        relative_drift_threshold=relative_drift_threshold,
                    ),
                )
            )
    return tuple(rows)


def build_internal_standard_sample_qc(
    entries: tuple[InternalStandardTrackingEntry, ...],
) -> tuple[SampleReliabilityQcEntry, ...]:
    """Convert tracked internal-standard rows into sample-level QC posture."""

    if not entries:
        raise ValueError(
            "internal standard sample qc requires at least one tracking row"
        )

    seen_pairs: set[tuple[str, str]] = set()
    by_sample: dict[str, list[InternalStandardTrackingEntry]] = defaultdict(list)
    for entry in entries:
        pair = (entry.standard_id, entry.sample_id)
        if pair in seen_pairs:
            raise ValueError(
                "internal standard sample qc requires unique standard_id and sample_id pairs"
            )
        seen_pairs.add(pair)
        by_sample[entry.sample_id].append(entry)

    qc_rows: list[SampleReliabilityQcEntry] = []
    for sample_id in sorted(by_sample):
        sample_entries = tuple(
            sorted(
                by_sample[sample_id],
                key=lambda entry: (entry.standard_id, entry.sample_id),
            )
        )
        drift_count = sum(entry.drift_flag for entry in sample_entries)
        missing_count = sum(entry.missing for entry in sample_entries)
        if drift_count == 0:
            status = SampleReliabilityQcStatus.PASSED
        elif drift_count == len(sample_entries):
            status = SampleReliabilityQcStatus.FAIL
        else:
            status = SampleReliabilityQcStatus.CAUTION

        reasons: list[str] = []
        if missing_count > 0:
            reasons.append("internal_standard_missing")
        if drift_count > missing_count:
            reasons.append("internal_standard_drift")
        if not reasons and drift_count > 0:
            reasons.append("internal_standard_drift")

        qc_rows.append(
            SampleReliabilityQcEntry(
                sample_id=sample_id,
                qc_status=status,
                blocked=False,
                status_reason_codes=tuple(reasons),
            )
        )
    return tuple(qc_rows)


def render_internal_standard_tracking_tsv(
    entries: tuple[InternalStandardTrackingEntry, ...],
) -> str:
    """Render tracked internal-standard rows as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "standard_id",
            "sample_id",
            "intensity",
            "cv",
            "missing",
            "drift_flag",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.standard_id,
                entry.sample_id,
                f"{entry.intensity:.4f}",
                f"{entry.cv:.4f}",
                str(entry.missing).lower(),
                str(entry.drift_flag).lower(),
            )
        )
    return buffer.getvalue()


def _matrix_intensity(
    matrix: QuantMatrix,
    entity_index: int,
    sample_index: int,
) -> tuple[float, bool]:
    state = matrix.missing_value_states[entity_index][sample_index]
    value = matrix.values[entity_index][sample_index]
    if state is MissingValueState.OBSERVED and value is not None:
        return max(float(value), 0.0), False
    if state is MissingValueState.ZERO:
        return 0.0, False
    return 0.0, True


def _coefficient_of_variation(intensities: tuple[float, ...]) -> float:
    if len(intensities) < 2:
        return 0.0
    mean_intensity = sum(intensities) / len(intensities)
    if mean_intensity <= 0.0:
        return 0.0
    return float(stdev(intensities) / mean_intensity)


def _drift_flag(
    *,
    intensity: float,
    missing: bool,
    baseline_intensity: float,
    relative_drift_threshold: float,
) -> bool:
    if missing:
        return True
    if baseline_intensity <= 0.0:
        return intensity <= 0.0
    deviation_fraction = abs(intensity - baseline_intensity) / baseline_intensity
    return deviation_fraction > relative_drift_threshold


__all__ = [
    "InternalStandardTrackingEntry",
    "build_internal_standard_sample_qc",
    "render_internal_standard_tracking_tsv",
    "track_internal_standards",
]
