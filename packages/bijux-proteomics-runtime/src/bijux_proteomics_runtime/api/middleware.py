# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""API middleware."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a request id header for tracing."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        """Inject a request id for correlation across logs."""
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Log request/response metadata with correlation id."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        """Log request lifecycle."""
        start = time.perf_counter()
        request_id = request.headers.get("x-request-id") or getattr(
            request.state, "request_id", "unknown"
        )
        base_dir = getattr(request.app.state, "base_dir", None)
        log_path = None
        if isinstance(base_dir, Path):
            log_path = base_dir / "artifacts" / "api" / "requests.jsonl"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            _write_log(
                log_path,
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "event": "request_start",
                    "correlation_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                },
            )
        response = await call_next(request)
        if log_path is not None:
            _write_log(
                log_path,
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "event": "request_complete",
                    "correlation_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round((time.perf_counter() - start) * 1000.0, 3),
                },
            )
        return response


def _write_log(path: Path, payload: dict[str, object]) -> None:
    """_write_log."""
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")
