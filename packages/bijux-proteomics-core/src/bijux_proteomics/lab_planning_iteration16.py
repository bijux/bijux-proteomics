# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Lab planning production surfaces for iteration 16."""

from __future__ import annotations

from enum import StrEnum
import random

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


class PlateRandomizationStrategy(StrEnum):
    """Randomization/blocking strategies for plate layout planning."""

    FULL_RANDOM = "full_random"
    BLOCK_BY_CONDITION = "block_by_condition"
    BLOCK_BY_BATCH = "block_by_batch"


class PlateRandomizationRequest(JsonModel):
    """Input for reproducible plate randomization strategy planning."""

    model_config = ConfigDict(extra="forbid")

    plate_id: str = Field(..., min_length=1)
    strategy: PlateRandomizationStrategy
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    block_labels: tuple[str, ...] = Field(default_factory=tuple)
    seed: int = Field(..., ge=0)


class PlateRandomizationIssue(JsonModel):
    """Support/refusal issue for selected randomization strategy."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class PlateRandomizationPlan(JsonModel):
    """Reproducible randomization output with explicit strategy support state."""

    model_config = ConfigDict(extra="forbid")

    plate_id: str = Field(..., min_length=1)
    strategy: PlateRandomizationStrategy
    supported: bool
    assignment_order: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[PlateRandomizationIssue, ...] = Field(default_factory=tuple)


def build_plate_randomization_plan(
    request: PlateRandomizationRequest,
) -> PlateRandomizationPlan:
    """Support/refuse randomization strategies with deterministic seeded assignment."""

    issues: list[PlateRandomizationIssue] = []
    if not request.sample_ids:
        issues.append(
            PlateRandomizationIssue(
                code="missing_samples",
                message="plate randomization requires at least one sample",
            )
        )
    if request.strategy is not PlateRandomizationStrategy.FULL_RANDOM and (
        not request.block_labels or len(request.block_labels) != len(request.sample_ids)
    ):
        issues.append(
            PlateRandomizationIssue(
                code="invalid_block_labels",
                message=(
                    "blocking strategies require one block label per sample for "
                    "deterministic constrained assignment"
                ),
            )
        )

    if issues:
        return PlateRandomizationPlan(
            plate_id=request.plate_id,
            strategy=request.strategy,
            supported=False,
            assignment_order=(),
            issues=tuple(issues),
        )

    rng = random.Random(request.seed)
    ordered = list(request.sample_ids)
    if request.strategy is PlateRandomizationStrategy.FULL_RANDOM:
        rng.shuffle(ordered)
    else:
        grouped: dict[str, list[str]] = {}
        for sample_id, block in zip(request.sample_ids, request.block_labels, strict=False):
            grouped.setdefault(block, []).append(sample_id)
        block_keys = sorted(grouped)
        rng.shuffle(block_keys)
        ordered = []
        for block in block_keys:
            samples = grouped[block]
            rng.shuffle(samples)
            ordered.extend(samples)

    return PlateRandomizationPlan(
        plate_id=request.plate_id,
        strategy=request.strategy,
        supported=True,
        assignment_order=tuple(ordered),
        issues=(),
    )
