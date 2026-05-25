# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Core API lock for stability and extension control."""

from __future__ import annotations

CORE_API_FROZEN = (
    "bijux_proteomics_runtime.runs.RunManager",
    "bijux_proteomics_runtime.runs.RunConfig",
    "bijux_proteomics_runtime.api.cli.cli",
    "bijux_proteomics_runtime.workflows.paths.run_reviewable_sequence_path",
    "bijux_proteomics_runtime.runs.reruns.build_runtime_partial_rerun_plan",
)

DEPRECATED_EXTENSIONS = ("bijux_proteomics_runtime.providers.remote",)

DO_NOT_EXTEND_ZONES = (
    "bijux_proteomics_runtime.artifacts",
    "bijux_proteomics_runtime.parallel",
    "bijux_proteomics_runtime.resume",
    "bijux_proteomics_runtime.runs",
    "bijux_proteomics_runtime.state",
    "bijux_proteomics_runtime.streaming",
    "bijux_proteomics_runtime.support",
    "bijux_proteomics_runtime.workflows",
)
