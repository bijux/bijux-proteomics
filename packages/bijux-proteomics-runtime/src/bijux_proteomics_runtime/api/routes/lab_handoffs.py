# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable route contracts for lab handoff operations."""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class LabHandoffRouteRequest(JsonModel):
    """Stable API request for assay request, handoff export, and lifecycle status."""

    model_config = ConfigDict(extra="forbid")

    operation: Literal["request", "export", "status"]
    assay_request_id: str = Field(..., min_length=1)
    lifecycle_state: Literal[
        "planned", "queued", "running", "completed", "rejected"
    ] = "planned"
    export_format: Literal["json", "csv", "tsv"] = "json"


class LabHandoffRouteResponse(JsonModel):
    """Stable API response for lab handoff routes."""

    model_config = ConfigDict(extra="forbid")

    operation: str = Field(..., min_length=1)
    assay_request_id: str = Field(..., min_length=1)
    lifecycle_state: str = Field(..., min_length=1)
    schema_ref: str = Field(..., min_length=1)
    handoff_pointer: str = Field(..., min_length=1)


def route_lab_handoff_api(
    payload: LabHandoffRouteRequest,
) -> LabHandoffRouteResponse:
    """Route lab handoff operations through a stable product API surface."""

    pointer = f"lab/{payload.operation}/{payload.assay_request_id}"
    if payload.operation == "export":
        pointer = f"lab/export/{payload.assay_request_id}.{payload.export_format}"
    return LabHandoffRouteResponse(
        operation=payload.operation,
        assay_request_id=payload.assay_request_id,
        lifecycle_state=payload.lifecycle_state,
        schema_ref="api.lab-handoff.route.v1",
        handoff_pointer=pointer,
    )


__all__ = [
    "LabHandoffRouteRequest",
    "LabHandoffRouteResponse",
    "route_lab_handoff_api",
]
