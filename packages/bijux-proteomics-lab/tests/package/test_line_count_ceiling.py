# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_foundation.testing.source_tree_limits import (
    SourceFileLineCountException,
    build_source_tree_line_count_report,
)

LAB_SRC_ROOT = Path("packages/bijux-proteomics-lab/src/bijux_proteomics_lab")
LINE_COUNT_CEILING = 1000


def _temporary_reason(relative_path: str) -> str:
    if relative_path.startswith("design/"):
        return "lab design owners still combine multiple experiment planning surfaces that need narrower modules."
    if relative_path.startswith("outcomes/"):
        return "lab outcome owners still combine observation capture, quality scoring, and evidence promotion that need narrower modules."
    if relative_path.startswith("planning/"):
        return "lab planning owners still combine assay portfolio and next-cycle planning surfaces that need narrower modules."
    return "temporary large-file allowance for a lab owner that still needs narrower boundaries."


def _exception(
    relative_path: str, allowed_line_count: int
) -> SourceFileLineCountException:
    return SourceFileLineCountException(
        relative_path=relative_path,
        allowed_line_count=allowed_line_count,
        temporary_reason=_temporary_reason(relative_path),
    )


LAB_LINE_COUNT_EXCEPTIONS = (
    _exception("design/experiments.py", 1054),
    _exception("outcomes/observations.py", 1283),
    _exception("planning/assays.py", 1380),
)


def test_lab_source_tree_respects_line_count_ceiling() -> None:
    report = build_source_tree_line_count_report(
        LAB_SRC_ROOT,
        ceiling=LINE_COUNT_CEILING,
        exceptions=LAB_LINE_COUNT_EXCEPTIONS,
        exclude_marked_generated=True,
    )

    assert report.stale_exceptions == ()
    assert report.unexpected_over_ceiling == ()
    assert tuple(item.relative_path for item in report.approved_over_ceiling) == tuple(
        item.relative_path for item in LAB_LINE_COUNT_EXCEPTIONS
    )
