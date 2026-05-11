# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from agentic_proteins.orchestration import (
    BridgeSurfaceContract,
    CompatibilityRetirementBudget,
    build_bridge_retirement_budget,
    list_bridge_surface_contracts,
)

AGENTIC_SRC_ROOT = Path("packages/agentic-proteins/src/agentic_proteins")
EXPECTED_TOP_LEVEL_FAMILIES = {
    "agents",
    "execution",
    "interfaces",
    "orchestration",
    "providers",
    "state",
    "tools",
}


def test_bridge_surface_contracts_cover_every_active_bridge_family() -> None:
    contracts = list_bridge_surface_contracts()
    assert all(isinstance(contract, BridgeSurfaceContract) for contract in contracts)

    covered_families = {
        contract.compatibility_entrypoint.split(".")[1] for contract in contracts
    }
    actual_families = {
        path.name
        for path in AGENTIC_SRC_ROOT.iterdir()
        if path.is_dir() and path.name in EXPECTED_TOP_LEVEL_FAMILIES
    }

    assert covered_families == actual_families


def test_bridge_surface_contracts_name_canonical_owner_and_retirement_condition() -> (
    None
):
    contracts = list_bridge_surface_contracts()

    assert contracts
    assert all(
        contract.canonical_owner_package.startswith("bijux-proteomics-")
        for contract in contracts
    )
    assert all(
        contract.canonical_owner_module.startswith("bijux_") for contract in contracts
    )
    assert all(
        "retire" in contract.retirement_condition
        or "end" in contract.retirement_condition
        for contract in contracts
    )


def test_bridge_retirement_budget_sets_shrink_target_and_end_of_life_rule() -> None:
    budget = build_bridge_retirement_budget()

    assert isinstance(budget, CompatibilityRetirementBudget)
    assert budget.maximum_bridge_surface_count == len(list_bridge_surface_contracts())
    assert budget.shrink_target_surface_count < budget.maximum_bridge_surface_count
    assert budget.legacy_alias_surface_count == 2
    assert "no active downstream dependency" in budget.end_of_life_condition
