# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Core tool invocation schemas."""

from __future__ import annotations

from enum import Enum
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from agentic_proteins.core.hashing import sha256_hex


class ToolDeterminism(Enum):
    """ToolDeterminism."""

    DETERMINISTIC = "deterministic"
    STOCHASTIC = "stochastic"


class SchemaDefinition(BaseModel):
    """SchemaDefinition."""

    model_config = ConfigDict(extra="forbid")

    schema_name: str = Field(..., min_length=1, description="Schema identifier.")
    json_schema: str = Field(..., min_length=1, description="JSON schema string.")


class ToolContract(BaseModel):
    """ToolContract."""

    model_config = ConfigDict(extra="forbid")

    tool_name: str = Field(..., min_length=1, description="Tool identifier.")
    version: str = Field(..., min_length=1, description="Tool version.")
    input_schema: SchemaDefinition = Field(..., description="Input schema.")
    output_schema: SchemaDefinition = Field(..., description="Output schema.")
    failure_modes: list[str] = Field(
        default_factory=list, description="Failure mode codes."
    )
    cost_estimate: float = Field(0.0, gt=0.0, description="Cost estimate.")
    latency_estimate_ms: int = Field(1, gt=0, description="Latency estimate in ms.")
    determinism: ToolDeterminism = Field(
        ToolDeterminism.DETERMINISTIC,
        description="Determinism classification.",
    )


class ToolDescriptor(BaseModel):
    """ToolDescriptor."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, description="Tool identifier.")
    input_schema: SchemaDefinition = Field(..., description="Input schema.")
    output_schema: SchemaDefinition = Field(..., description="Output schema.")
    cost_estimate: float = Field(0.0, ge=0.0, description="Estimated cost units.")
    latency_estimate_ms: int = Field(0, ge=0, description="Estimated latency in ms.")


class InvocationInput(BaseModel):
    """InvocationInput."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, description="Input identifier.")
    value: str = Field(..., min_length=1, description="Input value.")


class OutputExpectation(BaseModel):
    """OutputExpectation."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, description="Output identifier.")
    schema_version: str = Field(..., min_length=1, description="Output schema version.")


class ToolInvocationSpec(BaseModel):
    """ToolInvocationSpec."""

    model_config = ConfigDict(extra="forbid")

    invocation_id: str = Field(..., min_length=1, description="Invocation identifier.")
    tool_name: str = Field(..., min_length=1, description="Tool identifier.")
    tool_version: str = Field(..., min_length=1, description="Tool version.")
    inputs: list[InvocationInput] = Field(
        default_factory=list, description="Structured inputs."
    )
    expected_outputs: list[OutputExpectation] = Field(
        default_factory=list,
        description="Expected outputs.",
    )
    constraints: list[str] = Field(
        default_factory=list, description="Constraint codes."
    )
    origin_task_id: str = Field(
        ..., min_length=1, description="Originating task identifier."
    )


class ToolError(BaseModel):
    """ToolError."""

    model_config = ConfigDict(extra="forbid")

    error_type: str = Field(..., min_length=1, description="Error type identifier.")
    message: str = Field(..., min_length=1, description="Error message code.")


class ToolMetric(BaseModel):
    """ToolMetric."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, description="Metric identifier.")
    value: float = Field(0.0, description="Metric value.")
    unit: str = Field(..., min_length=1, description="Metric unit.")


class ToolResult(BaseModel):
    """ToolResult."""

    model_config = ConfigDict(extra="forbid")

    invocation_id: str = Field(..., min_length=1, description="Invocation identifier.")
    tool_name: str = Field(..., min_length=1, description="Tool identifier.")
    status: Literal["success", "failure"] = Field(
        "success",
        description="success or failure.",
    )
    outputs: list[InvocationInput] = Field(
        default_factory=list, description="Structured outputs."
    )
    metrics: list[ToolMetric] = Field(
        default_factory=list, description="Metric values."
    )
    error: ToolError | None = Field(default=None, description="Failure details.")

    def fingerprint(self, tool_version: str, inputs: list[InvocationInput]) -> str:
        """fingerprint."""
        normalized = {
            "tool_name": self.tool_name,
            "tool_version": tool_version,
            "inputs": [item.model_dump() for item in inputs],
            "outputs": [item.model_dump() for item in self.outputs],
            "metrics": [item.model_dump() for item in self.metrics],
            "status": self.status,
            "error": self.error.model_dump() if self.error else None,
        }
        payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
        return sha256_hex(payload)
