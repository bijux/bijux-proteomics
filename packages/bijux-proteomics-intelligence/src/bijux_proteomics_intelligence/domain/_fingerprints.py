"""Deterministic payload fingerprint helpers for intelligence domain objects."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any


def hash_payload(payload: dict[str, Any]) -> str:
    """Return a stable hash for JSON-compatible payloads."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()
