# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Hashing helpers."""

from __future__ import annotations

import hashlib


def sha256_hex(payload: str) -> str:
    """Return a hex SHA256 digest for the payload."""
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
