# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Surface-area budgets for public interfaces."""

from __future__ import annotations

PUBLIC_ENTRYPOINTS = (
    "agentic_proteins.interfaces.cli.cli",
    "agentic_proteins.runtime.RunManager",
    "agentic_proteins.biology.PathwayExecutor",
    "agentic_proteins.biology.ProteinAgent",
    "agentic_proteins.biology.SignalPayload",
)

EXTENSION_POINTS = (
    "agentic_proteins.providers",
    "agentic_proteins.tools",
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
