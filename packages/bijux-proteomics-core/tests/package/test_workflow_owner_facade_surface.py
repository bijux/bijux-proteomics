# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

_PYTHON_ROOT = Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics"
_WORKFLOW_ROOT = _PYTHON_ROOT / "workflow"
_WORKFLOW_INIT = _WORKFLOW_ROOT / "__init__.py"
_WORKFLOW_STUDIES_INIT = _WORKFLOW_ROOT / "studies" / "__init__.py"
_WORKFLOW_ROOT_WRAPPERS = {
    _WORKFLOW_ROOT / "cohort_stratification.py",
    _WORKFLOW_ROOT / "cross_species_effect_comparison.py",
    _WORKFLOW_ROOT / "cross_study_effect_comparison.py",
    _WORKFLOW_ROOT / "cross_study_meta_analysis.py",
    _WORKFLOW_ROOT / "cross_study_pathway_comparison.py",
    _WORKFLOW_ROOT / "cross_study_protein_harmonization.py",
    _WORKFLOW_ROOT / "public_dataset_comparison.py",
    _WORKFLOW_ROOT / "study_result.py",
}
_WORKFLOW_WRAPPER_MODULES = {
    "bijux_proteomics.workflow.cohort_stratification",
    "bijux_proteomics.workflow.cross_species_effect_comparison",
    "bijux_proteomics.workflow.cross_study_effect_comparison",
    "bijux_proteomics.workflow.cross_study_meta_analysis",
    "bijux_proteomics.workflow.cross_study_pathway_comparison",
    "bijux_proteomics.workflow.cross_study_protein_harmonization",
    "bijux_proteomics.workflow.public_dataset_comparison",
    "bijux_proteomics.workflow.study_result",
}
_WORKFLOW_SUBPACKAGE_FACADE_MODULES = {
    "bijux_proteomics.workflow.cards",
    "bijux_proteomics.workflow.demo",
    "bijux_proteomics.workflow.exports",
    "bijux_proteomics.workflow.studies",
}
_WORKFLOW_PIPELINE_FACADE_MODULES = {
    "bijux_proteomics.workflow.pipelines.benchmarking",
    "bijux_proteomics.workflow.pipelines.comparative",
    "bijux_proteomics.workflow.pipelines.operations",
    "bijux_proteomics.workflow.pipelines.synthesis",
}


def _collect_direct_import_violations(
    disallowed_modules: set[str], *, ignored_paths: set[Path], owner_description: str
) -> list[str]:
    violations: list[str] = []

    for path in sorted(_PYTHON_ROOT.rglob("*.py")):
        if path in ignored_paths:
            continue
        module = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(module):
            if isinstance(node, ast.ImportFrom) and node.module in disallowed_modules:
                violations.append(
                    f"{path.relative_to(_PYTHON_ROOT)} imports {node.module} instead of {owner_description}"
                )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in disallowed_modules:
                        violations.append(
                            f"{path.relative_to(_PYTHON_ROOT)} imports {alias.name} instead of {owner_description}"
                        )

    return violations


def test_internal_modules_import_workflow_owner_modules_directly() -> None:
    violations = _collect_direct_import_violations(
        {"bijux_proteomics.workflow"},
        ignored_paths={_WORKFLOW_INIT},
        owner_description="an owned workflow module",
    )

    assert not violations, "\n".join(violations)


def test_internal_modules_import_workflow_study_owner_modules_directly() -> None:
    violations = _collect_direct_import_violations(
        _WORKFLOW_WRAPPER_MODULES,
        ignored_paths=_WORKFLOW_ROOT_WRAPPERS | {_WORKFLOW_INIT, _WORKFLOW_STUDIES_INIT},
        owner_description="the workflow.studies owner module",
    )

    assert not violations, "\n".join(violations)


def test_internal_modules_import_workflow_subpackage_owner_modules_directly() -> None:
    violations = _collect_direct_import_violations(
        _WORKFLOW_SUBPACKAGE_FACADE_MODULES,
        ignored_paths={
            _WORKFLOW_INIT,
            _WORKFLOW_ROOT / "cards" / "__init__.py",
            _WORKFLOW_ROOT / "demo" / "__init__.py",
            _WORKFLOW_ROOT / "exports" / "__init__.py",
            _WORKFLOW_STUDIES_INIT,
        },
        owner_description="the workflow subpackage owner module",
    )
    assert not violations, "\n".join(violations)


def test_internal_modules_import_workflow_pipeline_owner_modules_directly() -> None:
    violations = _collect_direct_import_violations(
        _WORKFLOW_PIPELINE_FACADE_MODULES,
        ignored_paths={
            _WORKFLOW_ROOT / "pipelines" / "benchmarking" / "__init__.py",
            _WORKFLOW_ROOT / "pipelines" / "comparative" / "__init__.py",
            _WORKFLOW_ROOT / "pipelines" / "operations" / "__init__.py",
            _WORKFLOW_ROOT / "pipelines" / "synthesis" / "__init__.py",
        },
        owner_description="the workflow pipeline owner module",
    )
    assert not violations, "\n".join(violations)
