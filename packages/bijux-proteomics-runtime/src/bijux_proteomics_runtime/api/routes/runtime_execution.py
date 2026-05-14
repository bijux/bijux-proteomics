# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable route contracts for runtime planning and execution."""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class RuntimeExecutionRouteRequest(JsonModel):
    """Stable API request for runtime planning and execution routes."""

    model_config = ConfigDict(extra="forbid")

    operation: Literal["plan", "run", "status", "artifacts", "cache", "replay"]
    workflow_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)


class RuntimeExecutionRouteResponse(JsonModel):
    """Stable API response for runtime planning and execution routes."""

    model_config = ConfigDict(extra="forbid")

    operation: str = Field(..., min_length=1)
    workflow_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    schema_ref: str = Field(..., min_length=1)
    route_pointer: str = Field(..., min_length=1)
    artifact_pointer: str = Field(..., min_length=1)


def route_runtime_execution_api(
    payload: RuntimeExecutionRouteRequest,
) -> RuntimeExecutionRouteResponse:
    """Expose plan/run/status/artifacts/cache/replay via one stable route schema."""

    return RuntimeExecutionRouteResponse(
        operation=payload.operation,
        workflow_id=payload.workflow_id,
        run_id=payload.run_id,
        schema_ref="api.runtime-execution.route.v1",
        route_pointer=f"runtime/{payload.operation}/{payload.run_id}",
        artifact_pointer=f"artifacts/runtime/{payload.workflow_id}/{payload.run_id}.json",
    )


__all__ = [
    "RuntimeExecutionRouteRequest",
    "RuntimeExecutionRouteResponse",
    "route_runtime_execution_api",
]
