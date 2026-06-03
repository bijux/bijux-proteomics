# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_foundation.testing.source_tree_complexity import (
    SourceFunctionComplexityException,
    build_source_tree_complexity_report,
)

KNOWLEDGE_SRC_ROOT = Path(
    "packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge"
)
COMPLEXITY_CEILING = 25


def _temporary_reason(relative_path: str) -> str:
    if relative_path.startswith("memory/"):
        return "knowledge memory owners still combine graph traversal, evidence scoring, and contradiction handling that need narrower modules."
    return "temporary complexity allowance for a knowledge owner that still needs narrower boundaries."


def _exception(
    relative_path: str,
    qualified_name: str,
    allowed_complexity: int,
) -> SourceFunctionComplexityException:
    return SourceFunctionComplexityException(
        relative_path=relative_path,
        qualified_name=qualified_name,
        allowed_complexity=allowed_complexity,
        temporary_reason=_temporary_reason(relative_path),
    )


KNOWLEDGE_COMPLEXITY_EXCEPTIONS = (
    _exception("memory/integrity/graph.py", "build_evidence_graph", 30),
    _exception("memory/models/evidence.py", "evaluate_quantitative_support", 27),
    _exception("memory/models/evidence.py", "assess_evidence_record", 26),
    _exception("memory/models/evidence.py", "flag_conflicting_evidence", 30),
)


def test_knowledge_source_tree_respects_complexity_ceiling() -> None:
    report = build_source_tree_complexity_report(
        KNOWLEDGE_SRC_ROOT,
        ceiling=COMPLEXITY_CEILING,
        exceptions=KNOWLEDGE_COMPLEXITY_EXCEPTIONS,
        exclude_marked_generated=True,
    )

    assert report.stale_exceptions == ()
    assert report.unexpected_over_ceiling == ()
    assert tuple(
        (item.relative_path, item.qualified_name)
        for item in report.approved_over_ceiling
    ) == tuple(
        (item.relative_path, item.qualified_name)
        for item in KNOWLEDGE_COMPLEXITY_EXCEPTIONS
    )
