"""Runtime control flow primitives."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_CONTROL_EXPORT_GROUPS = {
    "bijux_proteomics_runtime.runs.artifacts": [
        "ExecutionSnapshots",
        "compare_runs",
        "require_human_decision",
    ],
    "bijux_proteomics_runtime.runtime.control.cache": [
        "RuntimeCacheClaim",
        "RuntimeCacheDecision",
        "claim_runtime_cache",
        "release_runtime_cache_claim",
    ],
    "bijux_proteomics_runtime.runs.manager": [
        "RunManager",
        "run_flow",
    ],
    "bijux_proteomics_runtime.runs.operations": [
        "build_runtime_run_config",
        "compare_run_operation",
        "export_report_operation",
        "import_external_result_operation",
        "inspect_candidate_operation",
        "load_run_config_operation",
        "load_run_summary_operation",
        "resume_candidate_operation",
        "run_sequence_operation",
    ],
    "bijux_proteomics_runtime.runs.launch_bundles": [
        "ContainerRunBundle",
        "SchedulerJobBundle",
        "build_container_run_bundle",
        "build_scheduler_job_bundle",
        "load_container_run_bundle",
        "load_scheduler_job_bundle",
    ],
    "bijux_proteomics_runtime.runs.import_lineage": [
        "ImportRunBundle",
        "RuntimeImportTrace",
        "build_import_run_bundle",
        "build_import_trace",
        "load_import_run_bundle",
        "load_import_trace",
    ],
    "bijux_proteomics_runtime.runs.integrity": [
        "ArtifactIntegrityReport",
        "LargeArtifactGuardDecision",
        "load_artifact_integrity_report",
        "verify_runtime_artifact_integrity",
    ],
    "bijux_proteomics_runtime.runs.checkpoints": [
        "ResumeCheckpoint",
        "load_resume_checkpoint",
    ],
    "bijux_proteomics_runtime.runtime.control.cleanup": [
        "RuntimeCleanupArtifact",
        "RuntimeCleanupPlan",
        "apply_runtime_cleanup_plan",
        "build_runtime_cleanup_plan",
    ],
    "bijux_proteomics_runtime.runtime.control.failure_reports": [
        "RuntimeFailureCategory",
        "RuntimeFailureReport",
        "build_runtime_failure_report",
        "classify_runtime_failure",
        "write_runtime_failure_report",
    ],
    "bijux_proteomics_runtime.runs.ledger": [
        "ArtifactLedgerEntry",
        "RuntimeArtifactLedger",
        "load_artifact_ledger",
        "refresh_runtime_artifact_ledger",
    ],
    "bijux_proteomics_runtime.runtime.control.preflight": [
        "PreflightCheck",
        "PreflightCheckState",
        "RuntimePreflightReport",
        "build_runtime_preflight_report",
    ],
    "bijux_proteomics_runtime.runtime.control.recovery": [
        "FailureRecoveryArtifact",
        "RuntimeFailureRecoveryAudit",
        "build_runtime_failure_recovery_audit",
    ],
    "bijux_proteomics_runtime.runs.replay": [
        "LocalRunBundle",
        "ReplayContract",
        "ReplayEligibility",
        "build_local_run_bundle",
        "build_replay_contract",
        "evaluate_replay_eligibility",
        "load_local_run_bundle",
    ],
    "bijux_proteomics_runtime.runs.reruns": [
        "PartialRerunPlan",
        "PartialRerunStep",
        "RuntimeDependencyNode",
        "build_partial_rerun_plan",
        "build_runtime_dependency_graph",
        "build_runtime_partial_rerun_plan",
    ],
    "bijux_proteomics_runtime.runs.state_machine": [
        "RunStateMachine",
        "apply_transition",
    ],
    "bijux_proteomics_runtime.workflows.paths": [
        "RuntimeReviewableOutputPath",
        "RuntimeSmokeWorkflow",
        "RuntimeWorkflowStep",
        "build_runtime_smoke_workflows",
        "run_reviewable_import_path",
        "run_reviewable_sequence_path",
    ],
}

_CONTROL_EXPORTS = {
    name: (module_name, name)
    for module_name, names in _CONTROL_EXPORT_GROUPS.items()
    for name in names
}

__all__ = sorted(_CONTROL_EXPORTS)


def __getattr__(name: str) -> Any:
    """Load runtime control exports lazily to avoid import-time package cycles."""

    target = _CONTROL_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute_name = target
    module = import_module(module_name)
    return getattr(module, attribute_name)
