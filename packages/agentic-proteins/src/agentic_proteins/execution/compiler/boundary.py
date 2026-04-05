# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Execution boundary interface and policy helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from agentic_proteins.tools.base import Tool
from agentic_proteins.tools.schemas import ToolError, ToolInvocationSpec, ToolResult


class ExecutionBoundary(ABC):
    """ExecutionBoundary."""

    @abstractmethod
    def execute(self, invocation: ToolInvocationSpec) -> ToolResult:
        """Execute a tool invocation."""


class ToolBoundary(ExecutionBoundary):
    """ToolBoundary."""

    def __init__(self, tools: dict[tuple[str, str], Tool]) -> None:
        """Create a boundary that dispatches to provided tools."""
        self._tools = tools

    def execute(self, invocation: ToolInvocationSpec) -> ToolResult:
        """Execute an invocation against the tool registry."""
        invocation = ToolInvocationSpec.model_validate(invocation)
        key = (invocation.tool_name, invocation.tool_version)
        tool = self._tools.get(key)
        if tool is None:
            return ToolResult(
                invocation_id=invocation.invocation_id,
                tool_name=invocation.tool_name,
                status="failure",
                outputs=[],
                metrics=[],
                error=ToolError(
                    error_type="missing_tool", message="tool_not_registered"
                ),
            )
        return tool.run(invocation.invocation_id, invocation.inputs)


def evaluate_failure(
    result: ToolResult,
    *,
    fatal_errors: set[str],
    replan_errors: set[str],
) -> str:
    """evaluate_failure."""
    if result.status != "failure":
        return "continue"
    error_type = result.error.error_type if result.error else ""
    if error_type in fatal_errors:
        return "halt"
    if error_type in replan_errors:
        return "replan"
    return "continue"
