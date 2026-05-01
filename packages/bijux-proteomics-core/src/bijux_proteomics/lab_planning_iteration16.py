# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Lab planning production surfaces for iteration 16."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class LabCostModelInput(JsonModel):
    """Cost inputs for one planned assay action."""

    model_config = ConfigDict(extra="forbid")

    action_id: str = Field(..., min_length=1)
    reagent_cost: float = Field(..., ge=0.0)
    instrument_cost: float = Field(..., ge=0.0)
    staff_cost: float = Field(..., ge=0.0)
    opportunity_cost: float = Field(..., ge=0.0)
    uncertainty_fraction: float = Field(..., ge=0.0, le=1.0)


class LabCostModelEntry(JsonModel):
    """Computed cost summary with bounded uncertainty interval."""

    model_config = ConfigDict(extra="forbid")

    action_id: str = Field(..., min_length=1)
    expected_total_cost: float = Field(..., ge=0.0)
    low_estimate: float = Field(..., ge=0.0)
    high_estimate: float = Field(..., ge=0.0)


class LabCostModelReport(JsonModel):
    """Cost model report across planned assay actions."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[LabCostModelEntry, ...] = Field(default_factory=tuple)


def build_lab_cost_model_report(
    actions: tuple[LabCostModelInput, ...],
) -> LabCostModelReport:
    """Model reagent/instrument/staff/opportunity costs with uncertainty intervals."""

    entries = []
    for action in actions:
        expected = (
            action.reagent_cost
            + action.instrument_cost
            + action.staff_cost
            + action.opportunity_cost
        )
        swing = expected * action.uncertainty_fraction
        entries.append(
            LabCostModelEntry(
                action_id=action.action_id,
                expected_total_cost=expected,
                low_estimate=max(0.0, expected - swing),
                high_estimate=expected + swing,
            )
        )

    entries.sort(key=lambda entry: entry.action_id)
    return LabCostModelReport(entries=tuple(entries))
