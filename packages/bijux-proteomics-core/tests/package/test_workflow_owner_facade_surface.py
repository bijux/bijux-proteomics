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


def test_internal_modules_import_workflow_study_owner_modules_directly() -> None:
    violations: list[str] = []

    for path in sorted(_PYTHON_ROOT.rglob("*.py")):
        if path in _WORKFLOW_ROOT_WRAPPERS | {_WORKFLOW_INIT, _WORKFLOW_STUDIES_INIT}:
            continue
        module = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(module):
            if isinstance(node, ast.ImportFrom) and node.module in _WORKFLOW_WRAPPER_MODULES:
                violations.append(
                    f"{path.relative_to(_PYTHON_ROOT)} imports {node.module} instead of the workflow.studies owner module"
                )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in _WORKFLOW_WRAPPER_MODULES:
                        violations.append(
                            f"{path.relative_to(_PYTHON_ROOT)} imports {alias.name} instead of the workflow.studies owner module"
                        )

    assert not violations, "\n".join(violations)
