# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility wrapper for canonical serialization primitives."""

from __future__ import annotations

from typing import Any

from bijux_proteomics_foundation.serialization.canonicalization import (
    flatten_tsv_mapping,
    normalize_json_value,
    to_canonical_json,
)


__all__ = ["flatten_tsv_mapping", "normalize_json_value", "to_canonical_json"]
