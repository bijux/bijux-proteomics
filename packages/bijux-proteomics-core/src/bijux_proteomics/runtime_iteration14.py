# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Workflow runtime and API surfaces for iteration 14."""

from __future__ import annotations

from enum import StrEnum
import hashlib
import json
from pathlib import PurePosixPath

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


class ArtifactInventoryRecord(JsonModel):
    """One produced workflow artifact with schema and lineage metadata."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    producing_step_id: str = Field(..., min_length=1)
    schema_ref: str = Field(..., min_length=1)
    content_sha256: str = Field(..., min_length=64, max_length=64)
    lineage_parent_ids: tuple[str, ...] = Field(default_factory=tuple)


class ArtifactInventoryVerificationIssue(JsonModel):
    """One verification issue found in artifact inventory validation."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    severity: str = Field(..., pattern=r"^(error|warning)$")
    artifact_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class ArtifactInventoryVerificationReport(JsonModel):
    """Verification result for role/hash/schema/lineage artifact inventory checks."""

    model_config = ConfigDict(extra="forbid")

    verified: bool
    issues: tuple[ArtifactInventoryVerificationIssue, ...] = Field(default_factory=tuple)


def verify_workflow_artifact_inventory(
    *,
    records: tuple[ArtifactInventoryRecord, ...],
    observed_hashes_by_path: dict[str, str],
    allowed_schema_refs: tuple[str, ...],
) -> ArtifactInventoryVerificationReport:
    """Verify produced artifacts by role, hash, producing step, schema, and lineage."""

    issues: list[ArtifactInventoryVerificationIssue] = []
    seen_artifact_ids: set[str] = set()
    all_ids = {record.artifact_id for record in records}
    allowed_schemas = set(allowed_schema_refs)

    for record in records:
        if record.artifact_id in seen_artifact_ids:
            issues.append(
                ArtifactInventoryVerificationIssue(
                    code="duplicate_artifact_id",
                    severity="error",
                    artifact_id=record.artifact_id,
                    message="artifact identifier appears more than once in inventory",
                )
            )
        seen_artifact_ids.add(record.artifact_id)

        observed_hash = observed_hashes_by_path.get(record.path)
        if observed_hash is None:
            issues.append(
                ArtifactInventoryVerificationIssue(
                    code="missing_observed_hash",
                    severity="error",
                    artifact_id=record.artifact_id,
                    message="artifact path is absent from observed hash map",
                )
            )
        elif observed_hash != record.content_sha256:
            issues.append(
                ArtifactInventoryVerificationIssue(
                    code="hash_mismatch",
                    severity="error",
                    artifact_id=record.artifact_id,
                    message="inventory hash does not match observed artifact hash",
                )
            )

        if record.schema_ref not in allowed_schemas:
            issues.append(
                ArtifactInventoryVerificationIssue(
                    code="unsupported_schema_ref",
                    severity="error",
                    artifact_id=record.artifact_id,
                    message=f"schema reference is not allowed: {record.schema_ref}",
                )
            )

        for parent_id in record.lineage_parent_ids:
            if parent_id not in all_ids:
                issues.append(
                    ArtifactInventoryVerificationIssue(
                        code="missing_lineage_parent",
                        severity="warning",
                        artifact_id=record.artifact_id,
                        message=f"lineage parent artifact is not present: {parent_id}",
                    )
                )

    issues.sort(key=lambda issue: (issue.severity, issue.code, issue.artifact_id))
    return ArtifactInventoryVerificationReport(verified=not issues, issues=tuple(issues))


class PortableRunBundleFile(JsonModel):
    """Portable bundle entry detached from original machine-specific paths."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    portable_path: str = Field(..., min_length=1)
    content_sha256: str = Field(..., min_length=64, max_length=64)


class PortableRunBundle(JsonModel):
    """Portable workflow run bundle that remains inspectable on another machine."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    bundle_version: str = Field(..., min_length=1)
    files: tuple[PortableRunBundleFile, ...] = Field(default_factory=tuple)
    manifest_sha256: str = Field(..., min_length=64, max_length=64)


