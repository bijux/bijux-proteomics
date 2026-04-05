# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Experiment planning helpers."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from bijux_proteomics.programs import ProgramSpec
from bijux_proteomics_knowledge import EvidenceBundle, evidence_gaps


class AssayObservation(BaseModel):
    """Observed assay result."""

    model_config = ConfigDict(extra="forbid")

    assay_id: str = Field(..., min_length=1, description="Assay identifier.")
    metric: str = Field(..., min_length=1, description="Observed metric.")
    value: float = Field(..., description="Observed value.")
    unit: str | None = Field(default=None, description="Measurement unit.")
    passed: bool = Field(..., description="Whether the observation met expectations.")


class ExperimentBatch(BaseModel):
    """Batch of experiments with a shared purpose."""

    model_config = ConfigDict(extra="forbid")

    batch_id: str = Field(..., min_length=1, description="Stable batch identifier.")
    objective: str = Field(..., min_length=1, description="Batch objective.")
    assay_ids: list[str] = Field(
        default_factory=list, description="Assays in the batch."
    )
    blocking_review_gates: list[str] = Field(
        default_factory=list,
        description="Review gates that must clear this batch.",
    )
    priority: int = Field(..., ge=1, description="Execution priority.")


class ExperimentPlan(BaseModel):
    """Experiment plan derived from a program definition."""

    model_config = ConfigDict(extra="forbid")

    program_id: str = Field(..., min_length=1, description="Program identifier.")
    evidence_gaps: list[str] = Field(
        default_factory=list,
        description="Evidence gaps that remain open.",
    )
    review_queue: list[str] = Field(
        default_factory=list,
        description="Review gates that block execution.",
    )
    batches: list[ExperimentBatch] = Field(
        default_factory=list,
        description="Ordered experiment batches.",
    )


def plan_experiment_batches(
    program: ProgramSpec,
    bundle: EvidenceBundle | None = None,
) -> ExperimentPlan:
    """Build a two-lane plan with blocking work first."""
    blocking_assays = [
        assay.assay_id for assay in program.assay_panel if assay.blocking
    ]
    supporting_assays = [
        assay.assay_id for assay in program.assay_panel if not assay.blocking
    ]
    batches: list[ExperimentBatch] = []
    if blocking_assays:
        batches.append(
            ExperimentBatch(
                batch_id=f"{program.program_id}-gate-batch",
                objective="De-risk the program before expensive work starts.",
                assay_ids=blocking_assays,
                blocking_review_gates=[
                    gate.gate_id for gate in program.review_gates if gate.blocking
                ],
                priority=1,
            )
        )
    if supporting_assays:
        batches.append(
            ExperimentBatch(
                batch_id=f"{program.program_id}-optimization-batch",
                objective="Expand confidence and rank promising candidates.",
                assay_ids=supporting_assays,
                blocking_review_gates=[],
                priority=2 if batches else 1,
            )
        )
    required_kinds = [need.value for need in program.evidence_needs]
    gaps = evidence_gaps(bundle, required_kinds) if bundle else required_kinds
    return ExperimentPlan(
        program_id=program.program_id,
        evidence_gaps=gaps,
        review_queue=[gate.gate_id for gate in program.review_gates if gate.blocking],
        batches=batches,
    )
