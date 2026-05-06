# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Fingerprint utilities."""

from __future__ import annotations

from typing import Any

from bijux_proteomics_foundation import hash_payload as foundation_hash_payload
from bijux_proteomics_foundation import to_canonical_json


def stable_json(payload: dict[str, Any]) -> str:
    """stable_json."""
    return to_canonical_json(payload)


def hash_payload(payload: dict[str, Any]) -> str:
    """hash_payload."""
    return foundation_hash_payload(payload)
