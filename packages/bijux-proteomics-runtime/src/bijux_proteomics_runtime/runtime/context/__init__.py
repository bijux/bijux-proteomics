"""Run context and lifecycle artifacts."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_CONTEXT_EXPORT_GROUPS = {
    "bijux_proteomics_runtime.runtime.context.contracts": [
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
    "bijux_proteomics_runtime.runtime.context.context": [
        "RunContext",
        "create_run_context",
    ],
    "bijux_proteomics_runtime.runtime.context.run_config": ["RunConfig"],
    "bijux_proteomics_runtime.runtime.context.lifecycle": ["RunLifecycleState"],
    "bijux_proteomics_runtime.runtime.context.output": [
        "ErrorDetail",
        "RunOutput",
        "RunStatus",
        "VersionInfo",
    ],
    "bijux_proteomics_runtime.runtime.context.request": ["RunRequest"],
}

_CONTEXT_EXPORTS = {
    name: (module_name, name)
    for module_name, names in _CONTEXT_EXPORT_GROUPS.items()
    for name in names
}

__all__ = sorted(_CONTEXT_EXPORTS)


def __getattr__(name: str) -> Any:
    """Load runtime context exports lazily to keep package imports cycle-safe."""

    target = _CONTEXT_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute_name = target
    module = import_module(module_name)
    return getattr(module, attribute_name)
