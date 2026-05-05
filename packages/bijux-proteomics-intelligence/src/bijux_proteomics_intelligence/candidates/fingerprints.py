"""Deterministic payload fingerprint helpers for intelligence domain objects."""

from __future__ import annotations

from typing import Any

from bijux_proteomics_foundation import hash_payload as foundation_hash_payload
from bijux_proteomics_foundation import hash_text as foundation_hash_text


def hash_payload(payload: dict[str, Any]) -> str:
    """Return a stable hash for JSON-compatible payloads."""
    return foundation_hash_payload(payload)


def sha256_hex(text: str) -> str:
    """Return a stable SHA-256 digest for utf-8 text."""

    return foundation_hash_text(text)
