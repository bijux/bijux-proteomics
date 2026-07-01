# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Unimod-aware modification resolution and validation."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry.contracts import (
    ModificationPosition,
    ModificationRegistryDocument,
)
from bijux_proteomics.chemistry.modification_registry import (
    modification_registry as _modification_registry_root_export,
)
from bijux_proteomics.chemistry.modification_registry import (
    resolve_modification,
)
from bijux_proteomics.chemistry.public_api import rebind_package_export
from bijux_proteomics_foundation import JsonModel

rebind_package_export(
    "bijux_proteomics.chemistry",
    "modification_registry",
    _modification_registry_root_export,
)


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
    rejection_code: str | None = None
    rejection_message: str | None = None
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
    resolution = resolve_modification(
        token=normalized,
        site=ModificationPosition.ANYWHERE if normalized_residue is not None else None,
        residue=normalized_residue,
        registry=registry,
    )
    issues: list[str] = []
    if resolution.rejection is not None:
        issues.append(resolution.rejection.message)
    return ModificationResolutionReport(
        query_token=token,
        normalized_token=normalized,
        resolved=resolution.matched,
        source=ModificationResolutionSource(resolution.source.value),
        modification_name=resolution.modification_name,
        controlled_id=resolution.controlled_id,
        application=resolution.application,
        position=resolution.position,
        residues=resolution.residues,
        mass_delta_monoisotopic=resolution.mass_delta_monoisotopic,
        mass_delta_average=resolution.mass_delta_average,
        residue_query=normalized_residue,
        residue_allowed=resolution.residue_allowed,
        rejection_code=resolution.rejection.code if resolution.rejection else None,
        rejection_message=resolution.rejection.message
        if resolution.rejection
        else None,
        issues=tuple(issues),
    )
