# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.benchmarks import KnowledgeWorkflowFamily
from bijux_proteomics_knowledge.references.workflows.briefings import (
    build_workflow_reference_briefing,
)


def test_lab_can_consume_knowledge_briefing_with_operational_caveats() -> None:
    briefing = build_workflow_reference_briefing(KnowledgeWorkflowFamily.TARGETED)

    assert (
        briefing.benchmark_manifest.benchmark_id
        == "benchmark:targeted_transition_quality_control"
    )
    assert briefing.limitation.problem_ids
    assert briefing.literature_groups
    assert briefing.scientific_rules
    assert any(
        problem.problem_id == "problem:targeted_rollup_shortcut"
        for problem in briefing.known_problems
    )
