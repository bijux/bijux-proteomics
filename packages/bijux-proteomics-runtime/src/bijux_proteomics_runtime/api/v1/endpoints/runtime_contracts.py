# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Stable runtime review-contract endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from bijux_proteomics_runtime.api.correlation import build_request_correlation_meta
from bijux_proteomics_runtime.api.catalog import (
    build_artifact_lookup_response,
    build_evidence_lookup_response,
    build_run_history_response,
    build_run_artifacts_response,
    build_run_evidence_response,
    build_run_review_response,
    build_runtime_health_response,
    build_runtime_status_response,
)
from bijux_proteomics_runtime.api.deps import get_base_dir
from bijux_proteomics_runtime.api.errors import raise_http_error
from bijux_proteomics_runtime.api.v1.schema import (
    ApiEnvelope,
    ErrorResponse,
)

router = APIRouter()


@router.get(
    "/runs/{run_id}/status",
    response_model=ApiEnvelope,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def run_status_endpoint(
    run_id: str,
    request: Request,
    base_dir: Annotated[Path, Depends(get_base_dir)],
    include_documents: bool = False,
    max_inline_bytes: int = 256000,
) -> ApiEnvelope:
    """Return the stable runtime status contract for one run."""
    meta = build_request_correlation_meta(request, "run-status", run_id)
    try:
        response = build_runtime_status_response(
            base_dir,
            run_id,
            include_documents=include_documents,
            max_inline_bytes=max_inline_bytes,
        )
        return ApiEnvelope(status="ok", data=response, error=None, meta=meta)
    except Exception as exc:  # noqa: BLE001
        raise_http_error(exc, str(request.url), meta=meta)


@router.get(
    "/runs/{run_id}/artifacts",
    response_model=ApiEnvelope,
    responses={404: {"model": ErrorResponse}},
)
def run_artifacts_endpoint(
    run_id: str,
    request: Request,
    base_dir: Annotated[Path, Depends(get_base_dir)],
) -> ApiEnvelope:
    """Return the stable artifact inventory for one run."""
    meta = build_request_correlation_meta(request, "run-artifacts", run_id)
    try:
        response = build_run_artifacts_response(base_dir, run_id)
        return ApiEnvelope(status="ok", data=response, error=None, meta=meta)
    except Exception as exc:  # noqa: BLE001
        raise_http_error(exc, str(request.url), meta=meta)


@router.get(
    "/runs/{run_id}/evidence-bundle",
    response_model=ApiEnvelope,
    responses={404: {"model": ErrorResponse}},
)
def run_evidence_endpoint(
    run_id: str,
    request: Request,
    base_dir: Annotated[Path, Depends(get_base_dir)],
    include_document: bool = False,
    max_inline_bytes: int = 256000,
) -> ApiEnvelope:
    """Return the stable evidence-bundle surface for one run."""
    meta = build_request_correlation_meta(request, "run-evidence-bundle", run_id)
    try:
        response = build_run_evidence_response(
            base_dir,
            run_id,
            include_document=include_document,
            max_inline_bytes=max_inline_bytes,
        )
        return ApiEnvelope(status="ok", data=response, error=None, meta=meta)
    except Exception as exc:  # noqa: BLE001
        raise_http_error(exc, str(request.url), meta=meta)


@router.get(
    "/runs/{run_id}/review-packet",
    response_model=ApiEnvelope,
    responses={404: {"model": ErrorResponse}},
)
def run_review_endpoint(
    run_id: str,
    request: Request,
    base_dir: Annotated[Path, Depends(get_base_dir)],
    include_document: bool = False,
    max_inline_bytes: int = 256000,
) -> ApiEnvelope:
    """Return the stable review-packet surface for one run."""
    meta = build_request_correlation_meta(request, "run-review-packet", run_id)
    try:
        response = build_run_review_response(
            base_dir,
            run_id,
            include_document=include_document,
            max_inline_bytes=max_inline_bytes,
        )
        return ApiEnvelope(status="ok", data=response, error=None, meta=meta)
    except Exception as exc:  # noqa: BLE001
        raise_http_error(exc, str(request.url), meta=meta)


@router.get(
    "/runtime-health",
    response_model=ApiEnvelope,
    responses={500: {"model": ErrorResponse}},
)
def runtime_health_endpoint(
    request: Request,
    base_dir: Annotated[Path, Depends(get_base_dir)],
) -> ApiEnvelope:
    """Return the typed runtime health report."""
    meta = build_request_correlation_meta(request, "runtime-health", request.url.path)
    try:
        response = build_runtime_health_response(base_dir)
        return ApiEnvelope(status="ok", data=response, error=None, meta=meta)
    except Exception as exc:  # noqa: BLE001
        raise_http_error(exc, str(request.url), meta=meta)


@router.get(
    "/runs/history",
    response_model=ApiEnvelope,
    responses={500: {"model": ErrorResponse}},
)
def run_history_endpoint(
    request: Request,
    base_dir: Annotated[Path, Depends(get_base_dir)],
    provider: str | None = None,
    workflow_state: str | None = None,
    outcome: str | None = None,
    candidate_id: str | None = None,
    cursor: str | None = None,
    page_size: int = 20,
    max_query_cost: int = 1000,
) -> ApiEnvelope:
    """Return the stable run-history lookup response."""
    meta = build_request_correlation_meta(request, "run-history", request.url.path)
    try:
        response = build_run_history_response(
            base_dir,
            provider=provider,
            workflow_state=workflow_state,
            outcome=outcome,
            candidate_id=candidate_id,
            cursor=cursor,
            page_size=page_size,
            max_query_cost=max_query_cost,
        )
        return ApiEnvelope(status="ok", data=response, error=None, meta=meta)
    except Exception as exc:  # noqa: BLE001
        raise_http_error(exc, str(request.url), meta=meta)


@router.get(
    "/artifacts",
    response_model=ApiEnvelope,
    responses={500: {"model": ErrorResponse}},
)
def artifact_lookup_endpoint(
    request: Request,
    base_dir: Annotated[Path, Depends(get_base_dir)],
    run_id: str | None = None,
    artifact_kind: str | None = None,
    cursor: str | None = None,
    page_size: int = 20,
    max_query_cost: int = 1000,
) -> ApiEnvelope:
    """Return the stable artifact lookup response."""
    meta = build_request_correlation_meta(request, "artifact-lookup", request.url.path)
    try:
        response = build_artifact_lookup_response(
            base_dir,
            run_id=run_id,
            artifact_kind=artifact_kind,
            cursor=cursor,
            page_size=page_size,
            max_query_cost=max_query_cost,
        )
        return ApiEnvelope(status="ok", data=response, error=None, meta=meta)
    except Exception as exc:  # noqa: BLE001
        raise_http_error(exc, str(request.url), meta=meta)


@router.get(
    "/evidence",
    response_model=ApiEnvelope,
    responses={500: {"model": ErrorResponse}},
)
def evidence_lookup_endpoint(
    request: Request,
    base_dir: Annotated[Path, Depends(get_base_dir)],
    run_id: str | None = None,
    document_kind: str | None = None,
    availability: str | None = None,
    cursor: str | None = None,
    page_size: int = 20,
    max_query_cost: int = 1000,
) -> ApiEnvelope:
    """Return the stable evidence and review lookup response."""
    meta = build_request_correlation_meta(request, "evidence-lookup", request.url.path)
    try:
        response = build_evidence_lookup_response(
            base_dir,
            run_id=run_id,
            document_kind=document_kind,
            availability=availability,
            cursor=cursor,
            page_size=page_size,
            max_query_cost=max_query_cost,
        )
        return ApiEnvelope(status="ok", data=response, error=None, meta=meta)
    except Exception as exc:  # noqa: BLE001
        raise_http_error(exc, str(request.url), meta=meta)
