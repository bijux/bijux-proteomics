# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Request correlation and logging middleware for runtime HTTP surfaces."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from bijux_proteomics_runtime.runs.correlation import build_trace_id


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach request and trace identifiers for runtime HTTP surfaces."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Inject stable request metadata before the request is handled."""
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id
        request.state.trace_id = build_trace_id(
            request.url.path,
            request_id,
            request.url.path,
        )
        response: Response = await call_next(request)
        response.headers["x-request-id"] = request_id
        response.headers["x-trace-id"] = request.state.trace_id
        return response


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Persist request lifecycle events into the runtime artifacts tree."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Log request start and completion with shared correlation metadata."""
        start = time.perf_counter()
        request_id = request.headers.get("x-request-id") or getattr(
            request.state, "request_id", "unknown"
        )
        trace_id = getattr(request.state, "trace_id", "unknown")
        base_dir = getattr(request.app.state, "base_dir", None)
        log_path: Path | None = None
        if isinstance(base_dir, Path):
            log_path = base_dir / "artifacts" / "api" / "requests.jsonl"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            _append_request_log(
                log_path,
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "event": "request_start",
                    "correlation_id": request_id,
                    "trace_id": trace_id,
                    "method": request.method,
                    "path": request.url.path,
                },
            )
        response: Response = await call_next(request)
        if log_path is not None:
            _append_request_log(
                log_path,
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "event": "request_complete",
                    "correlation_id": request_id,
                    "trace_id": trace_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round((time.perf_counter() - start) * 1000.0, 3),
                },
            )
        return response


def _append_request_log(path: Path, payload: dict[str, object]) -> None:
    """Append one runtime HTTP request event to a JSONL log."""
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
