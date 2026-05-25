# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""mzML-backed retention-time alignment wrappers."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.chromatography.retention_time_alignment import (
    RetentionTimeAlignmentReport,
    align_chromatographic_peak_retention_times,
)
from bijux_proteomics.io.raw.chromatographic_peak_picking import (
    extract_mzml_chromatographic_peaks,
)
from bijux_proteomics.io.tables.xic_target_table import (
    XicTargetEntry,
    XicTargetParseReport,
    coerce_xic_target_report,
)


def extract_mzml_retention_time_alignment(
    mzml_paths: tuple[Path, ...],
    targets: Path | XicTargetParseReport | tuple[XicTargetEntry, ...],
    *,
    tolerance_da: float | None = None,
    tolerance_ppm: float | None = None,
    reference_run_id: str | None = None,
    aligned_rt_tolerance_seconds: float = 5.0,
    min_anchor_count: int = 2,
) -> RetentionTimeAlignmentReport:
    """Extract chromatographic peaks from multiple mzML runs and align them."""

    if len(mzml_paths) < 2:
        raise ValueError("retention-time alignment requires at least two mzML files")
    target_source = coerce_xic_target_report(targets)
    peak_reports = tuple(
        extract_mzml_chromatographic_peaks(
            mzml_path,
            target_source,
            tolerance_da=tolerance_da,
            tolerance_ppm=tolerance_ppm,
        )
        for mzml_path in mzml_paths
    )
    return align_chromatographic_peak_retention_times(
        peak_reports,
        reference_run_id=reference_run_id,
        aligned_rt_tolerance_seconds=aligned_rt_tolerance_seconds,
        min_anchor_count=min_anchor_count,
    )
