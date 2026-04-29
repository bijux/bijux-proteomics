# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Request and trace correlation helpers for runtime API and CLI surfaces."""

from __future__ import annotations

import hashlib

from fastapi import Request


def build_trace_id(
    surface: str,
    request_id: str,
    correlation_key: str | None = None,
) -> str:
    """Build a stable trace id for one surface interaction."""
    material = f"{surface}:{request_id}:{correlation_key or ''}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:20]


def build_correlation_meta(
    surface: str,
    request_id: str,
    correlation_key: str | None = None,
) -> dict[str, str]:
    """Return the shared correlation metadata envelope."""
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
    """Return correlation metadata for one HTTP request."""
    request_id = getattr(request.state, "request_id", "unknown")
    return build_correlation_meta(surface, request_id, correlation_key)
