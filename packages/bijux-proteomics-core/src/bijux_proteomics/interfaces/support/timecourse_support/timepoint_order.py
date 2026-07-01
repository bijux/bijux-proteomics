# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Timepoint order parsing for time-course quantification workflows."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.domain.errors import DesignError


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


__all__ = ("_parse_timepoint_order_file",)
