# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable route contracts for evidence graph queries."""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class EvidenceGraphQueryRouteRequest(JsonModel):
    """Stable API request for evidence graph entity queries."""

    model_config = ConfigDict(extra="forbid")

    query_kind: Literal[
        "claim",
        "candidate",
        "protein",
        "peptide",
        "ptm",
        "sample",
        "run",
    ]
    query_id: str = Field(..., min_length=1)
    max_results: int = Field(default=25, ge=1, le=1000)


class EvidenceGraphQueryRouteResponse(JsonModel):
    """Stable API response for evidence graph queries."""

    model_config = ConfigDict(extra="forbid")

    query_kind: str = Field(..., min_length=1)
    query_id: str = Field(..., min_length=1)
    schema_ref: str = Field(..., min_length=1)
    query_pointer: str = Field(..., min_length=1)
    result_count_hint: int = Field(..., ge=0)


def route_evidence_graph_query_api(
    payload: EvidenceGraphQueryRouteRequest,
) -> EvidenceGraphQueryRouteResponse:
    """Route evidence graph entity queries through a stable API schema."""

    return EvidenceGraphQueryRouteResponse(
        query_kind=payload.query_kind,
        query_id=payload.query_id,
        schema_ref="api.evidence-graph.query.v1",
        query_pointer=f"evidence/{payload.query_kind}/{payload.query_id}",
        result_count_hint=payload.max_results,
    )


__all__ = [
    "EvidenceGraphQueryRouteRequest",
    "EvidenceGraphQueryRouteResponse",
    "route_evidence_graph_query_api",
]
