# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Unimod-aware modification resolution and validation."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry.contracts import (
    ModificationPosition,
    ModificationRegistryDocument,
    StaticModification,
    VariableModification,
    get_modification,
    modification_registry,
)
from bijux_proteomics_foundation import JsonModel


class ModificationResolutionSource(StrEnum):
    """Provenance for one resolved modification definition."""

    BUILTIN = "builtin"
    REGISTRY = "registry"
    UNKNOWN = "unknown"


class ModificationResolutionReport(JsonModel):
    """Resolution result for one modification token."""

    model_config = ConfigDict(extra="forbid")

    query_token: str = Field(..., min_length=1)
    normalized_token: str = Field(..., min_length=1)
    resolved: bool
    source: ModificationResolutionSource
    modification_name: str | None = None
    controlled_id: str | None = None
    application: str | None = None
    position: ModificationPosition | None = None
    residues: tuple[str, ...] = Field(default_factory=tuple)
    mass_delta_monoisotopic: float | None = None
    mass_delta_average: float | None = None
    residue_query: str | None = None
    residue_allowed: bool | None = None
    issues: tuple[str, ...] = Field(default_factory=tuple)


def build_modification_resolution_report(
    token: str,
    *,
    residue: str | None = None,
    registry: ModificationRegistryDocument | None = None,
) -> ModificationResolutionReport:
    """Resolve one modification token against builtin and optional custom definitions."""
    normalized = token.strip()
    normalized_residue = residue.strip().upper() if residue is not None else None
    if not normalized:
        raise ValueError("modification token cannot be empty")
    if normalized_residue is not None and (
        len(normalized_residue) != 1 or not normalized_residue.isalpha()
    ):
        raise ValueError("residue queries must use one amino-acid letter")

    try:
        definition = get_modification(normalized, registry=registry)
    except ValueError:
        return ModificationResolutionReport(
            query_token=token,
            normalized_token=normalized,
            resolved=False,
            source=ModificationResolutionSource.UNKNOWN,
            residue_query=normalized_residue,
            issues=(f"unknown modification {token!r}",),
        )

    source = _classify_resolution_source(definition, registry=registry)
    residue_allowed = _residue_allowed(definition, normalized_residue)
    issues: list[str] = []
    if residue_allowed is False:
        issues.append(
            f"modification {definition.name!r} is not valid on residue {normalized_residue!r}"
        )
    return ModificationResolutionReport(
        query_token=token,
        normalized_token=normalized,
        resolved=True,
        source=source,
        modification_name=definition.name,
        controlled_id=definition.controlled_id,
        application="static" if isinstance(definition, StaticModification) else "variable",
        position=definition.position,
        residues=definition.residues,
        mass_delta_monoisotopic=definition.mass_delta_monoisotopic,
        mass_delta_average=definition.mass_delta_average,
        residue_query=normalized_residue,
        residue_allowed=residue_allowed,
        issues=tuple(issues),
    )


def _classify_resolution_source(
    definition: StaticModification | VariableModification,
    *,
    registry: ModificationRegistryDocument | None,
) -> ModificationResolutionSource:
    if registry is None:
        return ModificationResolutionSource.BUILTIN
    for candidate in (*registry.static_modifications, *registry.variable_modifications):
        if _same_definition(candidate, definition):
            return ModificationResolutionSource.REGISTRY
    builtin_registry = modification_registry()
    for candidate in (
        *builtin_registry.static_modifications,
        *builtin_registry.variable_modifications,
    ):
        if _same_definition(candidate, definition):
            return ModificationResolutionSource.BUILTIN
    return ModificationResolutionSource.REGISTRY


def _same_definition(
    left: StaticModification | VariableModification,
    right: StaticModification | VariableModification,
) -> bool:
    return (
        left.name == right.name
        and left.controlled_id == right.controlled_id
        and left.position == right.position
        and left.residues == right.residues
        and left.mass_delta_monoisotopic == right.mass_delta_monoisotopic
        and left.mass_delta_average == right.mass_delta_average
    )


def _residue_allowed(
    definition: StaticModification | VariableModification,
    residue: str | None,
) -> bool | None:
    if residue is None:
        return None
    if definition.position is not ModificationPosition.ANYWHERE:
        return True
    return residue in definition.residues
