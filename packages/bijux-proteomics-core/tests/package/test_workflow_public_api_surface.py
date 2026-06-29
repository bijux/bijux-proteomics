# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics import workflow
from bijux_proteomics.workflow import cards, demo, exports, pipelines, reports
from bijux_proteomics.workflow import cross_study_protein_harmonization
from bijux_proteomics.workflow import public_benchmark_descriptors
from bijux_proteomics.workflow.public_api import (
    CARD_FACADE_OWNERS,
    DEMO_FACADE_OWNERS,
    EXPORT_FACADE_OWNERS,
    PIPELINE_FACADE_OWNERS,
    REPORT_FACADE_OWNERS,
    WORKFLOW_ROOT_OWNERS,
    WORKFLOW_ROOT_SUBMODULES,
    build_lazy_export_index,
    facade_owner_modules,
)
from bijux_proteomics.workflow.result_types import WorkflowResult


def test_workflow_root_public_api_matches_governed_owner_ledger() -> None:
    expected_names, _ = build_lazy_export_index(facade_owner_modules(WORKFLOW_ROOT_OWNERS))

    assert tuple(workflow.__all__) == expected_names
    assert set(WORKFLOW_ROOT_SUBMODULES).isdisjoint(workflow.__all__)
    assert all(hasattr(workflow, name) for name in WORKFLOW_ROOT_SUBMODULES)


def test_workflow_owner_subfacades_match_governed_owner_ledgers() -> None:
    expected_cards, _ = build_lazy_export_index(facade_owner_modules(CARD_FACADE_OWNERS))
    expected_demo, _ = build_lazy_export_index(facade_owner_modules(DEMO_FACADE_OWNERS))
    expected_exports, _ = build_lazy_export_index(
        facade_owner_modules(EXPORT_FACADE_OWNERS)
    )
    expected_pipelines, _ = build_lazy_export_index(
        facade_owner_modules(PIPELINE_FACADE_OWNERS)
    )
    expected_reports, _ = build_lazy_export_index(
        facade_owner_modules(REPORT_FACADE_OWNERS)
    )

    assert tuple(cards.__all__) == expected_cards
    assert tuple(demo.__all__) == expected_demo
    assert tuple(exports.__all__) == expected_exports
    assert tuple(pipelines.__all__) == expected_pipelines
    assert tuple(reports.__all__) == expected_reports


def test_workflow_root_prefers_canonical_owner_for_colliding_exports() -> None:
    assert (
        workflow.CrossStudyProteinStudyInput
        is cross_study_protein_harmonization.CrossStudyProteinStudyInput
    )
    assert workflow.WorkflowResult is WorkflowResult
    assert (
        workflow.load_public_benchmark_descriptor
        is public_benchmark_descriptors.load_public_benchmark_descriptor
    )
