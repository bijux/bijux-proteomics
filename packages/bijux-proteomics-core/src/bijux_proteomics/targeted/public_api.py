# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed targeted facade catalog and lazy export helpers."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from importlib import import_module
from importlib.util import find_spec
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TargetedFacadeBudget:
    """Public export and initializer budget for the targeted facade."""

    max_public_symbols: int
    max_init_lines: int


@dataclass(frozen=True)
class TargetedFacadeOwner:
    """One owner module that contributes public symbols to the targeted facade."""

    owner_module: str
    rationale: str
    excluded_exports: tuple[str, ...] = ()


def _owner(
    owner_module: str,
    rationale: str,
    *,
    excluded_exports: tuple[str, ...] = (),
) -> TargetedFacadeOwner:
    return TargetedFacadeOwner(
        owner_module=owner_module,
        rationale=rationale,
        excluded_exports=excluded_exports,
    )


TARGETED_FACADE_BUDGET = TargetedFacadeBudget(
    max_public_symbols=220,
    max_init_lines=55,
)

TARGETED_FACADE_OWNERS = (
    _owner(
        "bijux_proteomics.targeted.assay_interference",
        "assay interference review ownership",
    ),
    _owner("bijux_proteomics.targeted.assay_qc", "assay QC ownership"),
    _owner(
        "bijux_proteomics.targeted.biomarker_stability", "biomarker stability ownership"
    ),
    _owner("bijux_proteomics.targeted.carryover", "carryover review ownership"),
    _owner(
        "bijux_proteomics.targeted.discovery_peptide_selection",
        "discovery-to-targeted peptide selection ownership",
    ),
    _owner(
        "bijux_proteomics.targeted.fragment_ratios", "fragment ratio drift ownership"
    ),
    _owner("bijux_proteomics.targeted.panel_design", "targeted panel design ownership"),
    _owner("bijux_proteomics.targeted.panel_redundancy", "panel redundancy ownership"),
    _owner(
        "bijux_proteomics.targeted.result_import", "targeted result import ownership"
    ),
    _owner(
        "bijux_proteomics.targeted.result_validation",
        "targeted result validation ownership",
    ),
    _owner("bijux_proteomics.targeted.target_matrix", "target matrix ownership"),
    _owner(
        "bijux_proteomics.targeted.transition_coelution",
        "transition coelution ownership",
    ),
    _owner(
        "bijux_proteomics.targeted.transition_selection",
        "transition selection ownership",
    ),
    _owner(
        "bijux_proteomics.targeted.validation_evidence_cards",
        "validation evidence card ownership",
    ),
    _owner(
        "bijux_proteomics.targeted.validation_planning",
        "validation experiment planning ownership",
    ),
)


def facade_owner_modules(
    owners: tuple[TargetedFacadeOwner, ...],
) -> tuple[TargetedFacadeOwner, ...]:
    """Return owner modules in their governed targeted facade order."""

    return owners


def list_owned_public_names(owner_module: str) -> tuple[str, ...]:
    """Return the owned public symbols for one targeted owner module."""

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
    owners: tuple[TargetedFacadeOwner, ...],
) -> tuple[tuple[str, ...], dict[str, tuple[str, str]]]:
    """Build one ordered export ledger and import target map for targeted."""

    public_names: list[str] = []
    export_index: dict[str, tuple[str, str]] = {}
    for owner in owners:
        for export_name in list_owned_public_names(owner.owner_module):
            if export_name in owner.excluded_exports:
                continue
            if export_name in export_index:
                conflict_owner, _ = export_index[export_name]
                raise ValueError(
                    "targeted facade export collision for "
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
    """Load one governed targeted export lazily from its owner module."""

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
    """Return a stable directory view for the targeted facade."""

    return sorted(set(package_globals) | set(public_names))


def _module_source_path(owner_module: str) -> Path:
    spec = find_spec(owner_module)
    if spec is None or spec.origin is None:
        raise ValueError(
            f"targeted facade owner module is not discoverable: {owner_module}"
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
    if isinstance(target, ast.Name) and not target.id.startswith("_"):
        return [target.id]
    if isinstance(target, ast.Tuple | ast.List):
        names: list[str] = []
        for element in target.elts:
            names.extend(_public_assigned_names(element))
        return names
    return []
