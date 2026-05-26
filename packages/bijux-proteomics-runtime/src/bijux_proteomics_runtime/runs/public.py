"""Public run import surface helpers."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bijux_proteomics_runtime.runs.analysis import RunAnalysis, ToolStats
    from bijux_proteomics_runtime.runs.context import RunContext, create_run_context
    from bijux_proteomics_runtime.runs.contracts import (
        DatasetIdentity,
        RunContextContract,
        RunLineage,
        RuntimeArtifactPolicy,
        RuntimeArtifactRetentionClass,
        RuntimeDatasetKind,
        RuntimeEnvironmentIdentity,
        WorkflowIdentity,
        build_run_context_contract,
        build_runtime_environment,
        default_runtime_artifact_policy,
    )
    from bijux_proteomics_runtime.runs.lifecycle import RunLifecycleState
    from bijux_proteomics_runtime.runs.logging import (
        NoopStructuredLogger,
        StructuredLogger,
    )
    from bijux_proteomics_runtime.runs.manager import RunManager, run_flow
    from bijux_proteomics_runtime.runs.operations import (
        build_runtime_run_config,
        compare_run_operation,
        export_report_operation,
        import_external_result_operation,
        inspect_candidate_operation,
        load_run_config_operation,
        load_run_summary_operation,
        resume_candidate_operation,
        run_sequence_operation,
    )
    from bijux_proteomics_runtime.runs.output import (
        ErrorDetail,
        RunOutput,
        RunStatus,
        RuntimeFlowResult,
        VersionInfo,
    )
    from bijux_proteomics_runtime.runs.request import RunRequest
    from bijux_proteomics_runtime.runs.run_config import RunConfig
    from bijux_proteomics_runtime.runs.telemetry import (
        TelemetryClient,
        TelemetrySample,
    )
    from bijux_proteomics_runtime.runs.tool_reliability import (
        ToolReliabilityTracker,
    )

_RUN_EXPORT_GROUPS = {
    "bijux_proteomics_runtime.runs.contracts": [
        "DatasetIdentity",
        "RunContextContract",
        "RunLineage",
        "RuntimeArtifactPolicy",
        "RuntimeArtifactRetentionClass",
        "RuntimeDatasetKind",
        "RuntimeEnvironmentIdentity",
        "WorkflowIdentity",
        "build_run_context_contract",
        "build_runtime_environment",
        "default_runtime_artifact_policy",
    ],
    "bijux_proteomics_runtime.runs.context": [
        "RunContext",
        "create_run_context",
    ],
    "bijux_proteomics_runtime.runs.run_config": ["RunConfig"],
    "bijux_proteomics_runtime.runs.lifecycle": ["RunLifecycleState"],
    "bijux_proteomics_runtime.runs.output": [
        "ErrorDetail",
        "RuntimeFlowResult",
        "RunOutput",
        "RunStatus",
        "VersionInfo",
    ],
    "bijux_proteomics_runtime.runs.analysis": [
        "RunAnalysis",
        "ToolStats",
    ],
    "bijux_proteomics_runtime.runs.logging": [
        "NoopStructuredLogger",
        "StructuredLogger",
    ],
    "bijux_proteomics_runtime.runs.request": ["RunRequest"],
    "bijux_proteomics_runtime.runs.manager": [
        "RunManager",
        "run_flow",
    ],
    "bijux_proteomics_runtime.runs.telemetry": [
        "TelemetryClient",
        "TelemetrySample",
    ],
    "bijux_proteomics_runtime.runs.tool_reliability": [
        "ToolReliabilityTracker",
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
}

_RUN_EXPORTS = {
    name: (module_name, name)
    for module_name, names in _RUN_EXPORT_GROUPS.items()
    for name in names
}

__all__ = (
    "DatasetIdentity",
    "ErrorDetail",
    "NoopStructuredLogger",
    "RunAnalysis",
    "RunConfig",
    "RunContext",
    "RunContextContract",
    "RunLifecycleState",
    "RunLineage",
    "RunManager",
    "RunOutput",
    "RunRequest",
    "RunStatus",
    "RuntimeArtifactPolicy",
    "RuntimeArtifactRetentionClass",
    "RuntimeDatasetKind",
    "RuntimeEnvironmentIdentity",
    "RuntimeFlowResult",
    "StructuredLogger",
    "TelemetryClient",
    "TelemetrySample",
    "ToolReliabilityTracker",
    "ToolStats",
    "VersionInfo",
    "WorkflowIdentity",
    "build_run_context_contract",
    "build_runtime_environment",
    "build_runtime_run_config",
    "compare_run_operation",
    "create_run_context",
    "default_runtime_artifact_policy",
    "export_report_operation",
    "import_external_result_operation",
    "inspect_candidate_operation",
    "load_run_config_operation",
    "load_run_summary_operation",
    "resume_candidate_operation",
    "run_flow",
    "run_sequence_operation",
)


def __getattr__(name: str) -> Any:
    """Load run-owned exports lazily to avoid package-import cycles."""

    target = _RUN_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute_name = target
    module = import_module(module_name)
    return getattr(module, attribute_name)
