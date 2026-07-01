# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
import importlib
from pathlib import Path

from bijux_proteomics.workflow.public_api import (
    WORKFLOW_ROOT_OWNER_FILES,
    WORKFLOW_ROOT_WRAPPER_TARGETS,
)

_WORKFLOW_ROOT = (
    Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics" / "workflow"
)
_WORKFLOW_STUDIES_ROOT = _WORKFLOW_ROOT / "studies"


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
        if not (isinstance(node, ast.ImportFrom) and node.module == "__future__")
    ]


def test_workflow_root_wrappers_stay_thin_subpackage_facades() -> None:
    for filename, expected_target in WORKFLOW_ROOT_WRAPPER_TARGETS.items():
        nodes = _significant_nodes(_WORKFLOW_ROOT / filename)
        assert nodes, f"{filename} should contain a compatibility re-export"
        assert all(isinstance(node, ast.ImportFrom) for node in nodes), (
            f"{filename} should stay a thin compatibility facade"
        )
        assert any(
            node.module == expected_target
            for node in nodes
            if isinstance(node, ast.ImportFrom)
        ), f"{filename} should re-export its canonical workflow owner"


def test_workflow_study_wrappers_stay_thin_compatibility_facades() -> None:
    expected_targets = {
        "cross_study_effect_comparison.py": (
            "bijux_proteomics.workflow.studies.cross_study.effect_comparison"
        ),
        "cross_study_meta_analysis.py": (
            "bijux_proteomics.workflow.studies.cross_study.meta_analysis"
        ),
        "cross_study_pathway_comparison.py": (
            "bijux_proteomics.workflow.studies.cross_study.pathway_comparison"
        ),
        "cross_study_protein_harmonization.py": (
            "bijux_proteomics.workflow.studies.cross_study.protein_harmonization"
        ),
        "study_result.py": "bijux_proteomics.workflow.studies.study_results",
    }

    for filename, expected_target in expected_targets.items():
        nodes = _significant_nodes(_WORKFLOW_STUDIES_ROOT / filename)
        assert nodes, f"{filename} should contain a compatibility re-export"
        assert all(isinstance(node, ast.ImportFrom) for node in nodes), (
            f"{filename} should stay a thin compatibility facade"
        )
        assert any(
            node.module == expected_target
            for node in nodes
            if isinstance(node, ast.ImportFrom)
        ), f"{filename} should re-export its canonical study owner"


def test_workflow_root_keeps_only_shared_facade_owners() -> None:
    owner_files: set[str] = set()
    for path in _WORKFLOW_ROOT.glob("*.py"):
        nodes = _significant_nodes(path)
        if nodes and all(isinstance(node, ast.ImportFrom) for node in nodes):
            continue
        owner_files.add(path.name)
    assert owner_files == WORKFLOW_ROOT_OWNER_FILES


def test_workflow_subpackages_export_representative_owner_surfaces() -> None:
    benchmarks = importlib.import_module("bijux_proteomics.workflow.benchmarks")
    reports = importlib.import_module("bijux_proteomics.workflow.reports")
    cards = importlib.import_module("bijux_proteomics.workflow.cards")
    exports = importlib.import_module("bijux_proteomics.workflow.exports")
    demo = importlib.import_module("bijux_proteomics.workflow.demo")
    studies = importlib.import_module("bijux_proteomics.workflow.studies")

    assert hasattr(benchmarks, "PublicBenchmarkDescriptor")
    assert hasattr(benchmarks, "load_public_benchmark_descriptor")
    assert hasattr(benchmarks, "build_public_benchmark_subset")
    assert hasattr(benchmarks, "build_diann_benchmark_report")
    assert hasattr(benchmarks, "build_maxquant_benchmark_report")
    assert hasattr(benchmarks, "generate_quant_truth_dataset")
    assert hasattr(benchmarks, "render_synthetic_quant_truth_tsv")

    assert hasattr(reports, "build_biological_result_report_bundle")
    assert hasattr(reports, "export_biological_result_report_bundle")
    assert hasattr(reports, "build_biological_result_graph_report")

    assert hasattr(cards, "build_protein_evidence_card_report")
    assert hasattr(cards, "build_protein_mechanism_card_report")
    assert hasattr(cards, "build_cross_study_evidence_card_report")
    assert hasattr(cards, "build_mechanism_cards")
    assert hasattr(cards, "render_mechanism_cards_tsv")

    assert hasattr(exports, "synchronize_workflow_artifact_layout")
    assert hasattr(exports, "build_interactive_result_bundle_from_artifacts")
    assert hasattr(exports, "build_interactive_result_comparison_from_artifacts")
    assert hasattr(exports, "build_workflow_output_validation_report")
    assert hasattr(exports, "build_result_manifest_from_artifacts")
    assert hasattr(exports, "build_result_search_index_from_artifacts")
    assert hasattr(exports, "load_result_archive")
    assert hasattr(exports, "export_targeted_matrix_workflow_artifacts")
    assert hasattr(exports, "export_targeted_assay_qc_workflow_artifacts")

    assert hasattr(demo, "ScaleDemoConfig")
    assert hasattr(demo, "run_scale_demo")
    assert hasattr(demo, "render_scale_demo_summary_tsv")
    assert hasattr(demo, "load_surprising_demo_manifest")
    assert hasattr(demo, "run_surprising_demo")
    assert hasattr(demo, "build_surprising_demo_example_requests")
    assert hasattr(demo, "build_surprising_demo_interrogation_report")

    assert hasattr(studies, "build_cohort_stratification_report")
    assert hasattr(studies, "build_cross_study_effect_comparison_report")
    assert hasattr(studies, "build_cross_study_meta_analysis_report")
    assert hasattr(studies, "build_cross_study_pathway_comparison_report")
    assert hasattr(studies, "build_cross_study_protein_harmonization_report")
    assert hasattr(studies, "build_cross_species_effect_comparison_report")
    assert hasattr(studies, "build_public_dataset_comparison_report")
    assert hasattr(studies, "build_proteomics_study_result")
    assert hasattr(studies, "ProteomicsStudyKind")


def test_workflow_facades_import_owned_catalogs_instead_of_public_api() -> None:
    for path in _WORKFLOW_ROOT.rglob("__init__.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                assert node.module != "bijux_proteomics.workflow.public_api", (
                    f"{path} should import runtime helpers and owned catalogs directly"
                )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "bijux_proteomics.workflow.public_api", (
                        f"{path} should import runtime helpers and owned catalogs directly"
                    )
