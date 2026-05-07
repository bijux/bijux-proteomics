# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from importlib import import_module

from bijux_proteomics_runtime.workflows import (
    WorkflowOwnerPackage,
    build_canonical_workflow_handoff_contracts,
)


def _resolve_surface(ref: str) -> object:
    module_name, attribute_name = ref.rsplit(".", 1)
    module = import_module(module_name)
    return getattr(module, attribute_name)


def test_canonical_workflow_handoff_contracts_form_a_closed_stage_graph() -> None:
    contracts = build_canonical_workflow_handoff_contracts()

    assert contracts
    stage_ids = {contract.stage_id for contract in contracts}
    assert stage_ids == {
        "runtime-workflow-manifest",
        "core-identification-review",
        "core-quantification-review",
        "core-ptm-review",
        "knowledge-evidence-review",
        "intelligence-decision-review",
        "lab-review-packet",
        "lab-operational-follow-up",
    }
    for contract in contracts:
        assert set(contract.upstream_stage_ids) <= stage_ids
        assert set(contract.downstream_stage_ids) <= stage_ids
        assert contract.required_artifact_kinds


def test_canonical_workflow_handoff_contracts_resolve_real_owner_surfaces() -> None:
    contracts = build_canonical_workflow_handoff_contracts()

    assert {contract.owner_package for contract in contracts} == {
        WorkflowOwnerPackage.RUNTIME,
        WorkflowOwnerPackage.CORE,
        WorkflowOwnerPackage.KNOWLEDGE,
        WorkflowOwnerPackage.INTELLIGENCE,
        WorkflowOwnerPackage.LAB,
    }
    for contract in contracts:
        produced = _resolve_surface(contract.produced_surface_ref)
        review_packet = _resolve_surface(contract.review_packet_surface_ref)
        assert callable(produced)
        assert callable(review_packet)
