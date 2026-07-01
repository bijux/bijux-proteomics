# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared models and helpers for governed identification facade ledgers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IdentificationFacadeBudget:
    """Budget for one durable identification facade."""

    max_public_symbols: int
    max_init_lines: int


@dataclass(frozen=True)
class IdentificationFacadeModule:
    """One owner module grouped under an identification facade."""

    owner_module: str
    export_names: tuple[str, ...]
    classification: str
    rationale: str


def build_facade_module(
    owner_module: str,
    classification: str,
    rationale: str,
    export_names: tuple[str, ...],
) -> IdentificationFacadeModule:
    """Return one governed identification facade module entry."""

    return IdentificationFacadeModule(
        owner_module=owner_module,
        export_names=export_names,
        classification=classification,
        rationale=rationale,
    )


def flatten_facade_exports(
    modules: tuple[IdentificationFacadeModule, ...],
) -> tuple[str, ...]:
    """Return the flattened export names for a facade module tuple."""

    return tuple(
        export_name for module in modules for export_name in module.export_names
    )


def build_facade_export_map(
    modules: tuple[IdentificationFacadeModule, ...],
) -> dict[str, str]:
    """Return the export-name to owner-module map for a facade module tuple."""

    return {
        export_name: module.owner_module
        for module in modules
        for export_name in module.export_names
    }


def merge_facade_export_maps(*export_owner_maps: dict[str, str]) -> dict[str, str]:
    """Merge facade export maps while preserving first-owner precedence."""

    merged: dict[str, str] = {}
    for export_owner_map in export_owner_maps:
        for export_name, owner_module in export_owner_map.items():
            merged.setdefault(export_name, owner_module)
    return merged


__all__ = [
    "IdentificationFacadeBudget",
    "IdentificationFacadeModule",
    "build_facade_export_map",
    "build_facade_module",
    "flatten_facade_exports",
    "merge_facade_export_maps",
]
