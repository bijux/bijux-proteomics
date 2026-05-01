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


class WorkflowRunDiffCategory(StrEnum):
    """Diff categories for replayable workflow run comparisons."""

    INPUT = "input"
    ENGINE = "engine"
    PARAMETER = "parameter"
    CONFIDENCE = "confidence"
    QUANT = "quant"
    QC = "qc"
    EVIDENCE = "evidence"
    LAB_CONSEQUENCE = "lab_consequence"


class WorkflowRunSnapshot(JsonModel):
    """Normalized run snapshot used by runtime diffing."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    study_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    input_fingerprint: str = Field(..., min_length=8)
    engine_fingerprint: str = Field(..., min_length=8)
    parameter_fingerprint: str = Field(..., min_length=8)
    confidence_fingerprint: str = Field(..., min_length=8)
    quant_fingerprint: str = Field(..., min_length=8)
    qc_fingerprint: str = Field(..., min_length=8)
    evidence_fingerprint: str = Field(..., min_length=8)
    lab_handoff_fingerprint: str = Field(..., min_length=8)


class WorkflowRunDiffEntry(JsonModel):
    """One changed runtime surface between two runs."""

    model_config = ConfigDict(extra="forbid")

    category: WorkflowRunDiffCategory
    field_name: str = Field(..., min_length=1)
    baseline_value: str = Field(..., min_length=1)
    candidate_value: str = Field(..., min_length=1)
    consequence: str = Field(..., min_length=1)


class WorkflowRunDiffReport(JsonModel):
    """Comparison report across workflow inputs, engines, evidence, and lab impact."""

    model_config = ConfigDict(extra="forbid")

    baseline_run_id: str = Field(..., min_length=1)
    candidate_run_id: str = Field(..., min_length=1)
    same_study: bool
    same_sample: bool
    entries: tuple[WorkflowRunDiffEntry, ...] = Field(default_factory=tuple)


def build_workflow_run_diff_report(
    baseline: WorkflowRunSnapshot,
    candidate: WorkflowRunSnapshot,
) -> WorkflowRunDiffReport:
    """Compare runtime runs across input, parameter, confidence, quant, and lab surfaces."""

    mappings: tuple[tuple[WorkflowRunDiffCategory, str, str, str, str], ...] = (
        (
            WorkflowRunDiffCategory.INPUT,
            "input_fingerprint",
            baseline.input_fingerprint,
            candidate.input_fingerprint,
            "input asset set changed",
        ),
        (
            WorkflowRunDiffCategory.ENGINE,
            "engine_fingerprint",
            baseline.engine_fingerprint,
            candidate.engine_fingerprint,
            "engine/runtime implementation changed",
        ),
        (
            WorkflowRunDiffCategory.PARAMETER,
            "parameter_fingerprint",
            baseline.parameter_fingerprint,
            candidate.parameter_fingerprint,
            "workflow parameterization changed",
        ),
        (
            WorkflowRunDiffCategory.CONFIDENCE,
            "confidence_fingerprint",
            baseline.confidence_fingerprint,
            candidate.confidence_fingerprint,
            "confidence assignment changed",
        ),
        (
            WorkflowRunDiffCategory.QUANT,
            "quant_fingerprint",
            baseline.quant_fingerprint,
            candidate.quant_fingerprint,
            "quantification result surface changed",
        ),
        (
            WorkflowRunDiffCategory.QC,
            "qc_fingerprint",
            baseline.qc_fingerprint,
            candidate.qc_fingerprint,
            "qc decision surface changed",
        ),
        (
            WorkflowRunDiffCategory.EVIDENCE,
            "evidence_fingerprint",
            baseline.evidence_fingerprint,
            candidate.evidence_fingerprint,
            "evidence graph changed",
        ),
        (
            WorkflowRunDiffCategory.LAB_CONSEQUENCE,
            "lab_handoff_fingerprint",
            baseline.lab_handoff_fingerprint,
            candidate.lab_handoff_fingerprint,
            "lab handoff consequence changed",
        ),
    )

    entries = [
        WorkflowRunDiffEntry(
            category=category,
            field_name=field_name,
            baseline_value=baseline_value,
            candidate_value=candidate_value,
            consequence=consequence,
        )
        for category, field_name, baseline_value, candidate_value, consequence in mappings
        if baseline_value != candidate_value
    ]
    entries.sort(key=lambda entry: (entry.category.value, entry.field_name))

    return WorkflowRunDiffReport(
        baseline_run_id=baseline.run_id,
        candidate_run_id=candidate.run_id,
        same_study=baseline.study_id == candidate.study_id,
        same_sample=baseline.sample_id == candidate.sample_id,
        entries=tuple(entries),
    )
