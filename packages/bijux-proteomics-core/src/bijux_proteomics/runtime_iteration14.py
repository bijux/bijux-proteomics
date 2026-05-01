# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Workflow runtime and API surfaces for iteration 14."""

from __future__ import annotations

from enum import StrEnum
import hashlib
import json

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class RuntimeWorkflowBlueprintStage(StrEnum):
    """Canonical runtime stages required for replayable workflow blueprints."""

    SEQUENCE_INTAKE = "sequence_intake"
    SEARCH_INGESTION = "search_ingestion"
    FDR = "fdr"
    QUANT = "quant"
    QC = "qc"
    EVIDENCE = "evidence"
    INTELLIGENCE = "intelligence"
    LAB_HANDOFF = "lab_handoff"


class RuntimeWorkflowBlueprintStep(JsonModel):
    """One workflow step in a reproducible runtime blueprint."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    stage: RuntimeWorkflowBlueprintStage
    tool_name: str = Field(..., min_length=1)
    input_roles: tuple[str, ...] = Field(default_factory=tuple)
    output_roles: tuple[str, ...] = Field(default_factory=tuple)
    parameter_fingerprint: str = Field(..., min_length=8)
    schema_refs: tuple[str, ...] = Field(default_factory=tuple)


class RuntimeWorkflowBlueprint(JsonModel):
    """Reproducible blueprint connecting intake, search, FDR, quant, and lab handoff."""

    model_config = ConfigDict(extra="forbid")

    blueprint_id: str = Field(..., min_length=1)
    study_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    created_from_run_id: str | None = None
    steps: tuple[RuntimeWorkflowBlueprintStep, ...] = Field(default_factory=tuple)
    workflow_digest: str = Field(..., min_length=64, max_length=64)


def _stable_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def build_runtime_workflow_blueprint(
    *,
    blueprint_id: str,
    study_id: str,
    sample_id: str,
    steps: tuple[RuntimeWorkflowBlueprintStep, ...],
    created_from_run_id: str | None = None,
) -> RuntimeWorkflowBlueprint:
    """Build deterministic workflow blueprint covering the core scientific runtime chain."""

    if not steps:
        raise ValueError("runtime workflow blueprint requires at least one step")

    covered_stages = {step.stage for step in steps}
    missing_stages = [
        stage.value
        for stage in RuntimeWorkflowBlueprintStage
        if stage not in covered_stages
    ]
    if missing_stages:
        raise ValueError(
            "runtime workflow blueprint is incomplete; missing stages: "
            + ", ".join(missing_stages)
        )

    normalized_steps = tuple(
        RuntimeWorkflowBlueprintStep(
            step_id=step.step_id,
            stage=step.stage,
            tool_name=step.tool_name,
            input_roles=tuple(sorted(step.input_roles)),
            output_roles=tuple(sorted(step.output_roles)),
            parameter_fingerprint=step.parameter_fingerprint,
            schema_refs=tuple(sorted(step.schema_refs)),
        )
        for step in steps
    )
    digest = _stable_sha256(
        {
            "blueprint_id": blueprint_id,
            "study_id": study_id,
            "sample_id": sample_id,
            "created_from_run_id": created_from_run_id,
            "steps": [step.model_dump(mode="json") for step in normalized_steps],
        }
    )

    return RuntimeWorkflowBlueprint(
        blueprint_id=blueprint_id,
        study_id=study_id,
        sample_id=sample_id,
        created_from_run_id=created_from_run_id,
        steps=normalized_steps,
        workflow_digest=digest,
    )
