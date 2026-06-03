# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Artifact-valid workflow resume planning for persisted runtime runs."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import ConfigDict, Field, model_validator

from bijux_proteomics_foundation import JsonModel, hash_payload
from bijux_proteomics_runtime.artifacts import StepArtifact
from bijux_proteomics_runtime.support.workspace import write_json_atomic

_WORKFLOW_RESUME_STATE_FILE = "workflow_resume_state.json"


class WorkflowResumeDisposition(StrEnum):
    """Resume outcome for one persisted workflow step."""

    REUSED = "reused"
    RERUN = "rerun"


class WorkflowResumeConfig(JsonModel):
    """Current workflow input payloads evaluated against persisted step artifacts."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    input_payloads: dict[str, Any] = Field(default_factory=dict)


class WorkflowResumeStepState(JsonModel):
    """Persisted step state needed to validate one workflow resume boundary."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    depends_on: tuple[str, ...] = Field(default_factory=tuple)
    direct_input_keys: tuple[str, ...] = Field(default_factory=tuple)
    artifact: StepArtifact

    @model_validator(mode="after")
    def _validate_step_state(self) -> WorkflowResumeStepState:
        if len(set(self.depends_on)) != len(self.depends_on):
            raise ValueError("resume step dependencies must be unique")
        if len(set(self.direct_input_keys)) != len(self.direct_input_keys):
            raise ValueError("resume step direct input keys must be unique")
        return self


