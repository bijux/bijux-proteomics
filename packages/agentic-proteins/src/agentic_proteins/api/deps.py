# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Shared API dependencies."""

from __future__ import annotations

from pathlib import Path

from fastapi import Request


def get_base_dir(request: Request) -> Path:
    """get_base_dir."""
    return Path(request.app.state.base_dir)
