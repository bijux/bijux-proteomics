# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Resume endpoint."""

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
    ResumeRequest,
    RunResponse,
)
from bijux_proteomics_runtime.core.status import WorkflowState
from bijux_proteomics_runtime.runs.correlation import (
    build_request_correlation_meta,
)
from bijux_proteomics_runtime.runs.operations import (
    load_run_summary_operation,
    resume_candidate_operation,
)

router = APIRouter()


def _run_id_from_candidate(candidate_id: str) -> str:
    """_run_id_from_candidate."""
    if "-c" in candidate_id:
        return candidate_id.rsplit("-c", 1)[0]
    return candidate_id.split("-", 1)[0]


@router.post(
    "/resume",
    response_model=ApiEnvelope,
    responses={
        202: {"model": ApiEnvelope},
        422: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
def resume_endpoint(
    payload: ResumeRequest,
    request: Request,
    base_dir: Annotated[Path, Depends(get_runtime_base_dir)],
) -> ApiEnvelope | JSONResponse:
    """resume_endpoint."""
    meta = build_request_correlation_meta(request, "resume", request.url.path)
    try:
        artifacts_dir = None
        if payload.artifacts_dir:
            artifacts_dir = Path(payload.artifacts_dir)
            if not artifacts_dir.is_absolute():
                artifacts_dir = base_dir / artifacts_dir
        candidate_id = payload.candidate_id
        run_id = payload.run_id
        if not candidate_id and not run_id:
            raise ValueError("Provide run_id or candidate_id.")
        if not run_id and candidate_id:
            run_id = _run_id_from_candidate(candidate_id)
        if run_id:
            summary = load_run_summary_operation(
                base_dir,
                run_id,
                artifacts_dir,
            )
            if not candidate_id:
                candidate_id = summary.get("candidate_id") or f"{run_id}-c0"
            workflow_state = summary.get("workflow_state")
            if workflow_state == WorkflowState.DONE.value:
                raise RuntimeError(f"Run {run_id} already completed.")
        if candidate_id is None:
            raise ValueError("candidate_id could not be resolved")
        result = resume_candidate_operation(
            base_dir,
            candidate_id=candidate_id,
            rounds=payload.rounds,
            provider=payload.provider,
            artifacts_dir=artifacts_dir,
            execution_mode=payload.execution_mode,
        )
        run_id_obj = result.get("run_id")
        if not isinstance(run_id_obj, str) or not run_id_obj:
            raise ValueError("resume output missing run_id")
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
