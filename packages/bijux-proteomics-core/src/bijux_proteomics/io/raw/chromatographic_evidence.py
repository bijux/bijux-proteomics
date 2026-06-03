# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""mzML-backed chromatographic evidence wrappers."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.chromatography.chromatographic_evidence import (
    ChromatographicEvidenceScoreReport,
    score_chromatographic_evidence,
)
from bijux_proteomics.io.raw.chromatographic_peak_picking import (
    extract_mzml_chromatographic_peaks,
)
from bijux_proteomics.io.raw.retention_time_alignment import (
    extract_mzml_retention_time_alignment,
)
from bijux_proteomics.io.tables.xic_target_table import (
    XicTargetEntry,
    XicTargetParseReport,
)


def extract_mzml_chromatographic_evidence(
    mzml_paths: tuple[Path, ...],
    targets: Path | XicTargetParseReport | tuple[XicTargetEntry, ...],
    *,
    tolerance_da: float | None = None,
    tolerance_ppm: float | None = None,
    aligned_rt_tolerance_seconds: float = 5.0,
    min_anchor_count: int = 2,
) -> ChromatographicEvidenceScoreReport:
    """Extract peaks and score chromatographic evidence from one or more mzML runs."""

    if not mzml_paths:
        raise ValueError(
            "chromatographic evidence scoring requires at least one mzML file"
        )
    if len(mzml_paths) == 1:
        peak_reports = (
            extract_mzml_chromatographic_peaks(
                mzml_paths[0],
                targets,
                tolerance_da=tolerance_da,
                tolerance_ppm=tolerance_ppm,
            ),
        )
        return score_chromatographic_evidence(peak_reports)

    alignment_report = extract_mzml_retention_time_alignment(
        mzml_paths,
        targets,
        tolerance_da=tolerance_da,
        tolerance_ppm=tolerance_ppm,
        aligned_rt_tolerance_seconds=aligned_rt_tolerance_seconds,
        min_anchor_count=min_anchor_count,
    )
    return score_chromatographic_evidence(
        alignment_report.peak_reports,
        alignment_report=alignment_report,
    )
