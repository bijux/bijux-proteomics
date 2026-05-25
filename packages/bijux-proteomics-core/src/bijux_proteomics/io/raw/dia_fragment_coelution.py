# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""mzML-backed DIA fragment coelution wrappers."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.chromatography.dia_fragment_coelution import (
    DiaFragmentCoelutionReport,
    score_dia_fragment_trace_coelution,
)
from bijux_proteomics.io.raw.chromatographic_peak_picking import (
    extract_mzml_chromatographic_peaks,
)
from bijux_proteomics.io.tables.xic_target_table import (
    XicTargetEntry,
    XicTargetParseReport,
)


def extract_mzml_dia_fragment_trace_coelution(
    mzml_paths: tuple[Path, ...],
    targets: Path | XicTargetParseReport | tuple[XicTargetEntry, ...],
    *,
    tolerance_da: float | None = None,
    tolerance_ppm: float | None = None,
    ms_level: int = 2,
    min_peak_height: float = 1.0,
    shoulder_boundary_fraction_threshold: float = 0.5,
    apex_tolerance_seconds: float = 5.0,
    min_correlation: float = 0.8,
    min_passing_fragment_count: int = 2,
) -> DiaFragmentCoelutionReport:
    """Extract DIA fragment traces from mzML and score precursor coelution."""

    if not mzml_paths:
        raise ValueError("DIA fragment coelution extraction requires at least one mzML file")

    peak_reports = tuple(
        extract_mzml_chromatographic_peaks(
            mzml_path,
            targets,
            tolerance_da=tolerance_da,
            tolerance_ppm=tolerance_ppm,
            ms_level=ms_level,
            min_peak_height=min_peak_height,
            shoulder_boundary_fraction_threshold=shoulder_boundary_fraction_threshold,
        )
        for mzml_path in mzml_paths
    )
    return score_dia_fragment_trace_coelution(
        peak_reports,
        apex_tolerance_seconds=apex_tolerance_seconds,
        min_correlation=min_correlation,
        min_passing_fragment_count=min_passing_fragment_count,
    )
