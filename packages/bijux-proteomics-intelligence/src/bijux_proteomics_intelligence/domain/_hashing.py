"""Hashing helper exports for legacy report compatibility."""

from __future__ import annotations

from hashlib import sha256


def sha256_hex(text: str) -> str:
    """Return SHA-256 hex digest for utf-8 text."""
    return sha256(text.encode("utf-8")).hexdigest()
