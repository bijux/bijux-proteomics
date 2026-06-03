# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Deterministic rendering helpers for stable scientific output artifacts."""

from __future__ import annotations

import json
from typing import Any


def stable_json_dumps(
    payload: Any,
    *,
    indent: int | None = 2,
    separators: tuple[str, str] | None = None,
) -> str:
    """Render one JSON payload with canonical key ordering."""

    return json.dumps(
        payload,
        indent=indent,
        sort_keys=True,
        separators=separators,
    )


def sort_rows_by_fields(rows: tuple[Any, ...], *field_names: str) -> tuple[Any, ...]:
    """Return rows sorted by one durable field tuple."""

    return tuple(
        sorted(
            rows,
            key=lambda row: tuple(
                _stable_sort_value(getattr(row, field_name))
                for field_name in field_names
            ),
        )
    )


def sort_strings(values: tuple[str, ...]) -> tuple[str, ...]:
    """Return one lexically sorted string tuple."""

    return tuple(sorted(values))


def _stable_sort_value(value: Any) -> tuple[Any, ...]:
    if value is None:
        return (0, "")
    if isinstance(value, str):
        return (1, value)
    if isinstance(value, bool):
        return (2, int(value))
    if isinstance(value, int | float):
        return (3, value)
    if isinstance(value, tuple):
        return (4, tuple(_stable_sort_value(item) for item in value))
    if hasattr(value, "value"):
        return (5, str(value.value))
    return (6, str(value))
