# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Compare endpoint."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from agentic_proteins.api.deps import get_base_dir
from agentic_proteins.api.errors import raise_http_error
from agentic_proteins.api.v1.schema import (
    ApiEnvelope,
    CompareRequest,
    CompareResponse,
    ErrorResponse,
)
from agentic_proteins.interfaces.cli import _compare_runs_payload

router = APIRouter()


@router.post(
    "/compare",
    response_model=ApiEnvelope,
    responses={
        422: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
def compare_endpoint(
    payload: CompareRequest,
    request: Request,
    base_dir: Annotated[Path, Depends(get_base_dir)],
) -> ApiEnvelope:
    """compare_endpoint."""
    try:
        run_a = Path(payload.run_id_a)
        run_b = Path(payload.run_id_b)
        if not run_a.is_absolute():
            run_a = base_dir / run_a
        if not run_b.is_absolute():
            run_b = base_dir / run_b
        comparison = _compare_runs_payload(run_a, run_b)
        response = CompareResponse.model_validate(comparison)
        return ApiEnvelope(status="ok", data=response, error=None, meta={})
    except Exception as exc:  # noqa: BLE001
        raise_http_error(exc, str(request.url))
