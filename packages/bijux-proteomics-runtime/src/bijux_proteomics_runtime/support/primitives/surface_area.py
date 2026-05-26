# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Surface-area budgets for concrete runtime interfaces."""

from __future__ import annotations

PUBLIC_ENTRYPOINTS = (
    "bijux_proteomics_runtime.api.cli.cli",
    "bijux_proteomics_runtime.api.create_app",
    "bijux_proteomics_runtime.runs.RunManager",
    "bijux_proteomics_runtime.workflows.paths.run_reviewable_sequence_path",
    "bijux_proteomics_runtime.workflows.paths.run_reviewable_import_path",
    "bijux_proteomics_runtime.workflows.architecture_demo.run_runtime_architecture_demo",
    "bijux_proteomics_runtime.workflows.package_smoke.run_runtime_package_smoke_workflow",
)

EXTENSION_POINTS = (
    "bijux_proteomics_runtime.providers",
    "bijux_proteomics_runtime.execution.tools",
    "bijux_proteomics_runtime.providers.remote",
)

CONFIG_KNOBS = (
    "RunConfig.predictors_enabled",
    "RunConfig.resource_limits",
    "RunConfig.retry_policy",
    "RunConfig.logging_enabled",
    "RunConfig.seed",
    "RunConfig.require_human_decision",
    "RunConfig.artifacts_dir",
    "RunConfig.execution_mode",
    "RunConfig.launch_surface",
    "RunConfig.max_bundle_artifact_bytes",
)

SURFACE_CAPS = {
    "public_entrypoints": 7,
    "extension_points": 3,
    "config_knobs": 10,
}

__all__ = [
    "CONFIG_KNOBS",
    "EXTENSION_POINTS",
    "PUBLIC_ENTRYPOINTS",
    "SURFACE_CAPS",
]
