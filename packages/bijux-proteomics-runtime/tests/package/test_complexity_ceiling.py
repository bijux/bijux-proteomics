# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_foundation.testing.source_tree_complexity import (
    SourceFunctionComplexityException,
    build_source_tree_complexity_report,
)

RUNTIME_SRC_ROOT = Path(
    "packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime"
)
COMPLEXITY_CEILING = 25


def _temporary_reason(relative_path: str) -> str:
    if relative_path.startswith("providers/"):
        return "runtime provider owners still combine transport, polling, and payload adaptation that need narrower modules."
    if relative_path.startswith("runs/"):
        return "runtime run-management owners still combine preflight validation and orchestration reporting that need narrower modules."
    return "temporary complexity allowance for a runtime owner that still needs narrower boundaries."


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


RUNTIME_COMPLEXITY_EXCEPTIONS = (
    _exception(
        "providers/local/esmfold.py",
        "LocalESMFoldProvider._to_per_res_plddt",
        35,
    ),
    _exception("providers/local/esmfold.py", "LocalESMFoldProvider.predict", 26),
    _exception(
        "providers/remote/colabfold.py",
        "APIColabFoldProvider.predict",
        34,
    ),
    _exception(
        "providers/remote/openprotein.py",
        "APIOpenProteinProvider._wait_and_get_pdb",
        46,
    ),
    _exception("runs/preflight.py", "build_runtime_preflight_report", 27),
)


def test_runtime_source_tree_respects_complexity_ceiling() -> None:
    report = build_source_tree_complexity_report(
        RUNTIME_SRC_ROOT,
        ceiling=COMPLEXITY_CEILING,
        exceptions=RUNTIME_COMPLEXITY_EXCEPTIONS,
    )

    assert report.stale_exceptions == ()
    assert report.unexpected_over_ceiling == ()
    assert tuple(
        (item.relative_path, item.qualified_name) for item in report.approved_over_ceiling
    ) == tuple(
        (item.relative_path, item.qualified_name)
        for item in RUNTIME_COMPLEXITY_EXCEPTIONS
    )
