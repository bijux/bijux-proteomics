# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Hashing helpers."""

from __future__ import annotations

from bijux_proteomics_foundation import hash_text


def sha256_hex(payload: str) -> str:
    """Return a hex SHA256 digest for the payload."""
    return hash_text(payload)
