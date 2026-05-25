# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
import importlib
from pathlib import Path


_CORE_SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics"
_STUDY_ROOT = _CORE_SRC_ROOT / "study"
_LAB_ROOT = _CORE_SRC_ROOT / "lab"
_STUDY_WRAPPER_TARGETS = {
    "contrasts.py": "bijux_proteomics.study.design.contrasts",
    "design_classification.py": "bijux_proteomics.study.design.design_classification",
    "design_diagnostics.py": "bijux_proteomics.study.design.design_diagnostics",
    "design_validity.py": "bijux_proteomics.study.design.design_validity",
    "experiment_confidence.py": "bijux_proteomics.study.design.experiment_confidence",
    "experiment_design.py": "bijux_proteomics.study.design.experiment_design",
    "experiment_feasibility.py": "bijux_proteomics.study.design.experiment_feasibility",
    "replicate_structure.py": "bijux_proteomics.study.design.replicate_structure",
    "contracts.py": "bijux_proteomics.study.metadata.contracts",
    "sample_metadata.py": "bijux_proteomics.study.metadata.sample_metadata",
    "sample_run_identity.py": "bijux_proteomics.study.metadata.sample_run_identity",
    "sample_sheet_repairs.py": "bijux_proteomics.study.metadata.sample_sheet_repairs",
    "carryover.py": "bijux_proteomics.lab.carryover",
    "lc_drift.py": "bijux_proteomics.lab.lc_drift",
    "lab_protocol_context.py": "bijux_proteomics.lab.protocol_context",
    "protocol_consistency.py": "bijux_proteomics.lab.protocol_consistency",
    "laboratory_operations.py": "bijux_proteomics.lab.operations",
    "laboratory_plans.py": "bijux_proteomics.lab.planning",
    "qc.py": "bijux_proteomics.lab.qc",
    "qc_benchmarks.py": "bijux_proteomics.lab.qc_benchmarks",
}
_FORBIDDEN_DESIGN_VALIDITY_IMPORTS = {
    "bijux_proteomics.study.design_validity",
    "bijux_proteomics.study.design.design_validity",
}
_FORBIDDEN_DESIGN_VALIDITY_NAMES = {
    "ExperimentDesignValidityIssue",
    "ExperimentDesignValiditySummary",
    "ExperimentDesignValidityReport",
    "build_experiment_design_validity_report",
    "render_experiment_design_validity_tsv",
    "require_valid_experiment_design_for_differential_analysis",
}


def _significant_nodes(path: Path) -> list[ast.stmt]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    nodes = list(tree.body)
    if (
        nodes
        and isinstance(nodes[0], ast.Expr)
        and isinstance(nodes[0].value, ast.Constant)
        and isinstance(nodes[0].value.value, str)
    ):
        nodes = nodes[1:]
    return [
        node
        for node in nodes
        if not (
            isinstance(node, ast.ImportFrom) and node.module == "__future__"
        )
    ]


def test_study_root_wrappers_stay_thin_boundary_facades() -> None:
    for filename, expected_target in _STUDY_WRAPPER_TARGETS.items():
        nodes = _significant_nodes(_STUDY_ROOT / filename)
        assert nodes, f"{filename} should contain a compatibility re-export"
        assert all(isinstance(node, ast.ImportFrom) for node in nodes), (
            f"{filename} should stay a thin compatibility facade"
        )
        assert any(
            node.module == expected_target
            for node in nodes
            if isinstance(node, ast.ImportFrom)
        ), f"{filename} should re-export its canonical owner"


def test_study_design_metadata_and_lab_export_representative_owner_surfaces() -> None:
    design = importlib.import_module("bijux_proteomics.study.design")
    metadata = importlib.import_module("bijux_proteomics.study.metadata")
    lab = importlib.import_module("bijux_proteomics.lab")

    assert hasattr(design, "build_experiment_design")
    assert hasattr(design, "build_experiment_design_validity_report")
    assert hasattr(design, "build_experiment_confidence_report")
    assert hasattr(design, "build_replicate_structure_report")

    assert hasattr(metadata, "build_study_metadata_model")
    assert hasattr(metadata, "parse_sample_metadata_table")
    assert hasattr(metadata, "build_sample_run_identity_report")
    assert hasattr(metadata, "build_sample_sheet_repair_suggestion_report")

    assert hasattr(lab, "build_lcms_run_qc_report")
    assert hasattr(lab, "build_protocol_consistency_report")
    assert hasattr(lab, "build_lab_cost_model_report")
    assert hasattr(lab, "transition_assay_progression")


def test_lab_modules_do_not_duplicate_design_validity_logic() -> None:
    for path in sorted(_LAB_ROOT.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (
                node.module in _FORBIDDEN_DESIGN_VALIDITY_IMPORTS
            ):
                raise AssertionError(
                    f"{path.name} must not import study design-validity owners"
                )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in _FORBIDDEN_DESIGN_VALIDITY_IMPORTS:
                        raise AssertionError(
                            f"{path.name} must not import study design-validity owners"
                        )
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name in _FORBIDDEN_DESIGN_VALIDITY_NAMES:
                    raise AssertionError(
                        f"{path.name} must not define duplicated design-validity owners"
                    )
