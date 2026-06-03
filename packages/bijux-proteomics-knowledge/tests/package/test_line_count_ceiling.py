# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_foundation.testing.source_tree_limits import (
    SourceFileLineCountException,
    build_source_tree_line_count_report,
)

KNOWLEDGE_SRC_ROOT = Path(
    "packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge"
)
LINE_COUNT_CEILING = 1000


def _temporary_reason(relative_path: str) -> str:
    if relative_path.startswith("memory/models/"):
        return "knowledge memory models still combine multiple claim and evidence families that need narrower modules."
    if relative_path.startswith("references/workflows/"):
        return "knowledge workflow reference owners still combine corpus grounding, release packaging, and comparison surfaces that need narrower modules."
    return "temporary large-file allowance for a knowledge owner that still needs narrower boundaries."


def _exception(
    relative_path: str, allowed_line_count: int
) -> SourceFileLineCountException:
    return SourceFileLineCountException(
        relative_path=relative_path,
        allowed_line_count=allowed_line_count,
        temporary_reason=_temporary_reason(relative_path),
    )


KNOWLEDGE_LINE_COUNT_EXCEPTIONS = (
    _exception("memory/models/claims.py", 1125),
    _exception("memory/models/evidence.py", 2538),
    _exception("references/workflows/benchmarks.py", 1274),
    _exception("references/workflows/claim_grounding.py", 1802),
)


def test_knowledge_source_tree_respects_line_count_ceiling() -> None:
    report = build_source_tree_line_count_report(
        KNOWLEDGE_SRC_ROOT,
        ceiling=LINE_COUNT_CEILING,
        exceptions=KNOWLEDGE_LINE_COUNT_EXCEPTIONS,
        exclude_marked_generated=True,
    )

    assert report.stale_exceptions == ()
    assert report.unexpected_over_ceiling == ()
    assert tuple(item.relative_path for item in report.approved_over_ceiling) == tuple(
        item.relative_path for item in KNOWLEDGE_LINE_COUNT_EXCEPTIONS
    )
