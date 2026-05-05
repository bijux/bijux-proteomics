# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Runtime correlation helpers shared by operator-facing surfaces."""

from __future__ import annotations

import hashlib

from fastapi import Request


def build_trace_id(
    surface: str,
    request_id: str,
    correlation_key: str | None = None,
) -> str:
    """Build a stable trace identifier for one operator interaction."""
    material = f"{surface}:{request_id}:{correlation_key or ''}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:20]


def build_correlation_meta(
    surface: str,
    request_id: str,
    correlation_key: str | None = None,
) -> dict[str, str]:
    """Return the shared runtime correlation envelope."""
    return {
        "surface": surface,
        "request_id": request_id,
        "trace_id": build_trace_id(surface, request_id, correlation_key),
    }


def build_request_correlation_meta(
    request: Request,
    surface: str,
    correlation_key: str | None = None,
) -> dict[str, str]:
    """Build correlation metadata from one HTTP request state."""
    request_id = getattr(request.state, "request_id", "unknown")
    return build_correlation_meta(surface, request_id, correlation_key)


__all__ = [
    "build_correlation_meta",
    "build_request_correlation_meta",
    "build_trace_id",
]
