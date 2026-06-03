# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""mzML-backed fragment-ratio stability wrappers."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.chromatography.fragment_ratio_stability import (
    FragmentRatioStabilityReport,
    score_dia_fragment_ratio_stability,
)
from bijux_proteomics.io.raw.dia_fragment_coelution import (
    extract_mzml_dia_fragment_trace_coelution,
)
from bijux_proteomics.io.tables.xic_target_table import (
    XicTargetEntry,
    XicTargetParseReport,
)


def extract_mzml_dia_fragment_ratio_stability(
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
    absolute_ratio_delta_threshold: float = 0.12,
    ratio_cv_threshold: float = 0.25,
) -> FragmentRatioStabilityReport:
    """Extract DIA fragment traces from mzML and score cross-run ratio stability."""

    return score_dia_fragment_ratio_stability(
        extract_mzml_dia_fragment_trace_coelution(
            mzml_paths,
            targets,
            tolerance_da=tolerance_da,
            tolerance_ppm=tolerance_ppm,
            ms_level=ms_level,
            min_peak_height=min_peak_height,
            shoulder_boundary_fraction_threshold=shoulder_boundary_fraction_threshold,
            apex_tolerance_seconds=apex_tolerance_seconds,
            min_correlation=min_correlation,
            min_passing_fragment_count=min_passing_fragment_count,
        ),
        absolute_ratio_delta_threshold=absolute_ratio_delta_threshold,
        ratio_cv_threshold=ratio_cv_threshold,
    )
