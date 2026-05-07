# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.comparator_regressions import (
    ComparatorRegressionStatus,
    build_workflow_comparator_regression_report,
)


def test_comparator_regression_report_covers_each_workflow_family() -> None:
    report = build_workflow_comparator_regression_report()

    assert {entry.workflow_family for entry in report.entries} == set(
        KnowledgeWorkflowFamily
    )


def test_comparator_regression_report_starts_with_explicit_baseline() -> None:
    report = build_workflow_comparator_regression_report()

    assert all(
        entry.status is ComparatorRegressionStatus.UNCHANGED for entry in report.entries
    )
    assert all(
        "first explicit comparator regression baseline" in entry.reason
        for entry in report.entries
    )
