# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed public interpretation facade catalogs and lazy export helpers."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from importlib import import_module
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Literal

FacadeCollisionPolicy = Literal["error", "prefer_first_owner"]


@dataclass(frozen=True)
class InterpretationFacadeBudget:
    """Public export and initializer budget for one interpretation facade."""

    max_public_symbols: int
    max_init_lines: int


@dataclass(frozen=True)
class InterpretationFacadeOwner:
    """One owned module that contributes public symbols to an interpretation facade."""

    owner_module: str
    rationale: str
    excluded_exports: tuple[str, ...] = ()


def _owner(
    owner_module: str,
    rationale: str,
    *,
    excluded_exports: tuple[str, ...] = (),
) -> InterpretationFacadeOwner:
    return InterpretationFacadeOwner(
        owner_module=owner_module,
        rationale=rationale,
        excluded_exports=excluded_exports,
    )


INTERPRETATION_ROOT_FACADE_BUDGET = InterpretationFacadeBudget(
    max_public_symbols=340,
    max_init_lines=80,
)

INTERPRETATION_ROOT_FACADE_OWNERS = (
    _owner(
        "bijux_proteomics.interpretation.biological_context_mapping",
        "biological context annotation ownership",
    ),
    _owner(
        "bijux_proteomics.interpretation.annotation_packs",
        "annotation pack ownership",
    ),
    _owner(
        "bijux_proteomics.interpretation.compartment_biology",
        "compartment enrichment ownership",
    ),
    _owner(
        "bijux_proteomics.interpretation.complex_activity",
        "complex activity ownership",
    ),
    _owner(
        "bijux_proteomics.interpretation.complex_enrichment",
        "complex enrichment ownership",
    ),
    _owner(
        "bijux_proteomics.interpretation.drug_target_interpretation",
        "drug target interpretation ownership",
    ),
    _owner(
        "bijux_proteomics.interpretation.disease_phenotype_interpretation",
        "disease phenotype interpretation ownership",
    ),
    _owner(
        "bijux_proteomics.interpretation.foreground_background_model",
        "foreground and background modeling ownership",
    ),
    _owner(
        "bijux_proteomics.interpretation.go_enrichment",
        "gene ontology enrichment ownership",
    ),
    _owner(
        "bijux_proteomics.interpretation.ortholog_mapping",
        "ortholog mapping ownership",
    ),
    _owner(
        "bijux_proteomics.interpretation.pathway_activity",
        "pathway activity ownership",
    ),
    _owner(
        "bijux_proteomics.interpretation.pathway_enrichment",
        "pathway enrichment ownership",
    ),
    _owner(
        "bijux_proteomics.interpretation.ppi_network_modules",
        "protein interaction module ownership",
    ),
    _owner(
        "bijux_proteomics.interpretation.protein_annotation_mapping",
        "protein annotation mapping ownership",
    ),
    _owner(
        "bijux_proteomics.interpretation.regulator_inference",
        "upstream regulator inference ownership",
    ),
    _owner(
        "bijux_proteomics.interpretation.protein_set_enrichment",
        "protein set enrichment ownership",
    ),
    _owner(
        "bijux_proteomics.interpretation.protein_set_scoring",
        "protein set scoring ownership",
    ),
    _owner(
        "bijux_proteomics.interpretation.tissue_cell_type_context",
        "tissue and cell type interpretation ownership",
    ),
)


def facade_owner_modules(
    owners: tuple[InterpretationFacadeOwner, ...],
) -> tuple[InterpretationFacadeOwner, ...]:
    """Return owner modules in their governed interpretation facade order."""

    return owners


def list_owned_public_names(owner_module: str) -> tuple[str, ...]:
    """Return the owned public symbols for one interpretation owner module."""

    source_path = _module_source_path(owner_module)
    module_tree = ast.parse(source_path.read_text(encoding="utf-8"))
    explicit_exports = _extract_explicit_exports(module_tree)
    if explicit_exports is not None:
        return explicit_exports
    if source_path.name == "__init__.py":
        runtime_exports = getattr(import_module(owner_module), "__all__", None)
        if runtime_exports is not None:
            return tuple(runtime_exports)
    return _extract_owned_public_symbols(module_tree)


def build_lazy_export_index(
    owners: tuple[InterpretationFacadeOwner, ...],
    *,
    collision_policy: FacadeCollisionPolicy = "error",
) -> tuple[tuple[str, ...], dict[str, tuple[str, str]]]:
    """Build one ordered export ledger and import target map for a facade."""

    public_names: list[str] = []
    export_index: dict[str, tuple[str, str]] = {}
    for owner in owners:
        for export_name in list_owned_public_names(owner.owner_module):
            if export_name in owner.excluded_exports:
                continue
            if export_name in export_index:
                if collision_policy == "prefer_first_owner":
                    continue
                conflict_owner, _ = export_index[export_name]
                raise ValueError(
                    "interpretation facade export collision for "
                    f"{export_name!r}: {conflict_owner} vs {owner.owner_module}"
                )
            public_names.append(export_name)
            export_index[export_name] = (owner.owner_module, export_name)
    return tuple(public_names), export_index


def resolve_public_export(
    package_name: str,
    package_globals: dict[str, Any],
    export_index: dict[str, tuple[str, str]],
    name: str,
) -> Any:
    """Load one governed interpretation export lazily from its owner module."""

    owner = export_index.get(name)
    if owner is None:
        raise AttributeError(f"module {package_name!r} has no attribute {name!r}")
    module_name, export_name = owner
    value = getattr(import_module(module_name), export_name)
    package_globals[name] = value
    return value


def module_directory(
    package_globals: dict[str, Any], public_names: tuple[str, ...]
) -> list[str]:
    """Return a stable directory view for one governed interpretation facade."""

    return sorted(set(package_globals) | set(public_names))


def _module_source_path(owner_module: str) -> Path:
    spec = find_spec(owner_module)
    if spec is None or spec.origin is None:
        raise ValueError(
            f"interpretation facade owner module is not discoverable: {owner_module}"
        )
    return Path(spec.origin)


def _extract_explicit_exports(module_tree: ast.Module) -> tuple[str, ...] | None:
    for node in module_tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "__all__"
            for target in node.targets
        ):
            continue
        if not isinstance(node.value, ast.List | ast.Tuple):
            continue
        exports: list[str] = []
        for element in node.value.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                exports.append(element.value)
        return tuple(exports)
    return None


def _extract_owned_public_symbols(module_tree: ast.Module) -> tuple[str, ...]:
    owned_public_names: list[str] = []
    for node in module_tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                owned_public_names.append(node.name)
            continue
        if isinstance(node, ast.Assign):
            for target in node.targets:
                owned_public_names.extend(_public_assigned_names(target))
            continue
        if isinstance(node, ast.AnnAssign):
            owned_public_names.extend(_public_assigned_names(node.target))
    return tuple(dict.fromkeys(owned_public_names))


def _public_assigned_names(target: ast.expr) -> list[str]:
    if (
        isinstance(target, ast.Name)
        and target.id.isupper()
        and not target.id.startswith("_")
    ):
        return [target.id]
    return []


__all__ = [
    "FacadeCollisionPolicy",
    "INTERPRETATION_ROOT_FACADE_BUDGET",
    "INTERPRETATION_ROOT_FACADE_OWNERS",
    "InterpretationFacadeBudget",
    "InterpretationFacadeOwner",
    "build_lazy_export_index",
    "facade_owner_modules",
    "list_owned_public_names",
    "resolve_public_export",
    "module_directory",
]
