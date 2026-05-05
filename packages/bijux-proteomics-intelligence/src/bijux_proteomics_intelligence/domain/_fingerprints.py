"""Deterministic payload fingerprint helpers for intelligence domain objects."""

from __future__ import annotations

from typing import Any

from bijux_proteomics_foundation import hash_payload as foundation_hash_payload


def hash_payload(payload: dict[str, Any]) -> str:
    """Return a stable hash for JSON-compatible payloads."""
    return foundation_hash_payload(payload)
