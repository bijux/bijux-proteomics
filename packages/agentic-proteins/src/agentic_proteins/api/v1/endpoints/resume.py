# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Resume endpoint."""

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
    ResumeRequest,
    RunResponse,
)
from agentic_proteins.core.status import WorkflowState
from agentic_proteins.interfaces.cli import _load_run_summary, _resume_candidate

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
    base_dir: Annotated[Path, Depends(get_base_dir)],
) -> ApiEnvelope:
    """resume_endpoint."""
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
            summary = _load_run_summary(
                base_dir,
                run_id,
                artifacts_dir,
            )
            if not candidate_id:
                candidate_id = summary.get("candidate_id") or f"{run_id}-c0"
            workflow_state = summary.get("workflow_state")
            if workflow_state == WorkflowState.DONE.value:
                raise RuntimeError(f"Run {run_id} already completed.")
        result = _resume_candidate(
            base_dir,
            candidate_id,
            payload.rounds,
            payload.provider,
            artifacts_dir,
            payload.execution_mode,
        )
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
