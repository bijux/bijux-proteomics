# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Registry-engine access for chemistry contract owners."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Protocol, cast

from bijux_proteomics.chemistry.contracts.models import (
    ModificationPosition,
    ModificationRegistryDocument,
    ModificationRegistryValidationReport,
    StaticModification,
    VariableModification,
)


class _ModificationRegistryEngine(Protocol):
    def resolve_modification_definition(
        self,
        *,
        token: str | None = None,
        controlled_id: str | None = None,
        mass_delta_monoisotopic: float | None = None,
        site: ModificationPosition | None = None,
        residue: str | None = None,
        at_protein_n_term: bool = False,
        at_protein_c_term: bool = False,
        registry: ModificationRegistryDocument | None = None,
        tolerance: float = 1e-6,
    ) -> StaticModification | VariableModification: ...

    def validate_modification_registry(
        self,
        registry: ModificationRegistryDocument,
    ) -> ModificationRegistryValidationReport: ...

    def modification_registry(self) -> ModificationRegistryDocument: ...

    def build_modification_registry(
        self,
        *,
        static_modifications: tuple[StaticModification, ...] = (),
        variable_modifications: tuple[VariableModification, ...] = (),
    ) -> ModificationRegistryDocument: ...

    def load_modification_registry(
        self,
        path: Path,
    ) -> ModificationRegistryDocument: ...

    def _registry_lookup(
        self,
        registry: ModificationRegistryDocument | None,
    ) -> dict[str, StaticModification | VariableModification]: ...

    def get_modification(
        self,
        name: str,
        *,
        registry: ModificationRegistryDocument | None = None,
    ) -> StaticModification | VariableModification: ...


def _modification_registry_engine() -> _ModificationRegistryEngine:
    return cast(
        _ModificationRegistryEngine,
        importlib.import_module("bijux_proteomics.chemistry.modification_registry"),
    )


def resolve_modification_definition(
    *,
    token: str | None = None,
    controlled_id: str | None = None,
    mass_delta_monoisotopic: float | None = None,
    site: ModificationPosition | None = None,
    residue: str | None = None,
    at_protein_n_term: bool = False,
    at_protein_c_term: bool = False,
    registry: ModificationRegistryDocument | None = None,
    tolerance: float = 1e-6,
) -> StaticModification | VariableModification:
    """Resolve one modification definition through the owned registry engine."""

    return _modification_registry_engine().resolve_modification_definition(
        token=token,
        controlled_id=controlled_id,
        mass_delta_monoisotopic=mass_delta_monoisotopic,
        site=site,
        residue=residue,
        at_protein_n_term=at_protein_n_term,
        at_protein_c_term=at_protein_c_term,
        registry=registry,
        tolerance=tolerance,
    )


def validate_modification_registry(
    registry: ModificationRegistryDocument,
) -> ModificationRegistryValidationReport:
    """Validate one modification registry through the owned registry engine."""

    return _modification_registry_engine().validate_modification_registry(
        registry,
    )


def build_modification_registry(
    *,
    static_modifications: tuple[StaticModification, ...] = (),
    variable_modifications: tuple[VariableModification, ...] = (),
) -> ModificationRegistryDocument:
    """Build one registry through the owned registry engine."""

    return _modification_registry_engine().build_modification_registry(
        static_modifications=static_modifications,
        variable_modifications=variable_modifications,
    )


def modification_registry() -> ModificationRegistryDocument:
    """Return the builtin modification registry."""

    return _modification_registry_engine().modification_registry()


def load_modification_registry(path: Path) -> ModificationRegistryDocument:
    """Load one registry document from disk."""

    return _modification_registry_engine().load_modification_registry(path)


def registry_lookup(
    registry: ModificationRegistryDocument | None,
) -> dict[str, StaticModification | VariableModification]:
    """Return the normalized lookup mapping for one registry."""

    return _modification_registry_engine()._registry_lookup(registry)


def get_modification(
    name: str,
    *,
    registry: ModificationRegistryDocument | None = None,
) -> StaticModification | VariableModification:
    """Resolve one named modification from the active registry."""

    return _modification_registry_engine().get_modification(name, registry=registry)


__all__ = [
    "build_modification_registry",
    "get_modification",
    "load_modification_registry",
    "modification_registry",
    "registry_lookup",
    "resolve_modification_definition",
    "validate_modification_registry",
]
