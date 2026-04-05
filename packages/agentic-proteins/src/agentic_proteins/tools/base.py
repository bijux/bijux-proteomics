# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Tool base classes."""

from __future__ import annotations

from abc import ABC, abstractmethod

from agentic_proteins.tools.schemas import InvocationInput, ToolError, ToolResult


class Tool(ABC):
    """Tool."""

    name: str = ""
    version: str = "v1"

    @abstractmethod
    def run(self, invocation_id: str, inputs: list[InvocationInput]) -> ToolResult:
        """Run the tool against structured inputs."""

    @staticmethod
    def _inputs_to_dict(inputs: list[InvocationInput]) -> dict[str, str]:
        """_inputs_to_dict."""
        return {item.name: item.value for item in inputs}

    def _error_result(self, invocation_id: str, message: str) -> ToolResult:
        """_error_result."""
        return ToolResult(
            invocation_id=invocation_id,
            tool_name=self.name,
            status="failure",
            outputs=[],
            metrics=[],
            error=ToolError(error_type="tool_error", message=message),
        )
