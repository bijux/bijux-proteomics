# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_foundation.testing.source_tree_limits import (
    SourceFileLineCountException,
    build_source_tree_line_count_report,
)

RUNTIME_SRC_ROOT = Path(
    "packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime"
)
LINE_COUNT_CEILING = 1000


def _temporary_reason(relative_path: str) -> str:
    if relative_path.startswith("api/"):
        return "runtime api orchestration still combines too many command and presentation helpers in one owner."
    if relative_path.startswith("runs/"):
        return "runtime run-management owners still combine lifecycle, persistence, and replay surfaces that need narrower modules."
    if relative_path.startswith("workflows/"):
        return "runtime workflow owners still combine planning, execution, and review surfaces that need narrower modules."
    return "temporary large-file allowance for a runtime owner that still needs narrower boundaries."


def _exception(relative_path: str, allowed_line_count: int) -> SourceFileLineCountException:
    return SourceFileLineCountException(
        relative_path=relative_path,
        allowed_line_count=allowed_line_count,
        temporary_reason=_temporary_reason(relative_path),
    )


RUNTIME_LINE_COUNT_EXCEPTIONS = (
    _exception("api/cli.py", 1052),
    _exception("runs/manager.py", 1662),
    _exception("workflows/advanced_diann.py", 1300),
    _exception("workflows/benchmark_runs.py", 1547),
    _exception("workflows/plans.py", 4099),
    _exception("workflows/reproducibility.py", 1031),
    _exception("workflows/runs.py", 1812),
)


def test_runtime_source_tree_respects_line_count_ceiling() -> None:
    report = build_source_tree_line_count_report(
        RUNTIME_SRC_ROOT,
        ceiling=LINE_COUNT_CEILING,
        exceptions=RUNTIME_LINE_COUNT_EXCEPTIONS,
        exclude_marked_generated=True,
    )

    assert report.stale_exceptions == ()
    assert report.unexpected_over_ceiling == ()
    assert tuple(item.relative_path for item in report.approved_over_ceiling) == tuple(
        item.relative_path for item in RUNTIME_LINE_COUNT_EXCEPTIONS
    )
