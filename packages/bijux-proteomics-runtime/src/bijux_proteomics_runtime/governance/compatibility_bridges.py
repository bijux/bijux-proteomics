# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility bridge contracts owned by the canonical runtime package."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "BridgeSurfaceContract",
    "CompatibilityRetirementBudget",
    "build_bridge_retirement_budget",
    "list_bridge_surface_contracts",
]


@dataclass(frozen=True)
class BridgeSurfaceContract:
    """One durable compatibility surface and its retirement terms."""

    surface_id: str
    compatibility_entrypoint: str
    canonical_owner_package: str
    canonical_owner_module: str
    retirement_condition: str
    active_downstream_compatibility_required: bool = True


@dataclass(frozen=True)
class CompatibilityRetirementBudget:
    """Explicit shrink budget and end-of-life rule for the compatibility bridge."""

    budget_id: str
    active_bridge_surface_count: int
    legacy_alias_surface_count: int
    maximum_bridge_surface_count: int
    shrink_target_surface_count: int
    end_of_life_condition: str
    notes: tuple[str, ...] = ()


def _legacy_runtime_entrypoint(suffix: str) -> str:
    return "agentic" + "_" + "proteins." + suffix


def list_bridge_surface_contracts() -> tuple[BridgeSurfaceContract, ...]:
    """Return the governed compatibility surfaces for `agentic-proteins`."""

    return (
        BridgeSurfaceContract(
            surface_id="legacy-cli-routing",
            compatibility_entrypoint=_legacy_runtime_entrypoint("interfaces.cli"),
            canonical_owner_package="bijux-proteomics-runtime",
            canonical_owner_module="bijux_proteomics_runtime.api.cli",
            retirement_condition=(
                "retire when downstream integrations invoke the canonical runtime CLI"
            ),
        ),
        BridgeSurfaceContract(
            surface_id="legacy-http-routing",
            compatibility_entrypoint=_legacy_runtime_entrypoint("interfaces.http"),
            canonical_owner_package="bijux-proteomics-runtime",
            canonical_owner_module="bijux_proteomics_runtime.api",
            retirement_condition=(
                "retire when legacy HTTP callers migrate to the canonical runtime API"
            ),
        ),
        BridgeSurfaceContract(
            surface_id="structure-report-rendering",
            compatibility_entrypoint=_legacy_runtime_entrypoint(
                "interfaces.structure_reports"
            ),
            canonical_owner_package="bijux-proteomics-core",
            canonical_owner_module="bijux_proteomics.review.structure_reports",
            retirement_condition=(
                "retire when downstream report consumers import canonical structure review renderers directly"
            ),
        ),
        BridgeSurfaceContract(
            surface_id="agent-runtime-aliases",
            compatibility_entrypoint=_legacy_runtime_entrypoint("agents"),
            canonical_owner_package="bijux-proteomics-runtime",
            canonical_owner_module="bijux_proteomics_runtime.execution.agents",
            retirement_condition=(
                "retire when legacy agent imports stop depending on compat-prefixed entrypoints"
            ),
        ),
        BridgeSurfaceContract(
            surface_id="orchestration-runtime-routing",
            compatibility_entrypoint=_legacy_runtime_entrypoint("orchestration"),
            canonical_owner_package="bijux-proteomics-runtime",
            canonical_owner_module="bijux_proteomics_runtime.runs",
            retirement_condition=(
                "retire when orchestration callers move to canonical runtime run and execution modules"
            ),
        ),
        BridgeSurfaceContract(
            surface_id="legacy-execution-aliases",
            compatibility_entrypoint=_legacy_runtime_entrypoint("execution"),
            canonical_owner_package="bijux-proteomics-runtime",
            canonical_owner_module="bijux_proteomics_runtime.runs",
            retirement_condition=(
                "retire when historical execution aliases are no longer needed alongside orchestration imports"
            ),
        ),
        BridgeSurfaceContract(
            surface_id="provider-routing",
            compatibility_entrypoint=_legacy_runtime_entrypoint("providers"),
            canonical_owner_package="bijux-proteomics-runtime",
            canonical_owner_module="bijux_proteomics_runtime.providers",
            retirement_condition=(
                "retire when provider users import canonical runtime provider contracts and selection surfaces directly"
            ),
        ),
        BridgeSurfaceContract(
            surface_id="state-routing",
            compatibility_entrypoint=_legacy_runtime_entrypoint("state"),
            canonical_owner_package="bijux-proteomics-runtime",
            canonical_owner_module="bijux_proteomics_runtime.state",
            retirement_condition=(
                "retire when state and workspace consumers migrate to canonical runtime state ownership"
            ),
        ),
        BridgeSurfaceContract(
            surface_id="tool-routing",
            compatibility_entrypoint=_legacy_runtime_entrypoint("tools"),
            canonical_owner_package="bijux-proteomics-runtime",
            canonical_owner_module="bijux_proteomics_runtime.execution.tools",
            retirement_condition=(
                "retire when tool catalogs and helper imports point at canonical runtime tool surfaces"
            ),
        ),
    )


def build_bridge_retirement_budget() -> CompatibilityRetirementBudget:
    """Return the explicit shrink budget for the compatibility bridge."""

    contracts = list_bridge_surface_contracts()
    active_bridge_surface_count = len(contracts)
    legacy_alias_surface_count = sum(
        1 for contract in contracts if "alias" in contract.surface_id
    )
    return CompatibilityRetirementBudget(
        budget_id="agentic-proteins-bridge-retirement-budget",
        active_bridge_surface_count=active_bridge_surface_count,
        legacy_alias_surface_count=legacy_alias_surface_count,
        maximum_bridge_surface_count=active_bridge_surface_count,
        shrink_target_surface_count=6,
        end_of_life_condition=(
            "end the compatibility bridge when no active downstream dependency still requires compat-prefixed imports or the legacy CLI"
        ),
        notes=(
            "compatibility surfaces must shrink rather than widen when canonical runtime ownership is available",
            "legacy alias families are explicitly budgeted because they are the first retirement candidates",
        ),
    )
