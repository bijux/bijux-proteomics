# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""External import endpoint."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from bijux_proteomics_runtime.api.correlation import build_request_correlation_meta
from bijux_proteomics_runtime.api.deps import get_base_dir
from bijux_proteomics_runtime.api.errors import raise_http_error
from bijux_proteomics_runtime.api.v1.schema import (
    ApiEnvelope,
    ErrorResponse,
    ImportRequest,
    RunResponse,
)
from bijux_proteomics_runtime.runtime.control import (
    import_external_result_operation,
    load_run_summary_operation,
)

router = APIRouter()


@router.post(
    "/import",
    response_model=ApiEnvelope,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
def import_endpoint(
    payload: ImportRequest,
    request: Request,
    base_dir: Annotated[Path, Depends(get_base_dir)],
) -> ApiEnvelope:
    """Import one external-engine result through the canonical runtime surface."""
    meta = build_request_correlation_meta(request, "import", request.url.path)
    try:
        source_path = Path(payload.source_path)
        if not source_path.is_absolute():
            source_path = base_dir / source_path
        artifacts_dir = None
        if payload.artifacts_dir:
            artifacts_dir = Path(payload.artifacts_dir)
            if not artifacts_dir.is_absolute():
                artifacts_dir = base_dir / artifacts_dir
        result = import_external_result_operation(
            base_dir,
            sequence=payload.sequence,
            source_path=source_path,
            engine_name=payload.engine_name,
            engine_version=payload.engine_version,
            artifacts_dir=artifacts_dir,
        )
        run_id_obj = result.get("run_id")
        if not isinstance(run_id_obj, str) or not run_id_obj:
            raise ValueError("import output missing run_id")
        response = RunResponse.model_validate(
            load_run_summary_operation(base_dir, run_id_obj, artifacts_dir)
        )
        return ApiEnvelope(status="ok", data=response, error=None, meta=meta)
    except Exception as exc:  # noqa: BLE001
        raise_http_error(exc, str(request.url), meta=meta)
