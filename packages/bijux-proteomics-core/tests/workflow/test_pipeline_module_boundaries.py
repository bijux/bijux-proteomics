# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
import importlib
from pathlib import Path


_PIPELINE_MODULES = (
    "advanced_diann",
    "advanced_fragpipe",
    "advanced_maxquant",
    "advanced_ptm",
    "advanced_targeted",
    "advanced_tmt",
    "dda_biological_workflow",
    "dia_dda_comparison",
    "dia_differential_analysis",
    "diann_biological_workflow",
    "discovery_to_assay",
    "flagship_run",
    "integrated_scientific_report",
    "label_based_differential_analysis",
    "label_based_reporting",
    "maxquant_biological_workflow",
    "multi_study",
    "orchestrator",
    "ptm_site_workflow",
    "public_benchmark_runner",
    "surprising_demo",
    "surprising_demo_interrogation",
    "tmt_experiment_workflow",
    "trust_bundle",
    "weak_evidence",
)
_FORBIDDEN_HELPER_TOKENS = (
    "_parse_",
    "_score_",
    "_fdr_",
    "_quant_",
    "_normalize_",
    "_enrich_",
)
_APPROVED_ASSEMBLY_HELPERS = {
    "dda_biological_workflow": {
        "_normalize_search_results",
        "_parse_source_protein_refs",
    },
    "dia_dda_comparison": {"_parse_optional_float"},
    "label_based_differential_analysis": {"_normalize_input_report"},
}


def _workflow_source_root() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "src"
        / "bijux_proteomics"
        / "workflow"
    )


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
            isinstance(node, ast.ImportFrom)
            and node.module == "__future__"
        )
    ]


def test_workflow_root_owners_are_thin_pipeline_facades() -> None:
    root = _workflow_source_root()

    for module_name in _PIPELINE_MODULES:
        path = root / f"{module_name}.py"
        nodes = _significant_nodes(path)
        assert nodes, f"{path} should contain a pipeline re-export"
        assert all(isinstance(node, ast.ImportFrom) for node in nodes), (
            f"{path} should stay a thin compatibility facade"
        )
        assert any(
            node.module == f"bijux_proteomics.workflow.pipelines.{module_name}"
            for node in nodes
            if isinstance(node, ast.ImportFrom)
        ), f"{path} should re-export its owned workflow pipeline"


def test_workflow_pipelines_avoid_low_level_algorithm_helpers() -> None:
    root = _workflow_source_root() / "pipelines"

    for module_name in _PIPELINE_MODULES:
        path = root / f"{module_name}.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        defs = [
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        offending = [
            name
            for name in defs
            if name.startswith("_")
            and any(token in name for token in _FORBIDDEN_HELPER_TOKENS)
            and name
            not in _APPROVED_ASSEMBLY_HELPERS.get(module_name, set())
        ]
        assert not offending, (
            f"{path} should orchestrate domain owners instead of defining low-level "
            f"algorithm helpers: {offending}"
        )


def test_workflow_pipelines_match_legacy_wrapper_exports() -> None:
    pipelines = importlib.import_module("bijux_proteomics.workflow.pipelines")
    assert pipelines.__name__ == "bijux_proteomics.workflow.pipelines"

    wrapper_to_attr = {
        "dda_biological_workflow": "build_dda_biological_workflow_bundle",
        "advanced_tmt": "run_advanced_tmt_workflow",
        "advanced_targeted": "run_targeted_validation_workflow",
        "dia_dda_comparison": "build_diann_vs_dda_psm_comparison_report",
        "dia_differential_analysis": "build_dia_differential_analysis_report",
        "diann_biological_workflow": "build_diann_biological_workflow_bundle",
        "label_based_differential_analysis": (
            "build_label_based_differential_analysis_report"
        ),
        "label_based_reporting": "build_tmt_label_based_report_bundle",
        "maxquant_biological_workflow": "build_maxquant_biological_workflow_bundle",
        "orchestrator": "run_proteomics_workflow",
        "ptm_site_workflow": "build_ptm_site_workflow_bundle",
        "surprising_demo": "run_surprising_demo",
        "tmt_experiment_workflow": "build_tmt_experiment_workflow_bundle",
        "trust_bundle": "build_trust_bundle",
        "weak_evidence": "run_weak_evidence_benchmark",
    }
    for module_name, attr_name in wrapper_to_attr.items():
        wrapper = importlib.import_module(f"bijux_proteomics.workflow.{module_name}")
        owner = importlib.import_module(
            f"bijux_proteomics.workflow.pipelines.{module_name}"
        )
        assert getattr(wrapper, attr_name) is getattr(owner, attr_name)


def test_demo_pipeline_wrappers_delegate_to_demo_owners() -> None:
    root = _workflow_source_root() / "pipelines"
    expected_targets = {
        "surprising_demo.py": "bijux_proteomics.workflow.demo.surprising_demo",
        "surprising_demo_interrogation.py": (
            "bijux_proteomics.workflow.demo.surprising_demo_interrogation"
        ),
    }

    for filename, expected_target in expected_targets.items():
        nodes = _significant_nodes(root / filename)
        assert nodes, f"{filename} should contain a demo re-export"
        assert all(isinstance(node, ast.ImportFrom) for node in nodes), (
            f"{filename} should stay a thin compatibility facade"
        )
        assert any(
            node.module == expected_target
            for node in nodes
            if isinstance(node, ast.ImportFrom)
        ), f"{filename} should re-export its owned demo surface"
