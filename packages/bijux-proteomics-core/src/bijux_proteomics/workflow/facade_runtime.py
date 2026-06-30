# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Runtime helpers for governed workflow facade exports and submodules."""

from __future__ import annotations

import ast
from importlib import import_module
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Protocol


class WorkflowFacadeOwnerLike(Protocol):
    """Structural contract for facade owner records consumed by runtime helpers."""

    owner_module: str
    excluded_exports: tuple[str, ...]


def ordered_facade_owners(
    owners: tuple[WorkflowFacadeOwnerLike, ...],
) -> tuple[WorkflowFacadeOwnerLike, ...]:
    """Return facade owners in their declared stable governance order."""

    return owners


def list_owned_public_names(owner_module: str) -> tuple[str, ...]:
    """Return the owned public symbols for one workflow owner module."""

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
    owners: tuple[WorkflowFacadeOwnerLike, ...],
) -> tuple[tuple[str, ...], dict[str, tuple[str, str]]]:
    """Build one ordered export ledger and import target map for a facade."""

    public_names: list[str] = []
    export_index: dict[str, tuple[str, str]] = {}
    for owner in owners:
        for export_name in list_owned_public_names(owner.owner_module):
            if export_name in owner.excluded_exports:
                continue
            if export_name in export_index:
                conflict_owner, _ = export_index[export_name]
                raise ValueError(
                    "workflow facade export collision for "
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
    """Load one governed workflow export lazily from its owner module."""

    owner = export_index.get(name)
    if owner is None:
        raise AttributeError(f"module {package_name!r} has no attribute {name!r}")
    module_name, export_name = owner
    value = getattr(import_module(module_name), export_name)
    package_globals[name] = value
    return value


def resolve_public_submodule(
    package_name: str,
    package_globals: dict[str, Any],
    submodules: dict[str, str],
    name: str,
) -> Any:
    """Load one governed workflow submodule lazily from its canonical path."""

    module_name = submodules.get(name)
    if module_name is None:
        raise AttributeError(f"module {package_name!r} has no attribute {name!r}")
    module = import_module(module_name)
    package_globals[name] = module
    return module


def module_directory(
    package_globals: dict[str, Any],
    public_names: tuple[str, ...],
    *,
    submodule_names: tuple[str, ...] = (),
) -> list[str]:
    """Return a stable directory view for one governed workflow facade."""

    return sorted(set(package_globals) | set(public_names) | set(submodule_names))


def _module_source_path(owner_module: str) -> Path:
    spec = find_spec(owner_module)
    if spec is None or spec.origin is None:
        raise ValueError(
            f"workflow facade owner module is not discoverable: {owner_module}"
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
    if isinstance(target, ast.Name) and target.id.isupper():
        return [target.id]
    return []


__all__ = [
    "build_lazy_export_index",
    "list_owned_public_names",
    "resolve_public_export",
    "resolve_public_submodule",
    "module_directory",
    "ordered_facade_owners",
]
