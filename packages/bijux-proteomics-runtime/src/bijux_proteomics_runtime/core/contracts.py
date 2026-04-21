# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Frozen contracts for agent execution."""

from __future__ import annotations

AGENT_EXECUTION_CONTRACT = {
    "step_entrypoint": "bijux_proteomics.biology.pathway.PathwayExecutor.step",
    "transition_validator": "bijux_proteomics.biology.validation.validate_transition",
    "failure_semantics": "bijux_proteomics.biology.protein_agent.FailureEvent",
    "failure_disable": "bijux_proteomics.biology.protein_agent.ProteinFailure.DISABLED",
}

__all__ = ["AGENT_EXECUTION_CONTRACT"]
