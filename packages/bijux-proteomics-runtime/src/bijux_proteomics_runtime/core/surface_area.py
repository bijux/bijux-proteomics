# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Surface-area budgets for public interfaces."""

from __future__ import annotations

PUBLIC_ENTRYPOINTS = (
    "bijux_proteomics_runtime.interfaces.cli.cli",
    "bijux_proteomics_runtime.runtime.RunManager",
    "bijux_proteomics.biology.PathwayExecutor",
    "bijux_proteomics.biology.ProteinAgent",
    "bijux_proteomics.biology.SignalPayload",
)

EXTENSION_POINTS = (
    "agentic_proteins.providers",
    "bijux_proteomics_runtime.tools",
    "agentic_proteins.sandbox",
)

CONFIG_KNOBS = (
    "RunConfig.seed",
    "RunConfig.artifacts_dir",
    "RunConfig.provider",
    "PathwayContract.max_incoming_signals",
    "PathwayContract.max_outgoing_signals",
    "PathwayContract.max_dependency_depth",
    "PathwayContract.activation_mass_limit",
)

SURFACE_CAPS = {
    "public_entrypoints": 5,
    "extension_points": 4,
    "config_knobs": 10,
}

__all__ = [
    "CONFIG_KNOBS",
    "EXTENSION_POINTS",
    "PUBLIC_ENTRYPOINTS",
    "SURFACE_CAPS",
]
