# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_foundation.testing.source_tree_limits import (
    SourceFileLineCountException,
    build_source_tree_line_count_report,
)

INTELLIGENCE_SRC_ROOT = Path(
    "packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence"
)
LINE_COUNT_CEILING = 1000


def _temporary_reason(relative_path: str) -> str:
    if relative_path.startswith("candidates/"):
        return "candidate owners still combine lifecycle, ranking, and decision-policy surfaces that need narrower modules."
    if relative_path.startswith("reviews/"):
        return "review owners still combine benchmark corpus loading, scoring, and narrative assembly that need narrower modules."
    return "temporary large-file allowance for an intelligence owner that still needs narrower boundaries."


def _exception(
    relative_path: str, allowed_line_count: int
) -> SourceFileLineCountException:
    return SourceFileLineCountException(
        relative_path=relative_path,
        allowed_line_count=allowed_line_count,
        temporary_reason=_temporary_reason(relative_path),
    )


INTELLIGENCE_LINE_COUNT_EXCEPTIONS = (
    _exception("candidates/lifecycle.py", 1104),
    _exception("candidates/ranking.py", 1589),
)


def test_intelligence_source_tree_respects_line_count_ceiling() -> None:
    report = build_source_tree_line_count_report(
        INTELLIGENCE_SRC_ROOT,
        ceiling=LINE_COUNT_CEILING,
        exceptions=INTELLIGENCE_LINE_COUNT_EXCEPTIONS,
        exclude_marked_generated=True,
    )

    assert report.stale_exceptions == ()
    assert report.unexpected_over_ceiling == ()
    assert tuple(item.relative_path for item in report.approved_over_ceiling) == tuple(
        item.relative_path for item in INTELLIGENCE_LINE_COUNT_EXCEPTIONS
    )
