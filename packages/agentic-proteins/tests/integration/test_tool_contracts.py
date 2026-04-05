# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest

from agentic_proteins.registry.tools import ToolRegistry
from agentic_proteins.agents.schemas import PlannerAgentInput
from agentic_proteins.tools.schemas import (
    InvocationInput,
    OutputExpectation,
    SchemaDefinition,
    ToolContract,
    ToolDeterminism,
    ToolInvocationSpec,
    ToolResult,
)
from agentic_proteins.core.decisions import Decision
from agentic_proteins.validation.tools import validate_tools_for_agents
from tests.helpers.paths import repo_root


def register_sample_tool() -> ToolContract:
    ToolRegistry._registry.clear()
    ToolRegistry._locked = False
    contract = ToolContract(
        tool_name="sequence_validator",
        version="1.0",
        input_schema=SchemaDefinition(schema_name="seq_in", json_schema="{}"),
        output_schema=SchemaDefinition(schema_name="seq_out", json_schema="{}"),
        failure_modes=["invalid_sequence"],
        cost_estimate=1.0,
        latency_estimate_ms=1,
        determinism=ToolDeterminism.DETERMINISTIC,
    )
    ToolRegistry.register(contract)
    ToolRegistry.lock()
    return contract


def test_tool_registry_duplicate() -> None:
    register_sample_tool()
    with pytest.raises(ValueError):
        ToolRegistry.register(
            ToolContract(
                tool_name="sequence_validator",
                version="1.0",
                input_schema=SchemaDefinition(schema_name="seq_in", json_schema="{}"),
                output_schema=SchemaDefinition(schema_name="seq_out", json_schema="{}"),
                failure_modes=[],
                cost_estimate=1.0,
                latency_estimate_ms=1,
                determinism=ToolDeterminism.DETERMINISTIC,
            )
        )


def test_validate_tools_for_agents() -> None:
    register_sample_tool()
    validate_tools_for_agents({"sequence_analysis": {"sequence_validator"}})
    with pytest.raises(ValueError):
        validate_tools_for_agents({"sequence_analysis": {"missing_tool"}})


def test_tool_contract_schema_is_json_ready() -> None:
    contract = ToolContract(
        tool_name="sequence_validator",
        version="1.0",
        input_schema=SchemaDefinition(schema_name="seq_in", json_schema="{}"),
        output_schema=SchemaDefinition(schema_name="seq_out", json_schema="{}"),
        failure_modes=[],
        cost_estimate=1.0,
        latency_estimate_ms=1,
        determinism=ToolDeterminism.DETERMINISTIC,
    )
    contract.model_dump_json()


def test_tool_result_fingerprint_stable() -> None:
    result = ToolResult(
        invocation_id="inv1",
        tool_name="sequence_validator",
        status="success",
        outputs=[InvocationInput(name="valid", value="true")],
        metrics=[],
        error=None,
    )
    fingerprint_a = result.fingerprint(
        tool_version="1.0",
        inputs=[InvocationInput(name="seq", value="ACD")],
    )
    fingerprint_b = result.fingerprint(
        tool_version="1.0",
        inputs=[InvocationInput(name="seq", value="ACD")],
    )
    assert fingerprint_a == fingerprint_b


def test_tool_invocation_spec_json_ready() -> None:
    spec = ToolInvocationSpec(
        invocation_id="inv1",
        tool_name="sequence_validator",
        tool_version="1.0",
        inputs=[InvocationInput(name="seq", value="ACD")],
        expected_outputs=[OutputExpectation(name="valid", schema_version="1.0")],
        constraints=["no_cache"],
        origin_task_id="t1",
    )
    spec.model_dump_json()


def test_decision_requires_tool_invocation_specs() -> None:
    with pytest.raises(ValueError):
        Decision(
            agent_name="planner",
            rationale="r",
            requested_tools=["sequence_validator"],
            confidence=0.1,
        )


def test_agents_do_not_import_tools_package() -> None:
    root = repo_root()
    agents_dir = (
        root / "packages" / "agentic-proteins" / "src" / "agentic_proteins" / "agents"
    )
    for path in agents_dir.glob("*.py"):
        if path.name in {"__init__.py", "base.py"}:
            continue
        content = path.read_text()
        if re.search(r"agentic_proteins\\.tools", content) or re.search(
            r"agentic_proteins\\.execution", content
        ):
            raise AssertionError(f"Tool/execution import found in {path}")


def test_planner_requested_tools_reference_specs() -> None:
    register_sample_tool()
    module = importlib.import_module("agentic_proteins.agents.planning.planner")
    planner = module.PlannerAgent()
    decision = planner.decide(PlannerAgentInput())
    assert isinstance(decision.plan.tasks, dict)
