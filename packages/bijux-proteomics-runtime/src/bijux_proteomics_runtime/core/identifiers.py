# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Identifier helpers."""

from __future__ import annotations

from typing import Any

from bijux_proteomics_foundation import hash_payload


def deterministic_id(namespace: str, payload: dict[str, Any]) -> str:
    """deterministic_id."""
    return f"{namespace}_{hash_payload(payload)}"