def build_portable_workflow_run_bundle(
    *,
    run_id: str,
    records: tuple[ArtifactInventoryRecord, ...],
    bundle_version: str = "1",
) -> PortableRunBundle:
    """Build portable run bundle entries without hard-coded original absolute paths."""

    normalized_files: list[PortableRunBundleFile] = []
    for index, record in enumerate(records):
        filename = PurePosixPath(record.path).name or f"{record.artifact_id}.dat"
        portable_path = f"artifacts/{record.role}/{index:03d}_{filename}"
        normalized_files.append(
            PortableRunBundleFile(
                artifact_id=record.artifact_id,
                role=record.role,
                portable_path=portable_path,
                content_sha256=record.content_sha256,
            )
        )

    normalized_files.sort(key=lambda entry: (entry.role, entry.portable_path, entry.artifact_id))
    manifest_sha256 = _stable_sha256(
        {
            "run_id": run_id,
            "bundle_version": bundle_version,
            "files": [entry.model_dump(mode="json") for entry in normalized_files],
        }
    )

    return PortableRunBundle(
        run_id=run_id,
        bundle_version=bundle_version,
        files=tuple(normalized_files),
        manifest_sha256=manifest_sha256,
    )


class CacheDecisionOutcome(StrEnum):
    """Cache outcome for one workflow step probe."""

    HIT = "hit"
    MISS = "miss"
    REFUSED = "refused"


class WorkflowCacheProbe(JsonModel):
    """Runtime cache probe input for one tool invocation."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    tool_name: str = Field(..., min_length=1)
    schema_ref: str = Field(..., min_length=1)
    parameter_fingerprint: str = Field(..., min_length=8)
    input_fingerprint: str = Field(..., min_length=8)
    environment_fingerprint: str = Field(..., min_length=8)
    policy_fingerprint: str = Field(..., min_length=8)
    cache_allowed: bool = True


class WorkflowCacheRecord(JsonModel):
    """Materialized cache entry metadata."""

    model_config = ConfigDict(extra="forbid")

    record_id: str = Field(..., min_length=1)
    tool_name: str = Field(..., min_length=1)
    schema_ref: str = Field(..., min_length=1)
    parameter_fingerprint: str = Field(..., min_length=8)
    input_fingerprint: str = Field(..., min_length=8)
    environment_fingerprint: str = Field(..., min_length=8)
    policy_fingerprint: str = Field(..., min_length=8)


class CacheDecisionExplanationEntry(JsonModel):
    """Explainable cache decision for one probe."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    outcome: CacheDecisionOutcome
    reasons: tuple[str, ...] = Field(default_factory=tuple)


class CacheDecisionExplanationReport(JsonModel):
    """Cache decision explain report across workflow probes."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[CacheDecisionExplanationEntry, ...] = Field(default_factory=tuple)
    hit_count: int = Field(..., ge=0)
    miss_count: int = Field(..., ge=0)
    refused_count: int = Field(..., ge=0)


def explain_workflow_cache_decisions(
    *,
    probes: tuple[WorkflowCacheProbe, ...],
    cache_records: tuple[WorkflowCacheRecord, ...],
) -> CacheDecisionExplanationReport:
    """Explain cache hit/miss/refusal by tool, schema, params, input, environment, and policy."""

    entries: list[CacheDecisionExplanationEntry] = []

    for probe in probes:
        if not probe.cache_allowed:
            entries.append(
                CacheDecisionExplanationEntry(
                    step_id=probe.step_id,
                    outcome=CacheDecisionOutcome.REFUSED,
                    reasons=("cache policy forbids reuse for this step",),
                )
            )
            continue

        matching_tool = [
            record for record in cache_records if record.tool_name == probe.tool_name
        ]
        exact_match = next(
            (
                record
                for record in matching_tool
                if record.schema_ref == probe.schema_ref
                and record.parameter_fingerprint == probe.parameter_fingerprint
                and record.input_fingerprint == probe.input_fingerprint
                and record.environment_fingerprint == probe.environment_fingerprint
                and record.policy_fingerprint == probe.policy_fingerprint
            ),
            None,
        )
        if exact_match is not None:
            entries.append(
                CacheDecisionExplanationEntry(
                    step_id=probe.step_id,
                    outcome=CacheDecisionOutcome.HIT,
                    reasons=(f"reused cache record: {exact_match.record_id}",),
                )
            )
            continue

        if not matching_tool:
            entries.append(
                CacheDecisionExplanationEntry(
                    step_id=probe.step_id,
                    outcome=CacheDecisionOutcome.MISS,
                    reasons=("no prior cache entry for tool",),
                )
            )
            continue

        reasons: list[str] = []
        if not any(record.schema_ref == probe.schema_ref for record in matching_tool):
            reasons.append("schema_ref changed")
        if not any(
            record.parameter_fingerprint == probe.parameter_fingerprint
            for record in matching_tool
        ):
            reasons.append("parameter_fingerprint changed")
        if not any(record.input_fingerprint == probe.input_fingerprint for record in matching_tool):
            reasons.append("input_fingerprint changed")
        if not any(
            record.environment_fingerprint == probe.environment_fingerprint
            for record in matching_tool
        ):
            reasons.append("environment_fingerprint changed")
        if not any(
            record.policy_fingerprint == probe.policy_fingerprint for record in matching_tool
        ):
            reasons.append("policy_fingerprint changed")
        if not reasons:
            reasons.append("cache record exists but composite fingerprint does not match")

        entries.append(
            CacheDecisionExplanationEntry(
                step_id=probe.step_id,
                outcome=CacheDecisionOutcome.MISS,
                reasons=tuple(reasons),
            )
        )

    hit_count = sum(1 for entry in entries if entry.outcome is CacheDecisionOutcome.HIT)
    miss_count = sum(1 for entry in entries if entry.outcome is CacheDecisionOutcome.MISS)
    refused_count = sum(1 for entry in entries if entry.outcome is CacheDecisionOutcome.REFUSED)
    return CacheDecisionExplanationReport(
        entries=tuple(entries),
        hit_count=hit_count,
        miss_count=miss_count,
        refused_count=refused_count,
    )


class WorkflowRunHistoryStatus(StrEnum):
    """Run lifecycle status for history querying."""

    COMPLETED = "completed"
    FAILED = "failed"
    REFUSED = "refused"
    RUNNING = "running"


class WorkflowRunHistoryArtifact(JsonModel):
    """Artifact reference attached to one historical workflow run."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)


