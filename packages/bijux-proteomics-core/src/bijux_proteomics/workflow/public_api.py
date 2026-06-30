# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed public workflow facade catalogs and lazy export helpers."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from importlib import import_module
from importlib.util import find_spec
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WorkflowFacadeOwner:
    """One owned module that contributes public symbols to a workflow facade."""

    owner_module: str
    rationale: str
    excluded_exports: tuple[str, ...] = ()


CARD_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.cross_study_evidence_cards",
        rationale="cross-study evidence card ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.pathway_evidence_cards",
        rationale="pathway evidence card ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.protein_evidence_cards",
        rationale="protein evidence card ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.protein_mechanism_cards",
        rationale="protein mechanism card ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.sample_evidence_cards",
        rationale="sample evidence card ownership",
    ),
)

EXPORT_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.exports.artifact_layout",
        rationale="artifact layout ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.exports.interactive_result_bundle",
        rationale="interactive result bundle ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.exports.interactive_result_comparison",
        rationale="interactive result comparison ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.exports.output_validation",
        rationale="output validation ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.exports.result_archive",
        rationale="result archive ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.exports.result_manifest",
        rationale="result manifest ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.exports.result_search_index",
        rationale="result search index ownership",
    ),
)

DEMO_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.demo.scale_demo",
        rationale="generated scale demo ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.demo.surprising_demo",
        rationale="shipped surprising demo ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.demo.surprising_demo_interrogation",
        rationale="surprising demo interrogation ownership",
    ),
)

STUDY_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cohort_stratification",
        rationale="cohort stratification ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cross_study_effect_comparison",
        rationale="cross-study effect comparison ownership",
        excluded_exports=("CrossStudyProteinStudyInput",),
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cross_study_meta_analysis",
        rationale="cross-study meta-analysis ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cross_study_pathway_comparison",
        rationale="cross-study pathway comparison ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cross_study_protein_harmonization",
        rationale="cross-study protein harmonization ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cross_species_effect_comparison",
        rationale="cross-species effect comparison ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.public_dataset_comparison",
        rationale="public dataset comparison ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.study_result",
        rationale="study result ownership",
    ),
)

REPORT_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.reports.biological_reporting",
        rationale="biological result report ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.reports.biological_result_graph",
        rationale="biological result graph ownership",
    ),
)

PIPELINE_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.advanced_diann",
        rationale="advanced DIA-NN pipeline ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.advanced_fragpipe",
        rationale="advanced FragPipe pipeline ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.advanced_maxquant",
        rationale="advanced MaxQuant pipeline ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.advanced_ptm",
        rationale="advanced PTM pipeline ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.advanced_targeted",
        rationale="advanced targeted pipeline ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.advanced_tmt",
        rationale="advanced TMT pipeline ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.advanced_workflow_family",
        rationale="advanced workflow family ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.dda_biological_workflow",
        rationale="DDA biological workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.dia_dda_comparison",
        rationale="DIA versus DDA comparison ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.dia_differential_analysis",
        rationale="DIA differential analysis ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.diann_biological_workflow",
        rationale="DIA-NN biological workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.discovery_to_assay",
        rationale="discovery-to-assay workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.flagship_run",
        rationale="flagship workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.integrated_scientific_report",
        rationale="integrated scientific report ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.label_based_differential",
        rationale="label-based differential workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.label_based_reporting",
        rationale="label-based reporting workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.maxquant_biological_workflow",
        rationale="MaxQuant biological workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.multi_study",
        rationale="multi-study workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.orchestrator",
        rationale="workflow orchestrator ownership",
        excluded_exports=("WorkflowResult",),
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.ptm_site_workflow",
        rationale="PTM site workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.public_benchmark_runner",
        rationale="public benchmark runner ownership",
        excluded_exports=("load_public_benchmark_descriptor",),
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.demo.scale_demo",
        rationale="scale demo pipeline ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.demo.surprising_demo",
        rationale="surprising demo pipeline ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.demo.surprising_demo_interrogation",
        rationale="surprising demo interrogation ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.tmt_experiment_workflow",
        rationale="TMT experiment workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.trust_bundle",
        rationale="trust bundle workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.weak_evidence",
        rationale="weak evidence workflow ownership",
    ),
)

WORKFLOW_ROOT_SUBMODULES = {
    "cards": "bijux_proteomics.workflow.cards",
    "demo": "bijux_proteomics.workflow.demo",
    "exports": "bijux_proteomics.workflow.exports",
    "pipelines": "bijux_proteomics.workflow.pipelines",
    "reports": "bijux_proteomics.workflow.reports",
    "studies": "bijux_proteomics.workflow.studies",
}

