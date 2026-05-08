# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.judgment.benchmark_corpora import (
    BenchmarkDisposition,
)
from bijux_proteomics_intelligence.judgment.benchmark_counterfactuals import (
    build_counterfactual_recommendation_report,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)


def test_counterfactual_report_covers_five_flagship_families() -> None:
    report = build_counterfactual_recommendation_report()

    assert report.report_id == "flagship-counterfactual-recommendations"
    assert report.artifact_path.startswith("artifacts/")
    assert [entry.workflow_family for entry in report.entries] == [
        KnowledgeWorkflowFamily.DDA,
        KnowledgeWorkflowFamily.DIA,
        KnowledgeWorkflowFamily.LFQ,
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.TARGETED,
    ]


def test_counterfactual_report_makes_hidden_dependencies_visible() -> None:
    report = build_counterfactual_recommendation_report()

    assert all(
        entry.baseline_disposition is BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE
        for entry in report.entries
    )
    assert all(
        entry.without_comparator_disposition is BenchmarkDisposition.DO_NOT_RECOMMEND
        for entry in report.entries
    )
    assert all(
        entry.without_literature_disposition is BenchmarkDisposition.DO_NOT_RECOMMEND
        for entry in report.entries
    )
    assert all(
        entry.doubled_lab_burden_disposition is BenchmarkDisposition.DO_NOT_RECOMMEND
        for entry in report.entries
    )
