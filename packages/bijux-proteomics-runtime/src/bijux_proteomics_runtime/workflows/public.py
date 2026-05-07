"""Public workflow import surface helpers."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_WORKFLOW_EXPORT_GROUPS = {
    "bijux_proteomics_runtime.workflows.assurance": [
        "CanonicalOperatorPath",
        "WorkflowAssuranceLane",
        "WorkflowAssuranceMatrixRow",
        "WorkflowAssuranceTier",
        "build_canonical_operator_path",
        "build_workflow_assurance_matrix",
        "major_workflow_families",
        "simulation_contract_lane_ids",
        "workflow_assurance_lanes",
    ],
    "bijux_proteomics_runtime.workflows.paths": [
        "RuntimeReviewableOutputPath",
        "RuntimeSmokeWorkflow",
        "RuntimeWorkflowStep",
        "build_runtime_smoke_workflows",
        "run_reviewable_import_path",
        "run_reviewable_sequence_path",
    ],
    "bijux_proteomics_runtime.workflows.plans": [
        "DeterministicExecutionContract",
        "ExternalToolCapabilityIssue",
        "ExternalToolCapabilityReport",
        "ReproducibleWorkflowBlueprint",
        "WorkflowArtifactKind",
        "WorkflowCacheMissReason",
        "WorkflowCheckpointStatus",
        "WorkflowExecutionMode",
        "WorkflowExecutionReadinessIssue",
        "WorkflowExecutionReadinessReport",
        "WorkflowInputRole",
        "WorkflowManifestExplanationEntry",
        "WorkflowManifestExplanationReport",
        "WorkflowPathKind",
        "WorkflowResumeKind",
        "WorkflowSchedulerKind",
        "WorkflowScientificSurface",
        "WorkflowStepKind",
        "WorkflowStepProvenanceEntry",
        "WorkflowStepProvenanceReport",
        "WorkflowStepReplayDisposition",
        "WorkflowStreamingMode",
    ],
    "bijux_proteomics_runtime.workflows.reproducibility": [
        "RuntimeWorkflowBlueprint",
        "RuntimeWorkflowBlueprintStage",
        "RuntimeWorkflowBlueprintStep",
        "WorkflowRunDiffCategory",
        "WorkflowRunDiffEntry",
        "WorkflowRunDiffReport",
        "WorkflowRunSnapshot",
        "build_runtime_workflow_blueprint",
        "build_workflow_run_diff_report",
        "build_workflow_stable_error_envelope",
        "evaluate_large_artifact_upload_guard",
        "evaluate_workflow_api_cli_parity",
        "verify_portable_run_bundle",
    ],
    "bijux_proteomics_runtime.workflows.runs": [
        "DdaImportWorkflowRunReport",
        "DdaSearchHitInput",
        "DiaImportWorkflowRunReport",
        "DiaPrecursorQuantInput",
        "KnowledgeEvidenceInput",
        "KnowledgeReviewWorkflowRunReport",
        "PtmRuntimeWorkflowRunReport",
        "QuantRuntimeWorkflowRunReport",
        "RuntimeWorkflowStatus",
        "RuntimeWorkflowStepRecord",
        "SequenceToDigestWorkflowRunReport",
    ],
}

_WORKFLOW_EXPORTS = {
    name: (module_name, name)
    for module_name, names in _WORKFLOW_EXPORT_GROUPS.items()
    for name in names
}

__all__ = sorted(_WORKFLOW_EXPORTS)


def __getattr__(name: str) -> Any:
    """Load workflow exports lazily to avoid package-import cycles."""

    target = _WORKFLOW_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute_name = target
    module = import_module(module_name)
    return getattr(module, attribute_name)
