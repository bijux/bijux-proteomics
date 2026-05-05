# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable route contracts for adapter conformance reporting."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class AdapterConformanceRouteRequest(JsonModel):
    """Stable API request for adapter conformance reporting routes."""

    model_config = ConfigDict(extra="forbid")

    adapter_id: str = Field(..., min_length=1)
    mapped_fields: tuple[str, ...] = Field(default_factory=tuple)
    lost_fields: tuple[str, ...] = Field(default_factory=tuple)
    unsupported_fields: tuple[str, ...] = Field(default_factory=tuple)
    raw_evidence_policy: str = Field(..., min_length=1)


class AdapterConformanceRouteResponse(JsonModel):
    """Stable API response for adapter conformance reporting routes."""

    model_config = ConfigDict(extra="forbid")

    adapter_id: str = Field(..., min_length=1)
    schema_ref: str = Field(..., min_length=1)
    report_pointer: str = Field(..., min_length=1)
    mapped_fields: tuple[str, ...] = Field(default_factory=tuple)
    lost_fields: tuple[str, ...] = Field(default_factory=tuple)
    unsupported_fields: tuple[str, ...] = Field(default_factory=tuple)
    raw_evidence_policy: str = Field(..., min_length=1)


def route_adapter_conformance_api(
    payload: AdapterConformanceRouteRequest,
) -> AdapterConformanceRouteResponse:
    """Expose mapped/lost/unsupported adapter fields and raw evidence policy."""

    return AdapterConformanceRouteResponse(
        adapter_id=payload.adapter_id,
        schema_ref="api.adapter-conformance.route.v1",
        report_pointer=f"adapter/conformance/{payload.adapter_id}",
        mapped_fields=tuple(sorted(set(payload.mapped_fields))),
        lost_fields=tuple(sorted(set(payload.lost_fields))),
        unsupported_fields=tuple(sorted(set(payload.unsupported_fields))),
        raw_evidence_policy=payload.raw_evidence_policy,
    )


__all__ = [
    "AdapterConformanceRouteRequest",
    "AdapterConformanceRouteResponse",
    "route_adapter_conformance_api",
]
