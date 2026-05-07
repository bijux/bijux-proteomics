# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.contradiction_dossiers import (
    build_workflow_contradiction_dossier,
    list_workflow_contradiction_dossiers,
)


def test_workflow_contradiction_dossiers_cover_each_family() -> None:
    dossiers = list_workflow_contradiction_dossiers()

    assert {dossier.workflow_family for dossier in dossiers} == set(KnowledgeWorkflowFamily)


def test_workflow_contradiction_dossier_keeps_comparator_pressure_visible() -> None:
    dossier = build_workflow_contradiction_dossier(KnowledgeWorkflowFamily.MULTIPLEX)

    assert dossier.scenarios
    assert all(scenario.comparator_position for scenario in dossier.scenarios)
    assert any("external comparator path" in scenario.comparator_position for scenario in dossier.scenarios)
    assert all(scenario.recommended_hold for scenario in dossier.scenarios)


def test_workflow_contradiction_dossier_links_back_to_benchmark_and_matrix_rows() -> (
    None
):
    dossier = build_workflow_contradiction_dossier(KnowledgeWorkflowFamily.DDA)

    assert dossier.benchmark_id == "benchmark:dda_search_reproducibility"
    assert any(ref == dossier.benchmark_id for ref in dossier.scenarios[0].evidence_refs)
    assert any(ref.startswith("literature_matrix:dda:") for ref in dossier.scenarios[0].evidence_refs)
