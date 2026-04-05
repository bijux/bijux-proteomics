# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Run endpoint."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from agentic_proteins.api.deps import get_base_dir
from agentic_proteins.api.errors import ok_envelope, raise_http_error
from agentic_proteins.api.v1.schema import (
    ApiEnvelope,
    ErrorResponse,
    RunRequest,
    RunResponse,
)
from agentic_proteins.core.status import WorkflowState
from agentic_proteins.interfaces.cli import (
    _build_run_config,
    _load_run_summary,
    _read_sequence,
    _run_sequence,
    _validate_sequence,
)

router = APIRouter()


@router.post(
    "/run",
    response_model=ApiEnvelope,
    responses={
        202: {"model": ApiEnvelope},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def run_endpoint(
    payload: RunRequest,
    request: Request,
    base_dir: Annotated[Path, Depends(get_base_dir)],
) -> ApiEnvelope:
    """run_endpoint."""
    try:
        sequence_path = None
        if payload.sequence_file:
            sequence_path = Path(payload.sequence_file)
            if not sequence_path.is_absolute():
                sequence_path = base_dir / sequence_path
        seq = _read_sequence(payload.sequence, sequence_path)
        _validate_sequence(seq)
        artifacts_dir = None
        if payload.artifacts_dir:
            artifacts_dir = Path(payload.artifacts_dir)
            if not artifacts_dir.is_absolute():
                artifacts_dir = base_dir / artifacts_dir
        config = _build_run_config(
            payload.rounds,
            payload.dry_run,
            False,
            payload.provider,
            artifacts_dir,
            payload.execution_mode,
        )
        result = _run_sequence(base_dir, seq, config)
        run_id = result.get("run_id")
        summary = _load_run_summary(base_dir, run_id, artifacts_dir)
        response = RunResponse.model_validate(summary)
    except Exception as exc:  # noqa: BLE001
        raise_http_error(exc, str(request.url))

    if response.workflow_state == WorkflowState.AWAITING_HUMAN_REVIEW:
        return JSONResponse(
            content=ok_envelope(response.model_dump(mode="json")),
            status_code=status.HTTP_202_ACCEPTED,
        )
    return ApiEnvelope(status="ok", data=response, error=None, meta={})
