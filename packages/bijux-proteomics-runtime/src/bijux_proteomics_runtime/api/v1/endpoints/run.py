# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Run endpoint."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from bijux_proteomics_runtime.api.errors import ok_envelope, raise_http_error
from bijux_proteomics_runtime.api.request_context import get_runtime_base_dir
from bijux_proteomics_runtime.api.v1.schema import (
    ApiEnvelope,
    ErrorResponse,
    RunRequest,
    RunResponse,
)
from bijux_proteomics_runtime.support.primitives.status import WorkflowState
from bijux_proteomics_runtime.api.cli import (
    _read_sequence,
    _validate_sequence,
)
from bijux_proteomics_runtime.runs.correlation import (
    build_request_correlation_meta,
)
from bijux_proteomics_runtime.runs.operations import (
    build_runtime_run_config,
    load_run_summary_operation,
    run_sequence_operation,
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
    base_dir: Annotated[Path, Depends(get_runtime_base_dir)],
) -> ApiEnvelope | JSONResponse:
    """run_endpoint."""
    meta = build_request_correlation_meta(request, "run", request.url.path)
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
        config = build_runtime_run_config(
            rounds=payload.rounds,
            dry_run=payload.dry_run,
            logging_enabled=True,
            provider=payload.provider,
            artifacts_dir=artifacts_dir,
            execution_mode=payload.execution_mode,
        )
        result = run_sequence_operation(base_dir, seq, config)
        run_id_obj = result.get("run_id")
        if not isinstance(run_id_obj, str) or not run_id_obj:
            raise ValueError("run output missing run_id")
        run_id = run_id_obj
        summary = load_run_summary_operation(base_dir, run_id, artifacts_dir)
        response = RunResponse.model_validate(summary)
    except Exception as exc:  # noqa: BLE001
        raise_http_error(exc, str(request.url), meta=meta)

    if response.workflow_state == WorkflowState.AWAITING_HUMAN_REVIEW:
        return JSONResponse(
            content=ok_envelope(response.model_dump(mode="json"), meta=meta),
            status_code=status.HTTP_202_ACCEPTED,
        )
    return ApiEnvelope(status="ok", data=response, error=None, meta=meta)
