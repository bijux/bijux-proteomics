# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed public quantification facade catalogs and lazy export helpers."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from importlib import import_module
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Literal

FacadeCollisionPolicy = Literal["error", "prefer_first_owner"]


@dataclass(frozen=True)
class QuantificationFacadeBudget:
    """Public export and `__init__` size budget for one facade."""

    max_public_symbols: int
    max_init_lines: int


@dataclass(frozen=True)
class QuantificationFacadeOwner:
    """One owner module that contributes public symbols to a quantification facade."""

    owner_module: str
    rationale: str
    excluded_exports: tuple[str, ...] = ()


def _owner(
    owner_module: str,
    rationale: str,
    *,
    excluded_exports: tuple[str, ...] = (),
) -> QuantificationFacadeOwner:
    return QuantificationFacadeOwner(
        owner_module=owner_module,
        rationale=rationale,
        excluded_exports=excluded_exports,
    )


MATRIX_FACADE_BUDGET = QuantificationFacadeBudget(
    max_public_symbols=60,
    max_init_lines=80,
)
MISSINGNESS_FACADE_BUDGET = QuantificationFacadeBudget(
    max_public_symbols=35,
    max_init_lines=70,
)
NORMALIZATION_FACADE_BUDGET = QuantificationFacadeBudget(
    max_public_symbols=24,
    max_init_lines=70,
)
PROVENANCE_FACADE_BUDGET = QuantificationFacadeBudget(
    max_public_symbols=120,
    max_init_lines=80,
)
ROLLUP_FACADE_BUDGET = QuantificationFacadeBudget(
    max_public_symbols=30,
    max_init_lines=70,
)
STATISTICS_FACADE_BUDGET = QuantificationFacadeBudget(
    max_public_symbols=110,
    max_init_lines=80,
)
CONTRACTS_FACADE_BUDGET = QuantificationFacadeBudget(
    max_public_symbols=190,
    max_init_lines=120,
)

MATRIX_FACADE_OWNERS = (
    _owner(
        "bijux_proteomics.quantification.matrix.core_matrix",
        "numeric quantification matrix ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.matrix.dense_views",
        "dense quantification matrix view ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.matrix.design_matrix",
        "quantification design matrix ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.matrix.matrix_archive",
        "quantification matrix archive ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.matrix.peptide_intensity_matrix",
        "peptide intensity matrix ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.matrix.protein_intensity_matrix",
        "protein intensity matrix ownership",
    ),
)

MISSINGNESS_FACADE_OWNERS = (
    _owner(
        "bijux_proteomics.quantification.missingness.missingness",
        "missingness classification ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.missingness.peptide_profile_inconsistency",
        "peptide profile inconsistency ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.missingness.readiness",
        "quantification readiness ownership",
    ),
)

NORMALIZATION_FACADE_OWNERS = (
    _owner(
        "bijux_proteomics.quantification.normalization.batch_effect",
        "batch effect ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.normalization.composition",
        "compositional normalization ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.normalization.imputation",
        "imputation ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.normalization.normalization",
        "label-free normalization ownership",
    ),
)

PROVENANCE_FACADE_OWNERS = (
    _owner(
        "bijux_proteomics.quantification.provenance.benchmarks",
        "quantification benchmark provenance ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.provenance.heatmap_preparation",
        "heatmap preparation ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.provenance.replicate_qc",
        "replicate and batch QC ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.provenance.review",
        "quantification review bundle ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.provenance.sample_exploration",
        "sample exploration ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.provenance.value_provenance",
        "quantification value provenance ownership",
    ),
)

ROLLUP_FACADE_OWNERS = (
    _owner(
        "bijux_proteomics.quantification.rollup.model_rollup",
        "model-guided peptide rollup ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.rollup.protein_lfq",
        "protein LFQ ownership",
    ),
)

STATISTICS_FACADE_OWNERS = (
    _owner(
        "bijux_proteomics.quantification.statistics.censored_differential",
        "censored differential ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.differential_abundance",
        "differential abundance ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.differential_imputation_dependence",
        "imputation dependence ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.differential_result_robustness",
        "differential robustness ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.method_agreement",
        "statistical method agreement ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.multi_contrast_consistency",
        "multi-contrast consistency ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.peptide_level_differential",
        "peptide-level differential ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.power_estimation",
        "power estimation ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.statistical_backend",
        "statistical backend ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.time_course_differential",
        "time-course differential ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.uncertainty",
        "uncertainty estimation ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.variance_model",
        "variance model ownership",
    ),
)

CONTRACTS_FACADE_OWNERS = (
    _owner(
        "bijux_proteomics.quantification.contracts.artifact_bundle",
        "artifact bundle contract ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.contracts.design",
        "design contract ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.contracts.differential",
        "differential contract ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.contracts.input_models",
        "quantification input model ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.contracts.input_parsing",
        "quantification input parsing ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.contracts.label_based",
        "label-based quantification contract ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.contracts.matrix_building",
        "quantification matrix-building contract ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.contracts.matrix_models",
        "quantification matrix-model contract ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.contracts.missingness",
        "missingness contract ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.contracts.normalization_imputation",
        "normalization and imputation contract ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.contracts.protein_rollup",
        "protein rollup contract ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.contracts.study_qc",
        "study QC contract ownership",
    ),
)

