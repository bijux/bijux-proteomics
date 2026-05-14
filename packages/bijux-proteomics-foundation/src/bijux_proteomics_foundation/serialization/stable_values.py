# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Deterministic value-ordering helpers shared by serializable contracts."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
import json
from typing import Any


def stable_order_strings(values: Iterable[str]) -> tuple[str, ...]:
    """Return one deterministically sorted string tuple."""
    return tuple(sorted(values))


def stable_order_pairs(
    values: Mapping[str, Any] | Iterable[tuple[str, Any]],
) -> tuple[tuple[str, Any], ...]:
    """Return deterministically ordered key-value pairs."""
    items = values.items() if isinstance(values, Mapping) else values
    return tuple(
        sorted(
            ((str(key), stable_order_value(value)) for key, value in items),
            key=lambda item: (
                item[0],
                json.dumps(item[1], sort_keys=True, separators=(",", ":"), default=str),
            ),
        )
    )


def stable_order_value(value: Any) -> Any:
    """Normalize one value into a deterministically ordered JSON-safe form."""
    if isinstance(value, Mapping):
        return dict(
            stable_order_pairs(
                (str(mapping_key), mapping_value)
                for mapping_key, mapping_value in value.items()
            )
        )
    if isinstance(value, list):
        return [stable_order_value(item) for item in value]
    if isinstance(value, tuple):
        return [stable_order_value(item) for item in value]
    if isinstance(value, set | frozenset):
        normalized_items = [stable_order_value(item) for item in value]
        return sorted(
            normalized_items,
            key=lambda item: json.dumps(
                item,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ),
        )
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    return value
