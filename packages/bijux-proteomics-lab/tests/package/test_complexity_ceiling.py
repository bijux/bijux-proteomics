# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_foundation.testing.source_tree_complexity import (
    SourceFunctionComplexityException,
    build_source_tree_complexity_report,
)

LAB_SRC_ROOT = Path("packages/bijux-proteomics-lab/src/bijux_proteomics_lab")
COMPLEXITY_CEILING = 25


def _temporary_reason(relative_path: str) -> str:
    if relative_path.startswith("design/"):
        return "lab design owners still combine validation and multiplex planning that need narrower modules."
    if relative_path.startswith("lifecycle/"):
        return "lab lifecycle owners still combine state progression and handoff validation that need narrower modules."
    if relative_path.startswith("outcomes/"):
        return "lab outcomes owners still combine assay acceptance and rerun policy logic that need narrower modules."
    if relative_path.startswith("planning/"):
        return "lab planning owners still combine practical scoring and scheduling heuristics that need narrower modules."
    if relative_path.startswith("readiness/"):
        return "lab readiness owners still combine multiple operational gate families that need narrower modules."
    return "temporary complexity allowance for a lab owner that still needs narrower boundaries."


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


LAB_COMPLEXITY_EXCEPTIONS = (
    _exception("design/experiments.py", "validate_experiment_design", 40),
    _exception("design/experiments.py", "plan_multiplex_labeling", 34),
    _exception("lifecycle/progression.py", "advance_assay_lifecycle", 30),
    _exception("outcomes/observations.py", "evaluate_assay_acceptance", 28),
    _exception(
        "planning/priorities.py",
        "build_follow_up_practicality_report",
        27,
    ),
    _exception(
        "readiness/operations.py",
        "build_operational_readiness_report",
        37,
    ),
)


def test_lab_source_tree_respects_complexity_ceiling() -> None:
    report = build_source_tree_complexity_report(
        LAB_SRC_ROOT,
        ceiling=COMPLEXITY_CEILING,
        exceptions=LAB_COMPLEXITY_EXCEPTIONS,
    )

    assert report.stale_exceptions == ()
    assert report.unexpected_over_ceiling == ()
    assert tuple(
        (item.relative_path, item.qualified_name) for item in report.approved_over_ceiling
    ) == tuple(
        (item.relative_path, item.qualified_name)
        for item in LAB_COMPLEXITY_EXCEPTIONS
    )
