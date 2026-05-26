# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_foundation.testing.source_tree_limits import (
    build_source_tree_line_count_report,
)

FOUNDATION_SRC_ROOT = Path(
    "packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation"
)
LINE_COUNT_CEILING = 1000


def test_foundation_source_tree_respects_line_count_ceiling() -> None:
    report = build_source_tree_line_count_report(
        FOUNDATION_SRC_ROOT,
        ceiling=LINE_COUNT_CEILING,
    )

    assert report.approved_over_ceiling == ()
    assert report.unexpected_over_ceiling == ()
    assert report.stale_exceptions == ()
