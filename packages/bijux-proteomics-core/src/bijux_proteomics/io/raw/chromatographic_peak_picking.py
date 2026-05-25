# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""mzML-backed chromatographic peak extraction wrappers."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.chromatography.chromatographic_peak_picking import (
    ChromatographicPeakPickingReport,
    pick_chromatographic_peaks,
)
from bijux_proteomics.io.raw.xic_extraction import extract_mzml_xic_traces
from bijux_proteomics.io.tables.xic_target_table import (
    XicTargetEntry,
    XicTargetParseReport,
)


def extract_mzml_chromatographic_peaks(
    mzml_path: Path,
    targets: Path | XicTargetParseReport | tuple[XicTargetEntry, ...],
    *,
    tolerance_da: float | None = None,
    tolerance_ppm: float | None = None,
    ms_level: int = 1,
    min_peak_height: float = 1.0,
    shoulder_boundary_fraction_threshold: float = 0.5,
) -> ChromatographicPeakPickingReport:
    """Extract mzML XIC traces and detect chromatographic peaks."""

    trace_report = extract_mzml_xic_traces(
        mzml_path,
        targets,
        tolerance_da=tolerance_da,
        tolerance_ppm=tolerance_ppm,
        ms_level=ms_level,
    )
    return pick_chromatographic_peaks(
        trace_report,
        min_peak_height=min_peak_height,
        shoulder_boundary_fraction_threshold=shoulder_boundary_fraction_threshold,
    )
