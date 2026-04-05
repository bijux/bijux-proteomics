# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from datetime import datetime

from agentic_proteins.execution.runtime.executor import materialize_observation
from agentic_proteins.execution.schemas import ExecutionTask, RetryPolicy
from agentic_proteins.core.observations import Observation, ObservationSource
from agentic_proteins.tools.schemas import InvocationInput, ToolInvocationSpec, ToolMetric, ToolResult


def test_materialize_observation() -> None:
    task = ExecutionTask(
        task_id="t1",
        tool_invocation=ToolInvocationSpec(
            invocation_id="inv1",
            tool_name="sequence_validator",
            tool_version="1.0",
            inputs=[InvocationInput(name="seq", value="ACD")],
            expected_outputs=[],
            constraints=[],
            origin_task_id="t1",
        ),
        input_state_id="s1",
        expected_output_schema="schema",
        retry_policy=RetryPolicy(),
        timeout_ms=10,
    )
    result = ToolResult(
        invocation_id="inv1",
        tool_name="sequence_validator",
        status="success",
        outputs=[],
        metrics=[ToolMetric(name="latency_ms", value=1.0, unit="ms")],
        error=None,
    )
    observation = materialize_observation(result, task)
    assert isinstance(observation, Observation)
    assert observation.source == ObservationSource.TOOL
    assert observation.related_task_id == "t1"
    assert observation.tool_result_fingerprint
