# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Shared lookup-join validation helpers for biomarker candidate inputs."""

from __future__ import annotations


def _require_joined_row(
    rows: tuple[dict[str, str], ...],
    *,
    row_label: str,
    join_name: str,
) -> dict[str, str]:
    if not rows:
        raise ValueError(f"no {join_name} row matched {row_label}")
    return rows[0]
