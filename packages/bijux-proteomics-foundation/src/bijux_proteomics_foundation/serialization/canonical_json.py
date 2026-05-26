# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Deterministic canonical JSON helpers for durable document payloads."""

from __future__ import annotations

from datetime import datetime
import json
from typing import TYPE_CHECKING, Any

from bijux_proteomics_foundation.serialization.stable_values import stable_order_value

if TYPE_CHECKING:
    from bijux_proteomics_foundation.serialization.json_contracts import JsonModel


def normalize_json_value(value: Any) -> Any:
    """Return one value normalized for deterministic JSON serialization."""
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    return stable_order_value(value)


def flatten_tsv_mapping(value: Any, *, prefix: str = "") -> dict[str, str]:
    """Flatten one normalized payload into a deterministic TSV-ready mapping."""
    if isinstance(value, dict):
        flattened: dict[str, str] = {}
        for key, inner in sorted(value.items(), key=lambda item: str(item[0])):
            nested_prefix = f"{prefix}.{key}" if prefix else str(key)
            flattened.update(flatten_tsv_mapping(inner, prefix=nested_prefix))
        return flattened
    if isinstance(value, list):
        return {prefix: json.dumps(value, separators=(",", ":"))}
    if value is None:
        return {prefix: ""}
    return {prefix: str(value)}


def to_canonical_json(model: JsonModel | dict[str, Any]) -> str:
    """Serialize one model or payload with deterministic key ordering.

    Inputs:
    ``model`` must be either a foundation ``JsonModel`` or a JSON-compatible
    mapping that can be normalized into canonical value order.

    Outputs:
    Returns one canonical JSON string with sorted keys and deterministic
    separators.

    Failure Modes:
    Propagates normalization or JSON serialization failures for unsupported
    values.

    Scientific Caveats:
    Canonical serialization stabilizes persisted payload shape only; it does not
    validate scientific semantics or preserve every Python type distinction.
    """
    from bijux_proteomics_foundation.serialization.json_contracts import JsonModel

    payload = (
        model.to_dict() if isinstance(model, JsonModel) else normalize_json_value(model)
    )
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


__all__ = ["flatten_tsv_mapping", "normalize_json_value", "to_canonical_json"]
