# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.lookups import (
    get_benchmark_manifest,
)
from bijux_proteomics_knowledge.references.workflows.scientific_risk import (
    build_recommendation_failure_trap_report,
    build_workflow_scientific_error_budget,
)


def test_recommendation_failure_trap_report_requires_downgrade_guards() -> None:
    manifest = get_benchmark_manifest("benchmark:lfq_quantification_repeatability")
    assert manifest is not None

    report = build_recommendation_failure_trap_report(manifest)

    assert report.workflow_family.value == "lfq"
    assert report.entries
    assert "batch shift" in report.entries[0].injected_failure_mode


def test_workflow_scientific_error_budget_names_release_blockers() -> None:
    manifest = get_benchmark_manifest("benchmark:targeted_transition_quality_control")
    assert manifest is not None

    budget = build_workflow_scientific_error_budget(manifest)

    assert budget.workflow_family.value == "targeted"
    assert budget.acceptable_errors
    assert budget.release_blocking_errors
    assert "release bar" in budget.note.lower()