QUANTIFICATION_ROOT_FACADE_OWNERS = (
    _owner(
        "bijux_proteomics.quantification.contracts",
        "curated quantification contract compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.normalization.batch_effect",
        "batch effect compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.censored_differential",
        "censored differential compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.normalization.composition",
        "composition compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.matrix.core_matrix",
        "matrix core compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.matrix.design_matrix",
        "design matrix compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.differential_abundance",
        "differential abundance compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.differential_imputation_dependence",
        "differential imputation dependence compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.differential_result_robustness",
        "differential robustness compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.provenance.heatmap_preparation",
        "heatmap preparation compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.normalization.imputation",
        "imputation compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.matrix.matrix_archive",
        "matrix archive compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.method_agreement",
        "method agreement compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.rollup.model_rollup",
        "model rollup compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.missingness.missingness",
        "missingness compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.multi_contrast_consistency",
        "multi-contrast consistency compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.normalization.normalization",
        "normalization compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.peptide_level_differential",
        "peptide differential compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.matrix.peptide_intensity_matrix",
        "peptide matrix compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.missingness.peptide_profile_inconsistency",
        "peptide profile inconsistency compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.power_estimation",
        "power estimation compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.matrix.protein_intensity_matrix",
        "protein matrix compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.rollup.protein_lfq",
        "protein LFQ compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.missingness.readiness",
        "readiness compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.provenance.replicate_qc",
        "replicate QC compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.provenance.review",
        "review compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.provenance.sample_exploration",
        "sample exploration compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.statistical_backend",
        "statistical backend compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.time_course_differential",
        "time-course differential compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.uncertainty",
        "uncertainty compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.statistics.variance_model",
        "variance model compatibility ownership",
    ),
    _owner(
        "bijux_proteomics.quantification.provenance.value_provenance",
        "value provenance compatibility ownership",
    ),
)

QUANTIFICATION_ROOT_SUBMODULES = {
    "contracts": "bijux_proteomics.quantification.contracts",
    "matrix": "bijux_proteomics.quantification.matrix",
    "missingness": "bijux_proteomics.quantification.missingness",
    "normalization": "bijux_proteomics.quantification.normalization",
    "provenance": "bijux_proteomics.quantification.provenance",
    "rollup": "bijux_proteomics.quantification.rollup",
    "statistics": "bijux_proteomics.quantification.statistics",
}


def facade_owner_modules(
    owners: tuple[QuantificationFacadeOwner, ...],
) -> tuple[QuantificationFacadeOwner, ...]:
    """Return owner modules in their governed facade order."""

    return owners


def list_owned_public_names(owner_module: str) -> tuple[str, ...]:
    """Return the owned public symbols for one quantification owner module."""

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
    owners: tuple[QuantificationFacadeOwner, ...],
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
                    "quantification facade export collision for "
                    f"{export_name!r}: {conflict_owner} vs {owner.owner_module}"
                )
            public_names.append(export_name)
            export_index[export_name] = (owner.owner_module, export_name)
    return tuple(public_names), export_index


def load_public_export(
    package_name: str,
    package_globals: dict[str, Any],
    export_index: dict[str, tuple[str, str]],
    name: str,
) -> Any:
    """Load one governed quantification export lazily from its owner module."""

    owner = export_index.get(name)
    if owner is None:
        raise AttributeError(f"module {package_name!r} has no attribute {name!r}")
    module_name, export_name = owner
    value = getattr(import_module(module_name), export_name)
    package_globals[name] = value
    return value


def load_public_submodule(
    package_name: str,
    package_globals: dict[str, Any],
    submodules: dict[str, str],
    name: str,
) -> Any:
    """Load one governed quantification submodule lazily from its canonical path."""

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
    """Return a stable directory view for one governed quantification facade."""

    return sorted(set(package_globals) | set(public_names) | set(submodule_names))


def _module_source_path(owner_module: str) -> Path:
    spec = find_spec(owner_module)
    if spec is None or spec.origin is None:
        raise ValueError(
            f"quantification facade owner module is not discoverable: {owner_module}"
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
    "CONTRACTS_FACADE_BUDGET",
    "CONTRACTS_FACADE_OWNERS",
    "FacadeCollisionPolicy",
    "MATRIX_FACADE_BUDGET",
    "MATRIX_FACADE_OWNERS",
    "MISSINGNESS_FACADE_BUDGET",
    "MISSINGNESS_FACADE_OWNERS",
    "NORMALIZATION_FACADE_BUDGET",
    "NORMALIZATION_FACADE_OWNERS",
    "PROVENANCE_FACADE_BUDGET",
    "PROVENANCE_FACADE_OWNERS",
    "QUANTIFICATION_ROOT_FACADE_OWNERS",
    "QUANTIFICATION_ROOT_SUBMODULES",
    "ROLLUP_FACADE_BUDGET",
    "ROLLUP_FACADE_OWNERS",
    "STATISTICS_FACADE_BUDGET",
    "STATISTICS_FACADE_OWNERS",
    "QuantificationFacadeBudget",
    "QuantificationFacadeOwner",
    "build_lazy_export_index",
    "facade_owner_modules",
    "list_owned_public_names",
    "load_public_export",
    "load_public_submodule",
    "module_directory",
]