class WorkflowResumeState(JsonModel):
    """Persisted workflow-step artifact state for one resumable runtime run."""

    model_config = ConfigDict(extra="forbid")

    state_id: str = Field(..., min_length=1)
    workflow_id: str = Field(..., min_length=1)
    steps: tuple[WorkflowResumeStepState, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def _validate_state(self) -> WorkflowResumeState:
        seen: set[str] = set()
        for step in self.steps:
            if step.step_id in seen:
                raise ValueError("resume state step ids must be unique")
            missing = tuple(
                dependency for dependency in step.depends_on if dependency not in seen
            )
            if missing:
                raise ValueError(
                    "resume state dependencies must reference an earlier step: "
                    + ", ".join(missing)
                )
            seen.add(step.step_id)
        return self


class WorkflowResumeStepDecision(JsonModel):
    """Resume decision for one persisted workflow step."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    disposition: WorkflowResumeDisposition
    reasons: tuple[str, ...] = Field(default_factory=tuple)
    changed_input_keys: tuple[str, ...] = Field(default_factory=tuple)


class WorkflowResumeReport(JsonModel):
    """Stable report over reused and invalidated steps in one resumed workflow."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    reused_step_ids: tuple[str, ...] = Field(default_factory=tuple)
    rerun_step_ids: tuple[str, ...] = Field(default_factory=tuple)
    decisions: tuple[WorkflowResumeStepDecision, ...] = Field(default_factory=tuple)


def _resume_state_path(run_dir: Path) -> Path:
    return run_dir / _WORKFLOW_RESUME_STATE_FILE


def build_workflow_resume_state(
    *,
    workflow_id: str,
    steps: tuple[WorkflowResumeStepState, ...],
) -> WorkflowResumeState:
    """Build one deterministic persisted workflow resume state."""
    payload = {
        "workflow_id": workflow_id,
        "steps": tuple(step.to_dict() for step in steps),
    }
    return WorkflowResumeState(
        state_id=f"workflow_resume_state_{hash_payload(payload)}",
        workflow_id=workflow_id,
        steps=steps,
    )


def write_workflow_resume_state(run_dir: Path, state: WorkflowResumeState) -> Path:
    """Persist one workflow resume state into a runtime run directory."""
    path = _resume_state_path(run_dir)
    write_json_atomic(path, state.to_dict())
    return path


def load_workflow_resume_state(run_dir: Path) -> WorkflowResumeState:
    """Load one persisted workflow resume state from a runtime run directory."""
    return WorkflowResumeState.load_json(_resume_state_path(run_dir))


def _dependency_output_checksum(step: WorkflowResumeStepState) -> str:
    return hash_payload(step.artifact.output_checksums)


def _expected_input_checksums(
    *,
    step: WorkflowResumeStepState,
    config: WorkflowResumeConfig,
    step_by_id: dict[str, WorkflowResumeStepState],
) -> dict[str, str]:
    expected: dict[str, str] = {}
    for input_key in step.direct_input_keys:
        if input_key not in config.input_payloads:
            raise ValueError(
                f"resume config missing required input payload {input_key!r} for step {step.step_id!r}"
            )
        expected[f"config:{input_key}"] = hash_payload(config.input_payloads[input_key])
    for dependency in step.depends_on:
        expected[f"upstream:{dependency}"] = _dependency_output_checksum(
            step_by_id[dependency]
        )
    return expected


def resume_workflow(
    run_dir: Path, config: WorkflowResumeConfig
) -> WorkflowResumeReport:
    """Reuse valid completed steps and rerun only invalidated downstream steps."""
    state = load_workflow_resume_state(run_dir)
    if state.workflow_id != config.workflow_id:
        raise ValueError(
            "resume config workflow_id does not match persisted workflow resume state"
        )

    step_by_id = {step.step_id: step for step in state.steps}
    reused_step_ids: list[str] = []
    rerun_step_ids: list[str] = []
    decisions: list[WorkflowResumeStepDecision] = []

    for step in state.steps:
        reasons: list[str] = []
        changed_input_keys: list[str] = []
        if step.artifact.status != "completed":
            reasons.append("step_not_completed")
        if not step.artifact.output_checksums:
            reasons.append("missing_output_checksums")

        invalid_dependencies = tuple(
            dependency for dependency in step.depends_on if dependency in rerun_step_ids
        )
        if invalid_dependencies:
            reasons.append("downstream_of_invalidated_step")

        expected_input_checksums = _expected_input_checksums(
            step=step,
            config=config,
            step_by_id=step_by_id,
        )
        persisted_input_checksums = dict(step.artifact.input_checksums)
        if expected_input_checksums != persisted_input_checksums:
            reasons.append("input_checksums_changed")
            changed_input_keys.extend(
                input_key
                for input_key in step.direct_input_keys
                if persisted_input_checksums.get(f"config:{input_key}")
                != expected_input_checksums.get(f"config:{input_key}")
            )
            changed_input_keys.extend(
                dependency
                for dependency in step.depends_on
                if persisted_input_checksums.get(f"upstream:{dependency}")
                != expected_input_checksums.get(f"upstream:{dependency}")
            )

        if reasons:
            rerun_step_ids.append(step.step_id)
            decisions.append(
                WorkflowResumeStepDecision(
                    step_id=step.step_id,
                    disposition=WorkflowResumeDisposition.RERUN,
                    reasons=tuple(dict.fromkeys(reasons)),
                    changed_input_keys=tuple(dict.fromkeys(changed_input_keys)),
                )
            )
            continue

        reused_step_ids.append(step.step_id)
        decisions.append(
            WorkflowResumeStepDecision(
                step_id=step.step_id,
                disposition=WorkflowResumeDisposition.REUSED,
                reasons=(),
                changed_input_keys=(),
            )
        )

    return WorkflowResumeReport(
        workflow_id=state.workflow_id,
        reused_step_ids=tuple(reused_step_ids),
        rerun_step_ids=tuple(rerun_step_ids),
        decisions=tuple(decisions),
    )


__all__ = [
    "WorkflowResumeConfig",
    "WorkflowResumeDisposition",
    "WorkflowResumeReport",
    "WorkflowResumeState",
    "WorkflowResumeStepDecision",
    "WorkflowResumeStepState",
    "build_workflow_resume_state",
    "load_workflow_resume_state",
    "resume_workflow",
    "write_workflow_resume_state",
]
