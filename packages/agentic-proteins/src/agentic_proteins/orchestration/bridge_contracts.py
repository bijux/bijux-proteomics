"""Compatibility wrapper over canonical runtime bridge contracts."""

from __future__ import annotations

from bijux_proteomics_runtime.governance.compatibility_bridges import (
    BridgeSurfaceContract,
    CompatibilityRetirementBudget,
    build_bridge_retirement_budget,
    list_bridge_surface_contracts,
)

__all__ = (
    "BridgeSurfaceContract",
    "CompatibilityRetirementBudget",
    "build_bridge_retirement_budget",
    "list_bridge_surface_contracts",
)
