# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Private test-support helpers for source-tree maintainability ceilings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceFileLineCountException:
    """One temporary line-count exception for a source file."""

    relative_path: str
    allowed_line_count: int
    temporary_reason: str


@dataclass(frozen=True)
class SourceFileLineCountObservation:
    """Observed line-count state for one source file above the shared ceiling."""

    relative_path: str
    line_count: int
    allowed_line_count: int | None
    temporary_reason: str | None


@dataclass(frozen=True)
class SourceTreeLineCountReport:
    """Structured report over one source tree line-count ceiling scan."""

    source_root: Path
    ceiling: int
    scanned_file_count: int
    approved_over_ceiling: tuple[SourceFileLineCountObservation, ...]
    unexpected_over_ceiling: tuple[SourceFileLineCountObservation, ...]
    stale_exceptions: tuple[SourceFileLineCountException, ...]


def build_source_tree_line_count_report(
    source_root: Path,
    *,
    ceiling: int,
    exceptions: tuple[SourceFileLineCountException, ...] = (),
) -> SourceTreeLineCountReport:
    """Scan one source tree and classify files above the shared line-count ceiling."""

    exception_by_path = {entry.relative_path: entry for entry in exceptions}
    approved_over_ceiling: list[SourceFileLineCountObservation] = []
    unexpected_over_ceiling: list[SourceFileLineCountObservation] = []
    observed_counts: dict[str, int] = {}

    for path in sorted(source_root.rglob("*.py")):
        relative_path = path.relative_to(source_root).as_posix()
        line_count = len(path.read_text().splitlines())
        observed_counts[relative_path] = line_count
        if line_count <= ceiling:
            continue
        exception = exception_by_path.get(relative_path)
        observation = SourceFileLineCountObservation(
            relative_path=relative_path,
            line_count=line_count,
            allowed_line_count=(
                None if exception is None else exception.allowed_line_count
            ),
            temporary_reason=(
                None if exception is None else exception.temporary_reason
            ),
        )
        if exception is None or line_count > exception.allowed_line_count:
            unexpected_over_ceiling.append(observation)
        else:
            approved_over_ceiling.append(observation)

    stale_exceptions = tuple(
        entry
        for entry in exceptions
        if observed_counts.get(entry.relative_path, 0) <= ceiling
    )

    return SourceTreeLineCountReport(
        source_root=source_root,
        ceiling=ceiling,
        scanned_file_count=len(observed_counts),
        approved_over_ceiling=tuple(approved_over_ceiling),
        unexpected_over_ceiling=tuple(unexpected_over_ceiling),
        stale_exceptions=stale_exceptions,
    )


__all__ = [
    "SourceFileLineCountException",
    "SourceFileLineCountObservation",
    "SourceTreeLineCountReport",
    "build_source_tree_line_count_report",
]
