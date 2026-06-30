# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Normalization and sample-balance review for labeled differential workflows."""

from __future__ import annotations

import numpy as np

from bijux_proteomics.quantification.contracts.input_models import NormalizationMethod
from bijux_proteomics.workflow.pipelines.comparative.label_based_differential.models import (
    LabelBasedDifferentialInputReport,
    LabelBasedNormalizationBalancePlot,
    LabelBasedNormalizationBalancePoint,
)


def normalize_input_report(
    report: LabelBasedDifferentialInputReport,
    *,
    method: NormalizationMethod,
) -> tuple[LabelBasedDifferentialInputReport, dict[str, float]]:
    """Normalize one labeled differential matrix with the supported policy."""

    if method is NormalizationMethod.NONE:
        return (
            report.model_copy(
                update={"note": report.note},
            ),
            dict.fromkeys(report.sample_ids, 1.0),
        )
    if method is not NormalizationMethod.MEDIAN:
        raise ValueError(
            "labeled differential analysis currently supports only none or median normalization"
        )

    sample_values: dict[str, list[float]] = {
        sample_id: [] for sample_id in report.sample_ids
    }
    for row in report.rows:
        for value in row.values:
            if value.abundance is not None and value.abundance > 0.0:
                sample_values[value.sample_id].append(float(value.abundance))
    sample_medians = {
        sample_id: (float(np.median(values)) if values else 0.0)
        for sample_id, values in sample_values.items()
    }
    finite_medians = [median for median in sample_medians.values() if median > 0.0]
    global_median = float(np.median(finite_medians)) if finite_medians else 1.0
    normalization_factors = {
        sample_id: (global_median / median if median > 0.0 else 1.0)
        for sample_id, median in sample_medians.items()
    }
    normalized_rows = tuple(
        row.model_copy(
            update={
                "values": tuple(
                    value.model_copy(
                        update={
                            "abundance": (
                                None
                                if value.abundance is None
                                else float(value.abundance)
                                * normalization_factors[value.sample_id]
                            )
                        }
                    )
                    for value in row.values
                )
            }
        )
        for row in report.rows
    )
    return (
        report.model_copy(
            update={
                "rows": normalized_rows,
                "note": (
                    "labeled differential input preserves the same protein matrix after median sample centering"
                ),
            }
        ),
        normalization_factors,
    )


def build_label_based_normalization_balance_plot(
    before: LabelBasedDifferentialInputReport,
    after: LabelBasedDifferentialInputReport,
    *,
    method: NormalizationMethod,
) -> LabelBasedNormalizationBalancePlot:
    """Build one before/after sample-balance plot payload for labeled matrices."""

    points = (
        *[
            _build_balance_point(before, sample_id=sample_id, stage="before")
            for sample_id in before.sample_ids
        ],
        *[
            _build_balance_point(after, sample_id=sample_id, stage="after")
            for sample_id in after.sample_ids
        ],
    )
    return LabelBasedNormalizationBalancePlot(
        method=method,
        points=tuple(sorted(points, key=lambda entry: (entry.sample_id, entry.stage))),
        note=(
            "sample-balance plot preserves before-and-after totals, medians, and spread for labeled normalization review"
        ),
    )


def _build_balance_point(
    report: LabelBasedDifferentialInputReport,
    *,
    sample_id: str,
    stage: str,
) -> LabelBasedNormalizationBalancePoint:
    abundances = [
        float(value.abundance)
        for row in report.rows
        for value in row.values
        if value.sample_id == sample_id and value.abundance is not None
    ]
    if abundances:
        total_abundance = float(sum(abundances))
        median_abundance = float(np.median(abundances))
        percentile_75 = float(np.percentile(abundances, 75))
        percentile_25 = float(np.percentile(abundances, 25))
        interquartile_range = percentile_75 - percentile_25
    else:
        total_abundance = 0.0
        median_abundance = 0.0
        interquartile_range = 0.0
    return LabelBasedNormalizationBalancePoint(
        sample_id=sample_id,
        stage=stage,
        total_abundance=total_abundance,
        median_abundance=median_abundance,
        interquartile_range=interquartile_range,
    )


_normalize_input_report = normalize_input_report

__all__ = [
    "build_label_based_normalization_balance_plot",
    "normalize_input_report",
]
