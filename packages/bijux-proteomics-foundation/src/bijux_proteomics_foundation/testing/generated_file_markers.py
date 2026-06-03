# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Private test-support helpers for governed generated-file markers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class GeneratedFileMarkerKind(StrEnum):
    """Supported generated-file marker kinds used by repository governance."""

    GENERATED_HEADER = "generated_header"
    SSOT_NOTICE = "ssot_notice"


@dataclass(frozen=True)
class GeneratedFileMarker:
    """Detected generated-file marker metadata for one durable file."""

    kind: GeneratedFileMarkerKind
    regenerate_command: str | None = None


def detect_generated_file_marker(path: Path) -> GeneratedFileMarker | None:
    """Return the generated-file marker for one durable tracked file."""

    lines = path.read_text(encoding="utf-8").splitlines()
    return detect_generated_file_marker_lines(tuple(lines))


def detect_generated_file_marker_lines(
    lines: tuple[str, ...],
) -> GeneratedFileMarker | None:
    """Return generated marker metadata for one file payload."""

    if not lines:
        return None
    first_line = lines[0].strip()
    if first_line.startswith("# Generated "):
        if len(lines) < 2:
            return None
        second_line = lines[1].strip()
        if not second_line.startswith("# Regenerate with: "):
            return None
        return GeneratedFileMarker(
            kind=GeneratedFileMarkerKind.GENERATED_HEADER,
            regenerate_command=second_line.removeprefix("# Regenerate with: ").strip(),
        )
    if first_line.startswith("# SSOT NOTICE:"):
        return GeneratedFileMarker(kind=GeneratedFileMarkerKind.SSOT_NOTICE)
    return None


def is_marked_generated_file(path: Path) -> bool:
    """Return whether one durable tracked file carries a governed marker."""

    return detect_generated_file_marker(path) is not None


__all__ = [
    "GeneratedFileMarker",
    "GeneratedFileMarkerKind",
    "detect_generated_file_marker",
    "detect_generated_file_marker_lines",
    "is_marked_generated_file",
]
