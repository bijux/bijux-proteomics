# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Rendered outputs for missingness classification surfaces."""

from __future__ import annotations

import csv
from io import StringIO

from bijux_proteomics.quantification.missingness.models import (
    MissingnessClassificationReport,
)


def render_missingness_classification_tsv(
    report: MissingnessClassificationReport,
) -> str:
    """Render five-label missingness classifications as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_id",
            "label",
            "observed_sample_count",
            "missing_sample_count",
            "missing_fraction",
            "mean_log2_observed_abundance",
            "note",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.entity_id,
                entry.label.value,
                str(entry.observed_sample_count),
                str(entry.missing_sample_count),
                f"{entry.missing_fraction:.6f}",
                ""
                if entry.mean_log2_observed_abundance is None
                else f"{entry.mean_log2_observed_abundance:.6f}",
                entry.note,
            )
        )
    return buffer.getvalue()


__all__ = ["render_missingness_classification_tsv"]
