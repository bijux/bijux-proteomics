# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Fingerprint utilities."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def stable_json(payload: dict[str, Any]) -> str:
    """stable_json."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def hash_payload(payload: dict[str, Any]) -> str:
    """hash_payload."""
    data = stable_json(payload)
    return hashlib.sha256(data.encode()).hexdigest()
