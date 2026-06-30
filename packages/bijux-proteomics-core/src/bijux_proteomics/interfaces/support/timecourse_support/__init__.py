# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Time-course helpers shared by CLI command modules."""

from __future__ import annotations

from bijux_proteomics.domain.errors import DesignError

from .. import imports as _imports
from ..imports import *  # noqa: F401,F403


def _parse_timepoint_order_file(path: Path) -> tuple[str, ...]:
    labels: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        label = line.split("\t", 1)[0].strip()
        if label:
            labels.append(label)
    if labels and labels[0].casefold() in {"timepoint", "label"}:
        labels = labels[1:]
    ordered_labels = tuple(labels)
    if not ordered_labels:
        raise DesignError("timepoint order file must contain at least one label")
    return ordered_labels


__all__ = tuple(
    dict.fromkeys((*_imports.__all__, "DesignError", "_parse_timepoint_order_file"))
)
