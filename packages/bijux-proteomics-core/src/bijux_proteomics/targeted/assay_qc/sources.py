# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Source-specific assay-QC entrypoints."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.targeted.assay_qc.analysis import build_targeted_assay_qc_report
from bijux_proteomics.targeted.assay_qc.models import TargetedAssayQcReport
from bijux_proteomics.targeted.result_import import (
    build_skyline_result_import_report,
    build_transition_table_result_import_report,
)


def build_skyline_targeted_assay_qc_report(path: Path) -> TargetedAssayQcReport:
    """Build targeted assay QC directly from one Skyline-style export."""

    return build_targeted_assay_qc_report(build_skyline_result_import_report(path))


def build_transition_table_targeted_assay_qc_report(
    path: Path,
) -> TargetedAssayQcReport:
    """Build targeted assay QC directly from one exported transition table."""

    return build_targeted_assay_qc_report(
        build_transition_table_result_import_report(path)
    )


__all__ = [
    "build_skyline_targeted_assay_qc_report",
    "build_transition_table_targeted_assay_qc_report",
]
