# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared pytest marker classification for package test trees."""

from __future__ import annotations

from collections.abc import Collection, Iterable
from pathlib import Path, PurePath
from typing import Protocol

PRIMARY_TEST_SELECTION_MARKERS = frozenset(
    {
        "api",
        "benchmark",
        "e2e",
        "evaluation",
        "external_data",
        "integration",
        "live",
        "real_local",
        "regression",
        "unit",
    }
)


class _PytestMarker(Protocol):
    name: str


class _CollectedTestItem(Protocol):
    fixturenames: Collection[str]

    def iter_markers(self) -> Iterable[_PytestMarker]: ...

    def add_marker(self, marker: object) -> None: ...


def derive_default_test_markers(
    test_path: str | PurePath,
    *,
    fixturenames: Collection[str] = (),
    existing_markers: Collection[str] = (),
    benchmark_dirs: Collection[str] = (),
    integration_dirs: Collection[str] = (),
    e2e_dirs: Collection[str] = (),
    real_local_dirs: Collection[str] = (),
    external_data_dirs: Collection[str] = (),
    benchmark_name_tokens: Collection[str] = ("benchmark",),
    external_data_name_tokens: Collection[str] = ("external_",),
) -> tuple[str, ...]:
    """Derive stable default markers from one collected test path."""

    path = PurePath(test_path)
    path_parts = {part.lower() for part in path.parts}
    stem = path.stem.lower()
    fixturenames_lower = {name.lower() for name in fixturenames}
    markers = {name.lower() for name in existing_markers}
    inferred: list[str] = []

    if "benchmark" not in markers and (
        _matches_any_dir(path_parts, benchmark_dirs)
        or _contains_any_token(stem, benchmark_name_tokens)
        or "benchmark" in fixturenames_lower
    ):
        inferred.append("benchmark")
        markers.add("benchmark")

    if "external_data" not in markers and (
        _matches_any_dir(path_parts, external_data_dirs)
        or _contains_any_token(stem, external_data_name_tokens)
    ):
        inferred.append("external_data")
        markers.add("external_data")

    if "e2e" not in markers and _matches_any_dir(path_parts, e2e_dirs):
        inferred.append("e2e")
        markers.add("e2e")

    if "real_local" not in markers and _matches_any_dir(path_parts, real_local_dirs):
        inferred.append("real_local")
        markers.add("real_local")

    if "integration" not in markers and _matches_any_dir(path_parts, integration_dirs):
        inferred.append("integration")
        markers.add("integration")

    if not PRIMARY_TEST_SELECTION_MARKERS.intersection(markers):
        inferred.append("unit")

    return tuple(inferred)


def apply_default_test_markers(
    items: Iterable[_CollectedTestItem],
    *,
    benchmark_dirs: Collection[str] = (),
    integration_dirs: Collection[str] = (),
    e2e_dirs: Collection[str] = (),
    real_local_dirs: Collection[str] = (),
    external_data_dirs: Collection[str] = (),
    benchmark_name_tokens: Collection[str] = ("benchmark",),
    external_data_name_tokens: Collection[str] = ("external_",),
) -> None:
    """Apply derived default markers to one collected pytest item sequence."""

    import pytest

    for item in items:
        item_path = _item_path(item)
        item_markers = {mark.name for mark in item.iter_markers()}
        derived_markers = derive_default_test_markers(
            item_path,
            fixturenames=getattr(item, "fixturenames", ()),
            existing_markers=item_markers,
            benchmark_dirs=benchmark_dirs,
            integration_dirs=integration_dirs,
            e2e_dirs=e2e_dirs,
            real_local_dirs=real_local_dirs,
            external_data_dirs=external_data_dirs,
            benchmark_name_tokens=benchmark_name_tokens,
            external_data_name_tokens=external_data_name_tokens,
        )
        for marker_name in derived_markers:
            item.add_marker(getattr(pytest.mark, marker_name))


def _matches_any_dir(path_parts: Collection[str], candidate_dirs: Collection[str]) -> bool:
    normalized_path_parts = {part.lower() for part in path_parts}
    normalized_dirs = {candidate.lower() for candidate in candidate_dirs}
    return not normalized_path_parts.isdisjoint(normalized_dirs)


def _contains_any_token(stem: str, tokens: Collection[str]) -> bool:
    return any(token.lower() in stem for token in tokens)


def _item_path(item: object) -> Path:
    item_path = getattr(item, "path", None)
    if item_path is not None:
        return Path(str(item_path))
    return Path(str(getattr(item, "fspath")))