class WorkflowRunHistoryEntry(JsonModel):
    """One workflow run record indexed for history queries."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    study_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    status: WorkflowRunHistoryStatus
    started_at_utc: str = Field(..., min_length=1)
    artifacts: tuple[WorkflowRunHistoryArtifact, ...] = Field(default_factory=tuple)
    evidence_pointer_ids: tuple[str, ...] = Field(default_factory=tuple)
    review_packet_id: str | None = None
    lab_handoff_id: str | None = None


class WorkflowRunHistoryQuery(JsonModel):
    """Run history query by study/sample/status/artifact role."""

    model_config = ConfigDict(extra="forbid")

    study_id: str | None = None
    sample_id: str | None = None
    status: WorkflowRunHistoryStatus | None = None
    requires_artifact_role: str | None = None
    limit: int = Field(default=20, ge=1, le=500)


class WorkflowRunHistoryQueryReport(JsonModel):
    """Run history query results."""

    model_config = ConfigDict(extra="forbid")

    total_matches: int = Field(..., ge=0)
    runs: tuple[WorkflowRunHistoryEntry, ...] = Field(default_factory=tuple)


def query_workflow_run_history(
    *,
    entries: tuple[WorkflowRunHistoryEntry, ...],
    query: WorkflowRunHistoryQuery,
) -> WorkflowRunHistoryQueryReport:
    """Query runs, artifacts, evidence, reviews, and handoffs by study/sample/status."""

    filtered = [
        entry
        for entry in entries
        if (query.study_id is None or entry.study_id == query.study_id)
        and (query.sample_id is None or entry.sample_id == query.sample_id)
        and (query.status is None or entry.status is query.status)
        and (
            query.requires_artifact_role is None
            or any(artifact.role == query.requires_artifact_role for artifact in entry.artifacts)
        )
    ]
    filtered.sort(key=lambda entry: entry.started_at_utc, reverse=True)
    limited = tuple(filtered[: query.limit])
    return WorkflowRunHistoryQueryReport(total_matches=len(filtered), runs=limited)


class WorkflowApiCliParityIssue(JsonModel):
    """One API/CLI parity mismatch for workflow runtime actions."""

    model_config = ConfigDict(extra="forbid")

    action: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class WorkflowApiCliParityReport(JsonModel):
    """Parity report for API and CLI workflow runtime surfaces."""

    model_config = ConfigDict(extra="forbid")

    parity: bool
    actions_checked: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[WorkflowApiCliParityIssue, ...] = Field(default_factory=tuple)


def evaluate_workflow_api_cli_parity(
    *,
    api_json_by_action: dict[str, object],
    cli_json_by_action: dict[str, object],
) -> WorkflowApiCliParityReport:
    """Evaluate JSON parity across plan/run/inspect/verify/replay/review actions."""

    required_actions = ("plan", "run", "inspect", "verify", "replay", "review")
    issues: list[WorkflowApiCliParityIssue] = []

    for action in required_actions:
        api_payload = api_json_by_action.get(action)
        cli_payload = cli_json_by_action.get(action)
        if api_payload is None or cli_payload is None:
            missing_surfaces = []
            if api_payload is None:
                missing_surfaces.append("api")
            if cli_payload is None:
                missing_surfaces.append("cli")
            issues.append(
                WorkflowApiCliParityIssue(
                    action=action,
                    code="missing_action_surface",
                    message="action missing on " + ", ".join(missing_surfaces),
                )
            )
            continue

        api_text = json.dumps(api_payload, sort_keys=True, separators=(",", ":"))
        cli_text = json.dumps(cli_payload, sort_keys=True, separators=(",", ":"))
        if api_text != cli_text:
            issues.append(
                WorkflowApiCliParityIssue(
                    action=action,
                    code="payload_mismatch",
                    message="api and cli JSON payloads differ after canonicalization",
                )
            )

    return WorkflowApiCliParityReport(
        parity=not issues,
        actions_checked=required_actions,
        issues=tuple(issues),
    )


class ArtifactTrustLevel(StrEnum):
    """Trust level for uploaded or ingested large artifact sources."""

    TRUSTED = "trusted"
    UNKNOWN = "unknown"
    UNTRUSTED = "untrusted"


class LargeArtifactUploadDescriptor(JsonModel):
    """Descriptor for one large upload/ingestion artifact candidate."""

    model_config = ConfigDict(extra="forbid")

    artifact_name: str = Field(..., min_length=1)
    format_name: str = Field(..., min_length=1)
    file_size_bytes: int = Field(..., ge=0)
    content_sha256: str | None = None
    trust_level: ArtifactTrustLevel = ArtifactTrustLevel.UNKNOWN


class LargeArtifactUploadGuardPolicy(JsonModel):
    """Policy for size/format/trust checks over uploaded large artifacts."""

    model_config = ConfigDict(extra="forbid")

    max_size_bytes_total: int = Field(..., ge=1)
    max_size_bytes_by_format: dict[str, int] = Field(default_factory=dict)
    allowed_formats: tuple[str, ...] = Field(default_factory=tuple)
    require_content_hash: bool = True
    max_untrusted_size_bytes: int = Field(default=100_000_000, ge=1)


class LargeArtifactUploadGuardDecision(JsonModel):
    """Decision for one artifact after upload guard checks."""

    model_config = ConfigDict(extra="forbid")

    artifact_name: str = Field(..., min_length=1)
    accepted: bool
    reasons: tuple[str, ...] = Field(default_factory=tuple)


class LargeArtifactUploadGuardReport(JsonModel):
    """Aggregate upload/ingestion guard report for large artifacts."""

    model_config = ConfigDict(extra="forbid")

    accepted: bool
    decisions: tuple[LargeArtifactUploadGuardDecision, ...] = Field(default_factory=tuple)


def guard_large_artifact_uploads(
    *,
    artifacts: tuple[LargeArtifactUploadDescriptor, ...],
    policy: LargeArtifactUploadGuardPolicy,
) -> LargeArtifactUploadGuardReport:
    """Protect large spectra/search/quant uploads with size, format, and trust checks."""

    allowed_formats = set(policy.allowed_formats)
    decisions: list[LargeArtifactUploadGuardDecision] = []

    for artifact in artifacts:
        reasons: list[str] = []
        if artifact.format_name not in allowed_formats:
            reasons.append(f"unsupported format: {artifact.format_name}")

        format_limit = policy.max_size_bytes_by_format.get(
            artifact.format_name, policy.max_size_bytes_total
        )
        if artifact.file_size_bytes > format_limit:
            reasons.append(
                f"format size limit exceeded ({artifact.file_size_bytes} > {format_limit})"
            )
        if artifact.file_size_bytes > policy.max_size_bytes_total:
            reasons.append(
                f"global size limit exceeded ({artifact.file_size_bytes} > "
                f"{policy.max_size_bytes_total})"
            )
        if (
            artifact.trust_level is ArtifactTrustLevel.UNTRUSTED
            and artifact.file_size_bytes > policy.max_untrusted_size_bytes
        ):
            reasons.append(
                "untrusted artifact exceeds max_untrusted_size_bytes policy threshold"
            )
        if policy.require_content_hash and not artifact.content_sha256:
            reasons.append("content hash is required for upload verification")

        decisions.append(
            LargeArtifactUploadGuardDecision(
                artifact_name=artifact.artifact_name,
                accepted=not reasons,
                reasons=tuple(reasons),
            )
        )

    accepted = all(decision.accepted for decision in decisions)
    return LargeArtifactUploadGuardReport(accepted=accepted, decisions=tuple(decisions))
