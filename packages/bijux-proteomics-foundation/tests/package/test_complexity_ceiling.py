# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_foundation.testing.source_tree_complexity import (
    build_source_tree_complexity_report,
)

FOUNDATION_SRC_ROOT = Path(
    "packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation"
)
COMPLEXITY_CEILING = 25


def test_foundation_source_tree_respects_complexity_ceiling() -> None:
    report = build_source_tree_complexity_report(
        FOUNDATION_SRC_ROOT,
        ceiling=COMPLEXITY_CEILING,
        exclude_marked_generated=True,
    )

    assert report.approved_over_ceiling == ()
    assert report.unexpected_over_ceiling == ()
    assert report.stale_exceptions == ()
