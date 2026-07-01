# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed public laboratory facade catalogs and lazy export helpers."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from importlib import import_module
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Literal

FacadeCollisionPolicy = Literal["error", "prefer_first_owner"]


@dataclass(frozen=True)
class LabFacadeBudget:
    """Public export and `__init__` size budget for one lab facade."""

    max_public_symbols: int
    max_init_lines: int


@dataclass(frozen=True)
class LabFacadeOwner:
    """One owner module that contributes public symbols to a lab facade."""

    owner_module: str
    rationale: str
    excluded_exports: tuple[str, ...] = ()


def _owner(
    owner_module: str,
    rationale: str,
    *,
    excluded_exports: tuple[str, ...] = (),
) -> LabFacadeOwner:
    return LabFacadeOwner(
        owner_module=owner_module,
        rationale=rationale,
        excluded_exports=excluded_exports,
    )


LAB_ROOT_FACADE_BUDGET = LabFacadeBudget(
    max_public_symbols=240,
    max_init_lines=80,
)
QC_FACADE_BUDGET = LabFacadeBudget(
    max_public_symbols=70,
    max_init_lines=70,
)

QC_FACADE_OWNERS = (
    _owner(
        "bijux_proteomics.lab.qc.models",
        "laboratory QC contracts ownership",
        excluded_exports=(
            "AcquisitionType",
            "DepletionMode",
            "EnrichmentType",
            "FractionationMode",
            "LabelingMethod",
        ),
    ),
    _owner(
        "bijux_proteomics.lab.qc.assessment",
        "laboratory QC assessment ownership",
    ),
    _owner(
        "bijux_proteomics.lab.qc.review_artifacts",
        "laboratory QC review artifact ownership",
    ),
    _owner(
        "bijux_proteomics.lab.qc.run_reports",
        "laboratory QC run report ownership",
    ),
    _owner(
        "bijux_proteomics.lab.qc.summaries",
        "laboratory QC summary ownership",
    ),
)

LAB_ROOT_FACADE_OWNERS = (
    _owner(
        "bijux_proteomics.lab.protocol_context",
        "laboratory protocol context ownership",
    ),
    *QC_FACADE_OWNERS,
    _owner(
        "bijux_proteomics.lab.qc_benchmarks",
        "laboratory QC benchmark ownership",
    ),
    _owner(
        "bijux_proteomics.lab.carryover",
        "laboratory carryover ownership",
    ),
    _owner(
        "bijux_proteomics.lab.lc_drift",
        "laboratory LC drift ownership",
    ),
    _owner(
        "bijux_proteomics.lab.protocol_consistency",
        "laboratory protocol consistency ownership",
    ),
    _owner(
        "bijux_proteomics.lab.operations",
        "laboratory operations ownership",
    ),
    _owner(
        "bijux_proteomics.lab.planning",
        "laboratory planning ownership",
    ),
    _owner(
        "bijux_proteomics.lab.actions",
        "laboratory action packet ownership",
    ),
    _owner(
        "bijux_proteomics.lab.background",
        "laboratory background comparison ownership",
    ),
    _owner(
        "bijux_proteomics.lab.cohort",
        "laboratory cohort balance ownership",
    ),
    _owner(
        "bijux_proteomics.lab.contamination",
        "laboratory contamination ownership",
    ),
    _owner(
        "bijux_proteomics.lab.digestion_diagnosis",
        "laboratory digestion diagnosis ownership",
    ),
    _owner(
        "bijux_proteomics.lab.run_diagnosis",
        "laboratory run diagnosis ownership",
    ),
    _owner(
        "bijux_proteomics.lab.sample_identity",
        "laboratory sample identity ownership",
    ),
    _owner(
        "bijux_proteomics.lab.standards",
        "laboratory standards ownership",
    ),
)


def facade_owner_modules(
    owners: tuple[LabFacadeOwner, ...],
) -> tuple[LabFacadeOwner, ...]:
    """Return owner modules in their governed facade order."""

    return owners


def list_owned_public_names(owner_module: str) -> tuple[str, ...]:
    """Return the owned public symbols for one lab owner module."""

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
    owners: tuple[LabFacadeOwner, ...],
    *,
    collision_policy: FacadeCollisionPolicy = "error",
) -> tuple[tuple[str, ...], dict[str, tuple[str, str]]]:
    """Build one ordered export ledger and import target map for a lab facade."""

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
                    "lab facade export collision for "
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
    """Load one governed lab export lazily from its owner module."""

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
    """Return a stable directory view for one governed lab facade."""

    return sorted(set(package_globals) | set(public_names))


def _module_source_path(owner_module: str) -> Path:
    spec = find_spec(owner_module)
    if spec is None or spec.origin is None:
        raise ValueError(f"lab facade owner module is not discoverable: {owner_module}")
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
    "FacadeCollisionPolicy",
    "LAB_ROOT_FACADE_BUDGET",
    "LAB_ROOT_FACADE_OWNERS",
    "QC_FACADE_BUDGET",
    "QC_FACADE_OWNERS",
    "LabFacadeBudget",
    "LabFacadeOwner",
    "build_lazy_export_index",
    "facade_owner_modules",
    "list_owned_public_names",
    "resolve_public_export",
    "module_directory",
]
