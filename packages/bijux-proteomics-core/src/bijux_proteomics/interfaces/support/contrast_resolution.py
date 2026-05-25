# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Shared condition-contrast helpers for CLI command modules."""

from __future__ import annotations

from .imports import ExperimentalDesignEntry, click

__all__ = ["_resolve_cli_contrast"]


def _resolve_cli_contrast(
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str | None,
    condition_b: str | None,
) -> tuple[str, str]:
    """Resolve one CLI contrast from explicit options or a two-condition design."""

    conditions = tuple(dict.fromkeys(entry.condition for entry in design_entries))
    if len(conditions) < 2:
        raise click.ClickException(
            "design table must contain at least two distinct conditions"
        )
    if condition_a is None and condition_b is None:
        if len(conditions) != 2:
            raise click.ClickException(
                "condition_a and condition_b are required when the design contains more than two conditions"
            )
        return conditions[0], conditions[1]
    if condition_a is None or condition_b is None:
        raise click.ClickException(
            "condition_a and condition_b must be provided together"
        )
    if condition_a == condition_b:
        raise click.ClickException("condition_a and condition_b must be different")
    for condition in (condition_a, condition_b):
        if condition not in conditions:
            raise click.ClickException(
                f"condition {condition!r} was not present in the design table"
            )
    return condition_a, condition_b
