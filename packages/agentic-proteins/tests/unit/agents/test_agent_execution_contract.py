# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_proteins.core.contracts import AGENT_EXECUTION_CONTRACT


def test_agent_execution_contract_is_complete() -> None:
    required = {
        "step_entrypoint",
        "transition_validator",
        "failure_semantics",
        "failure_disable",
    }
    assert required.issubset(
        AGENT_EXECUTION_CONTRACT
    ), "Agent execution contract must list step, transitions, and failure semantics."
