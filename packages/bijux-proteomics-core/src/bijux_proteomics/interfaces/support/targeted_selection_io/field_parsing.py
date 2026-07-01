# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Small field parsing helpers reused across targeted support loaders."""

from __future__ import annotations


def _parse_cli_bool(raw_value: object, *, field_name: str) -> bool:
    value = str(raw_value).strip().lower()
    if value in {"true", "1", "yes"}:
        return True
    if value in {"false", "0", "no"}:
        return False
    raise ValueError(f"field {field_name!r} must be a boolean string")


def _split_semicolon_field(raw_value: object) -> tuple[str, ...]:
    return tuple(
        token
        for raw_token in str(raw_value or "").split(";")
        if (token := raw_token.strip())
    )


__all__ = [
    "_parse_cli_bool",
    "_split_semicolon_field",
]
