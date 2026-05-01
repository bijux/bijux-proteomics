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


class WorkflowStepExecutionStatus(StrEnum):
    """Execution status of a workflow step in one run snapshot."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStepRunState(JsonModel):
    """Materialized state for one step in an existing workflow run."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    status: WorkflowStepExecutionStatus
    depends_on: tuple[str, ...] = Field(default_factory=tuple)
    output_artifacts: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)


class PartialWorkflowRerunRequest(JsonModel):
    """Request to rerun selected workflow steps while preserving lineage."""

    model_config = ConfigDict(extra="forbid")

    prior_run_id: str = Field(..., min_length=1)
    selected_step_ids: tuple[str, ...] = Field(default_factory=tuple)
    rerun_failed_steps: bool = True


class PartialWorkflowRerunAction(JsonModel):
    """One step action in a partial rerun plan."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    action: str = Field(..., pattern=r"^(rerun|reuse)$")
    reason: str = Field(..., min_length=1)


class PartialWorkflowRerunPlan(JsonModel):
    """Dependency-aware partial rerun plan with preserved lineage and evidence."""

    model_config = ConfigDict(extra="forbid")

    prior_run_id: str = Field(..., min_length=1)
    actions: tuple[PartialWorkflowRerunAction, ...] = Field(default_factory=tuple)
    rerun_step_ids: tuple[str, ...] = Field(default_factory=tuple)
    reused_step_ids: tuple[str, ...] = Field(default_factory=tuple)
    preserved_evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)


def plan_partial_workflow_rerun(
    *,
    request: PartialWorkflowRerunRequest,
    step_states: tuple[WorkflowStepRunState, ...],
) -> PartialWorkflowRerunPlan:
    """Plan dependency-safe partial reruns while preserving unaffected historical evidence."""

    if not step_states:
        raise ValueError("partial rerun planning requires existing workflow step states")

    by_id = {step.step_id: step for step in step_states}
    rerun_candidates = set(request.selected_step_ids)
    if request.rerun_failed_steps:
        rerun_candidates.update(
            step.step_id
            for step in step_states
            if step.status is WorkflowStepExecutionStatus.FAILED
        )

    for step_id in tuple(rerun_candidates):
        if step_id not in by_id:
            raise ValueError(f"selected rerun step is not present in prior run: {step_id}")

    changed = set(rerun_candidates)
    grew = True
    while grew:
        grew = False
        for step in step_states:
            if step.step_id in changed:
                continue
            if any(parent in changed for parent in step.depends_on):
                changed.add(step.step_id)
                grew = True

    actions: list[PartialWorkflowRerunAction] = []
    preserved_evidence: list[str] = []
    for step in step_states:
        if step.step_id in changed:
            reason = (
                "requested rerun"
                if step.step_id in rerun_candidates
                else "depends on rerun step output"
            )
            actions.append(
                PartialWorkflowRerunAction(
                    step_id=step.step_id,
                    action="rerun",
                    reason=reason,
                )
            )
            continue

        actions.append(
            PartialWorkflowRerunAction(
                step_id=step.step_id,
                action="reuse",
                reason="unchanged dependencies; preserve prior evidence",
            )
        )
        preserved_evidence.extend(step.evidence_pointers)

    rerun_step_ids = tuple(action.step_id for action in actions if action.action == "rerun")
    reused_step_ids = tuple(action.step_id for action in actions if action.action == "reuse")
    preserved_evidence = sorted(set(preserved_evidence))

    return PartialWorkflowRerunPlan(
        prior_run_id=request.prior_run_id,
        actions=tuple(actions),
        rerun_step_ids=rerun_step_ids,
        reused_step_ids=reused_step_ids,
        preserved_evidence_pointers=tuple(preserved_evidence),
    )