WORKFLOW_ROOT_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.result_types",
        rationale="shared workflow result record ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.exports.result_manifest",
        rationale="result manifest ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.exports.result_search_index",
        rationale="result search index ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.exports.result_archive",
        rationale="result archive ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.reports.biological_reporting",
        rationale="biological report ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.reports.biological_result_graph",
        rationale="biological result graph ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.exports.artifact_layout",
        rationale="workflow artifact layout ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.exports.output_validation",
        rationale="workflow output validation ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.advanced_workflow_family",
        rationale="advanced workflow family ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.blueprint",
        rationale="workflow blueprint ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.advanced_fragpipe",
        rationale="advanced FragPipe pipeline ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.advanced_maxquant",
        rationale="advanced MaxQuant pipeline ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.advanced_ptm",
        rationale="advanced PTM pipeline ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.advanced_targeted",
        rationale="advanced targeted pipeline ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.advanced_tmt",
        rationale="advanced TMT pipeline ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.advanced_diann",
        rationale="advanced DIA-NN pipeline ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cohort_stratification",
        rationale="cohort stratification ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cross_study_effect_comparison",
        rationale="cross-study effect comparison ownership",
        excluded_exports=("CrossStudyProteinStudyInput",),
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.cross_study_evidence_cards",
        rationale="cross-study evidence card ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cross_study_meta_analysis",
        rationale="cross-study meta-analysis ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cross_study_pathway_comparison",
        rationale="cross-study pathway comparison ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cross_study_protein_harmonization",
        rationale="cross-study protein harmonization ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.cross_species_effect_comparison",
        rationale="cross-species effect comparison ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.discovery_to_assay",
        rationale="discovery-to-assay workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.pathway_evidence_cards",
        rationale="pathway evidence card ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.sample_evidence_cards",
        rationale="sample evidence card ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.dda_biological_workflow",
        rationale="DDA biological workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.diann_benchmarks",
        rationale="DIA-NN benchmark ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.diann_biological_workflow",
        rationale="DIA-NN biological workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.flagship_run",
        rationale="flagship workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.exports.interactive_result_comparison",
        rationale="interactive result comparison ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.exports.interactive_result_bundle",
        rationale="interactive result bundle ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.integrated_scientific_report",
        rationale="integrated scientific report ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.maxquant_benchmarks",
        rationale="MaxQuant benchmark ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.maxquant_biological_workflow",
        rationale="MaxQuant biological workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.mechanisms",
        rationale="mechanism report ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.multi_study",
        rationale="multi-study workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.orchestrator",
        rationale="workflow orchestrator ownership",
        excluded_exports=("WorkflowResult",),
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.ptm_site_workflow",
        rationale="PTM site workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.protein_evidence_cards",
        rationale="protein evidence card ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.protein_mechanism_cards",
        rationale="protein mechanism card ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.public_benchmark_descriptors",
        rationale="public benchmark descriptor ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.public_benchmark_subset",
        rationale="public benchmark subset ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.public_benchmark_runner",
        rationale="public benchmark runner ownership",
        excluded_exports=("load_public_benchmark_descriptor",),
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.public_dataset_comparison",
        rationale="public dataset comparison ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.demo.scale_demo",
        rationale="generated scale demo ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.studies.study_result",
        rationale="study result ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.demo.surprising_demo",
        rationale="surprising demo ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.demo.surprising_demo_interrogation",
        rationale="surprising demo interrogation ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.synthetic_quant_truth",
        rationale="synthetic quantification truth ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.targeted_review_workflow",
        rationale="targeted review workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.tmt_experiment_workflow",
        rationale="TMT experiment workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.trust_bundle",
        rationale="trust bundle workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.weak_evidence",
        rationale="weak evidence workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.dia_differential_analysis",
        rationale="DIA differential analysis ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.dia_dda_comparison",
        rationale="DIA versus DDA comparison ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.label_based_differential",
        rationale="label-based differential workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.pipelines.label_based_reporting",
        rationale="label-based reporting workflow ownership",
    ),
)


def facade_owner_modules(
    owners: tuple[WorkflowFacadeOwner, ...],
) -> tuple[WorkflowFacadeOwner, ...]:
    """Return owner module names in their governed facade order."""

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
    owners: tuple[WorkflowFacadeOwner, ...],
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


def load_public_export(
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


def load_public_submodule(
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
        raise ValueError(f"workflow facade owner module is not discoverable: {owner_module}")
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
    "CARD_FACADE_OWNERS",
    "DEMO_FACADE_OWNERS",
    "EXPORT_FACADE_OWNERS",
    "PIPELINE_FACADE_OWNERS",
    "REPORT_FACADE_OWNERS",
    "STUDY_FACADE_OWNERS",
    "WORKFLOW_ROOT_OWNERS",
    "WORKFLOW_ROOT_SUBMODULES",
    "WorkflowFacadeOwner",
    "build_lazy_export_index",
    "facade_owner_modules",
    "list_owned_public_names",
    "load_public_export",
    "load_public_submodule",
    "module_directory",
]
