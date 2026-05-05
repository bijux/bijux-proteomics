"""Hashing helper exports for legacy report compatibility."""

from __future__ import annotations

from bijux_proteomics_foundation import hash_text


def sha256_hex(text: str) -> str:
    """Return SHA-256 hex digest for utf-8 text."""
    return hash_text(text)
