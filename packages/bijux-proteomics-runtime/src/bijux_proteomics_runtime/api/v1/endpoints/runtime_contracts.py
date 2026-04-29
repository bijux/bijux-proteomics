# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Stable runtime review-contract endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from bijux_proteomics_runtime.api.catalog import (
    build_run_artifacts_response,
    build_run_evidence_response,
    build_run_review_response,
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
) -> ApiEnvelope:
    """Return the stable runtime status contract for one run."""
    try:
        response = build_runtime_status_response(
            base_dir,
            run_id,
            include_documents=include_documents,
        )
        return ApiEnvelope(status="ok", data=response, error=None, meta={})
    except Exception as exc:  # noqa: BLE001
        raise_http_error(exc, str(request.url))


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
    try:
        response = build_run_artifacts_response(base_dir, run_id)
        return ApiEnvelope(status="ok", data=response, error=None, meta={})
    except Exception as exc:  # noqa: BLE001
        raise_http_error(exc, str(request.url))


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
) -> ApiEnvelope:
    """Return the stable evidence-bundle surface for one run."""
    try:
        response = build_run_evidence_response(
            base_dir,
            run_id,
            include_document=include_document,
        )
        return ApiEnvelope(status="ok", data=response, error=None, meta={})
    except Exception as exc:  # noqa: BLE001
        raise_http_error(exc, str(request.url))


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
) -> ApiEnvelope:
    """Return the stable review-packet surface for one run."""
    try:
        response = build_run_review_response(
            base_dir,
            run_id,
            include_document=include_document,
        )
        return ApiEnvelope(status="ok", data=response, error=None, meta={})
    except Exception as exc:  # noqa: BLE001
        raise_http_error(exc, str(request.url))
