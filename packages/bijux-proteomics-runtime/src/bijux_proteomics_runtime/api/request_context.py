# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""FastAPI request helpers for runtime-owned base-directory access."""

from __future__ import annotations

from pathlib import Path

from fastapi import Request


def get_runtime_base_dir(request: Request) -> Path:
    """Return the runtime base directory attached to the FastAPI app state."""
    return Path(request.app.state.base_dir)


__all__ = ["get_runtime_base_dir"]
