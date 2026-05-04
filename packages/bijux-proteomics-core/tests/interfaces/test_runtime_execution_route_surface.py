# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.interfaces.api import (
    RuntimeExecutionRouteRequest,
    route_runtime_execution_api,
)


def test_route_runtime_execution_api_exposes_artifact_and_route_pointer() -> None:
    response = route_runtime_execution_api(
        RuntimeExecutionRouteRequest(
            operation="artifacts",
            workflow_id="workflow.dda-import",
            run_id="run-001",
        )
    )

    assert response.schema_ref == "api.runtime-execution.route.v1"
    assert response.route_pointer == "runtime/artifacts/run-001"
    assert (
        response.artifact_pointer
        == "artifacts/runtime/workflow.dda-import/run-001.json"
    )
