# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Laboratory-facing blank, wash, and background comparison surfaces."""

from __future__ import annotations

import csv
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.records import MissingValueState, QuantMatrix
from bijux_proteomics_foundation import JsonModel


class BackgroundComparisonEntry(JsonModel):
    """One entity-by-sample comparison against the observed blank burden."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    blank_intensity: float = Field(..., ge=0.0)
    sample_intensity: float = Field(..., ge=0.0)
    background_ratio: float = Field(..., ge=0.0)
    background_flag: bool


def compare_samples_to_blanks(
    sample_matrix: QuantMatrix,
    blank_runs: tuple[str, ...],
) -> tuple[BackgroundComparisonEntry, ...]:
    """Compare biological sample intensities against blank or wash runs."""

    blank_sample_ids = tuple(
        dict.fromkeys(
            sample_id.strip() for sample_id in blank_runs if sample_id.strip()
        )
    )
    if not blank_sample_ids:
        raise ValueError("blank_runs must include at least one sample_id")
    missing_blank_sample_ids = tuple(
        sample_id
        for sample_id in blank_sample_ids
        if sample_id not in sample_matrix.sample_ids
    )
    if missing_blank_sample_ids:
        raise ValueError(
            "blank_runs must be present in sample_matrix.sample_ids and are missing: "
            + ", ".join(missing_blank_sample_ids)
        )

    blank_indexes = {
        sample_matrix.sample_ids.index(sample_id) for sample_id in blank_sample_ids
    }
    biological_indexes = tuple(
        index
        for index, sample_id in enumerate(sample_matrix.sample_ids)
        if sample_id not in blank_sample_ids
    )

    rows: list[BackgroundComparisonEntry] = []
    for entity_index, entity_id in enumerate(sample_matrix.entity_ids):
        blank_intensity = _blank_intensity_for_row(
            sample_matrix,
            entity_index=entity_index,
            blank_indexes=blank_indexes,
        )
        for sample_index in biological_indexes:
            sample_id = sample_matrix.sample_ids[sample_index]
            sample_intensity = _matrix_intensity(
                sample_matrix,
                entity_index=entity_index,
                sample_index=sample_index,
            )
            background_ratio = 0.0
            if blank_intensity > 0.0:
                background_ratio = round(
                    blank_intensity / max(sample_intensity, 1e-9), 4
                )
            rows.append(
                BackgroundComparisonEntry(
                    entity_id=entity_id,
                    sample_id=sample_id,
                    blank_intensity=round(blank_intensity, 4),
                    sample_intensity=round(sample_intensity, 4),
                    background_ratio=background_ratio,
                    background_flag=_background_flag(
                        blank_intensity=blank_intensity,
                        sample_intensity=sample_intensity,
                    ),
                )
            )
    return tuple(rows)


def render_background_comparison_tsv(
    entries: tuple[BackgroundComparisonEntry, ...],
) -> str:
    """Render background comparison rows as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_id",
            "sample_id",
            "blank_intensity",
            "sample_intensity",
            "background_ratio",
            "background_flag",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.entity_id,
                entry.sample_id,
                f"{entry.blank_intensity:.4f}",
                f"{entry.sample_intensity:.4f}",
                f"{entry.background_ratio:.4f}",
                str(entry.background_flag).lower(),
            )
        )
    return buffer.getvalue()


def _blank_intensity_for_row(
    matrix: QuantMatrix,
    *,
    entity_index: int,
    blank_indexes: set[int],
) -> float:
    return max(
        (
            _matrix_intensity(
                matrix, entity_index=entity_index, sample_index=sample_index
            )
            for sample_index in blank_indexes
        ),
        default=0.0,
    )


def _matrix_intensity(
    matrix: QuantMatrix,
    *,
    entity_index: int,
    sample_index: int,
) -> float:
    state = matrix.missing_value_states[entity_index][sample_index]
    value = matrix.values[entity_index][sample_index]
    if state is MissingValueState.OBSERVED and value is not None:
        return max(float(value), 0.0)
    if state is MissingValueState.ZERO:
        return 0.0
    return 0.0


def _background_flag(*, blank_intensity: float, sample_intensity: float) -> bool:
    if blank_intensity <= 0.0:
        return False
    if sample_intensity <= 0.0:
        return True
    return sample_intensity <= blank_intensity * 3.0


__all__ = [
    "BackgroundComparisonEntry",
    "compare_samples_to_blanks",
    "render_background_comparison_tsv",
]
