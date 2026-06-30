# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed public sequence facade catalog and lazy export helpers."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from importlib import import_module
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Literal

FacadeCollisionPolicy = Literal["error", "prefer_first_owner"]


@dataclass(frozen=True)
class SequenceFacadeBudget:
    """Public export and initializer budget for the sequence facade."""

    max_public_symbols: int
    max_init_lines: int


@dataclass(frozen=True)
class SequenceFacadeOwner:
    """One owner module that contributes public symbols to the sequence facade."""

    owner_module: str
    rationale: str
    excluded_exports: tuple[str, ...] = ()


def _owner(
    owner_module: str,
    rationale: str,
    *,
    excluded_exports: tuple[str, ...] = (),
) -> SequenceFacadeOwner:
    return SequenceFacadeOwner(
        owner_module=owner_module,
        rationale=rationale,
        excluded_exports=excluded_exports,
    )


SEQUENCES_FACADE_BUDGET = SequenceFacadeBudget(
    max_public_symbols=220,
    max_init_lines=60,
)

SEQUENCES_FACADE_OWNERS = (
    _owner(
        "bijux_proteomics.sequences.contaminant_database",
        "contaminant catalog ownership",
    ),
    _owner(
        "bijux_proteomics.sequences.fasta",
        "FASTA intake, validation, and target-decoy compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.sequences.digestion",
        "protease digestion and peptide indexing ownership",
    ),
    _owner(
        "bijux_proteomics.sequences.fasta_profile",
        "FASTA database profiling ownership",
    ),
    _owner(
        "bijux_proteomics.sequences.peptide_chemical_liability",
        "peptide chemical liability ownership",
    ),
    _owner(
        "bijux_proteomics.sequences.peptide_detectability",
        "peptide detectability ownership",
    ),
    _owner(
        "bijux_proteomics.sequences.peptide_properties",
        "peptide property ownership",
    ),
    _owner(
        "bijux_proteomics.sequences.peptide_uniqueness_index",
        "peptide uniqueness index ownership",
    ),
    _owner(
        "bijux_proteomics.sequences.protein_identity_resolution",
        "protein identity resolution ownership",
    ),
    _owner(
        "bijux_proteomics.sequences.protein_index",
        "protein and peptide index ownership",
    ),
    _owner(
        "bijux_proteomics.sequences.protein_region_context",
        "protein region context ownership",
    ),
    _owner(
        "bijux_proteomics.sequences.proteogenomic_peptide_support",
        "proteogenomic peptide support ownership",
    ),
    _owner(
        "bijux_proteomics.sequences.theoretical_digest",
        "theoretical digest workflow ownership",
    ),
)


def facade_owner_modules(
    owners: tuple[SequenceFacadeOwner, ...],
) -> tuple[SequenceFacadeOwner, ...]:
    """Return owner modules in their governed sequence facade order."""

    return owners


def list_owned_public_names(owner_module: str) -> tuple[str, ...]:
    """Return the owned public symbols for one sequence owner module."""

    source_path = _module_source_path(owner_module)
    module_tree = ast.parse(source_path.read_text(encoding="utf-8"))
    explicit_exports = _extract_explicit_exports(module_tree)
    if explicit_exports is not None:
        return explicit_exports
    if source_path.name == "__init__.py":
        runtime_exports = getattr(import_module(owner_module), "__all__", None)
        if runtime_exports is not None:
            return tuple(runtime_exports)
    star_import_modules = _extract_star_import_modules(module_tree, owner_module)
    if star_import_modules:
        public_names: list[str] = []
        for imported_module in star_import_modules:
            public_names.extend(list_owned_public_names(imported_module))
        return tuple(dict.fromkeys(public_names))
    return _extract_owned_public_symbols(module_tree)


def build_lazy_export_index(
    owners: tuple[SequenceFacadeOwner, ...],
    *,
    collision_policy: FacadeCollisionPolicy = "error",
) -> tuple[tuple[str, ...], dict[str, tuple[str, str]]]:
    """Build one ordered export ledger and import target map for sequences."""

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
                    "sequence facade export collision for "
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
    """Load one governed sequence export lazily from its owner module."""

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
    """Return a stable directory view for the sequence facade."""

    return sorted(set(package_globals) | set(public_names))


def _module_source_path(owner_module: str) -> Path:
    spec = find_spec(owner_module)
    if spec is None or spec.origin is None:
        raise ValueError(f"sequence facade owner module is not discoverable: {owner_module}")
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


def _extract_star_import_modules(
    module_tree: ast.Module,
    owner_module: str,
) -> tuple[str, ...]:
    imported_modules: list[str] = []
    for node in module_tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        if not any(alias.name == "*" for alias in node.names):
            continue
        resolved_module = _resolve_imported_module(owner_module, node)
        if resolved_module is not None:
            imported_modules.append(resolved_module)
    return tuple(dict.fromkeys(imported_modules))


def _resolve_imported_module(owner_module: str, node: ast.ImportFrom) -> str | None:
    if node.module is None:
        return None
    if node.level == 0:
        return node.module
    parent_parts = owner_module.split(".")[:-1]
    if node.level > len(parent_parts) + 1:
        raise ValueError(
            f"cannot resolve relative star import in sequence owner {owner_module}"
        )
    base_parts = parent_parts[: len(parent_parts) - (node.level - 1)]
    return ".".join((*base_parts, node.module))


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
    "SEQUENCES_FACADE_BUDGET",
    "SEQUENCES_FACADE_OWNERS",
    "SequenceFacadeBudget",
    "SequenceFacadeOwner",
    "build_lazy_export_index",
    "facade_owner_modules",
    "list_owned_public_names",
    "resolve_public_export",
    "module_directory",
]
