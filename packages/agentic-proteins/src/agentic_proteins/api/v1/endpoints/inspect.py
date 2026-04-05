# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Inspect endpoint."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from agentic_proteins.api.deps import get_base_dir
from agentic_proteins.api.errors import raise_http_error
from agentic_proteins.api.v1.schema import (
    ApiCandidate,
    ApiEnvelope,
    ErrorResponse,
    InspectResponse,
)
from agentic_proteins.interfaces.cli import _inspect_candidate, _load_run_summary
from agentic_proteins.runtime.workspace import RunWorkspace

router = APIRouter()


def _run_id_from_candidate(candidate_id: str) -> str:
    """_run_id_from_candidate."""
    if "-c" in candidate_id:
        return candidate_id.rsplit("-c", 1)[0]
    return candidate_id.split("-", 1)[0]


@router.get(
    "/inspect/{candidate_id}",
    response_model=ApiEnvelope,
    responses={404: {"model": ErrorResponse}},
)
def inspect_endpoint(
    candidate_id: str,
    request: Request,
    base_dir: Annotated[Path, Depends(get_base_dir)],
) -> ApiEnvelope:
    """inspect_endpoint."""
    try:
        candidate = _inspect_candidate(base_dir, candidate_id)
        api_candidate = ApiCandidate.model_validate(candidate.model_dump(mode="json"))
        run_id = _run_id_from_candidate(candidate_id)
        workspace = RunWorkspace.for_run(base_dir, run_id)
        artifacts = {
            "run_dir": str(workspace.run_dir),
            "report_path": str(workspace.report_path),
            "run_summary_path": str(workspace.run_summary_path),
        }
        qc_status = None
        if workspace.run_summary_path.exists():
            summary = _load_run_summary(base_dir, run_id, None)
            qc_status = summary.get("qc_status")
        response = InspectResponse(
            candidate=api_candidate,
            qc_status=qc_status,
            artifacts=artifacts,
        )
        return ApiEnvelope(status="ok", data=response, error=None, meta={})
    except Exception as exc:  # noqa: BLE001
        raise_http_error(exc, str(request.url))
