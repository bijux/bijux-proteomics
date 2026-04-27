# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Core API lock for stability and extension control."""

from __future__ import annotations

CORE_API_FROZEN = (
    "bijux_proteomics_runtime.runtime.RunManager",
    "bijux_proteomics_runtime.runtime.infra.RunConfig",
    "bijux_proteomics_runtime.interfaces.cli.cli",
    "bijux_proteomics.biology.protein_agent.ProteinAgent",
    "bijux_proteomics_runtime.core.contracts.AGENT_EXECUTION_CONTRACT",
)

DEPRECATED_EXTENSIONS = ("agentic_proteins.providers.experimental",)

DO_NOT_EXTEND_ZONES = (
    "agentic_proteins.runtime.control",
    "agentic_proteins.runtime.infra",
)
