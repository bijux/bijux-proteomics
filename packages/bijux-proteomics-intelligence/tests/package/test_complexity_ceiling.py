# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_foundation.testing.source_tree_complexity import (
    SourceFunctionComplexityException,
    build_source_tree_complexity_report,
)

INTELLIGENCE_SRC_ROOT = Path(
    "packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence"
)
COMPLEXITY_CEILING = 25


INTELLIGENCE_COMPLEXITY_EXCEPTIONS = (
    SourceFunctionComplexityException(
        relative_path="posture/skeptical.py",
        qualified_name="build_skeptical_review_report",
        allowed_complexity=26,
        temporary_reason=(
            "skeptical posture review assembly still combines multiple challenge and refusal surfaces that need narrower modules."
        ),
    ),
)


def test_intelligence_source_tree_respects_complexity_ceiling() -> None:
    report = build_source_tree_complexity_report(
        INTELLIGENCE_SRC_ROOT,
        ceiling=COMPLEXITY_CEILING,
        exceptions=INTELLIGENCE_COMPLEXITY_EXCEPTIONS,
        exclude_marked_generated=True,
    )

    assert report.stale_exceptions == ()
    assert report.unexpected_over_ceiling == ()
    assert tuple(
        (item.relative_path, item.qualified_name)
        for item in report.approved_over_ceiling
    ) == tuple(
        (item.relative_path, item.qualified_name)
        for item in INTELLIGENCE_COMPLEXITY_EXCEPTIONS
    )
