# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
import importlib
from pathlib import Path

_WORKFLOW_ROOT = (
    Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics" / "workflow"
)
_ROOT_WRAPPER_TARGETS = {
    "diann_benchmarks.py": "bijux_proteomics.workflow.benchmarks.diann_benchmarks",
    "maxquant_benchmarks.py": (
        "bijux_proteomics.workflow.benchmarks.maxquant_benchmarks"
    ),
    "public_benchmark_descriptors.py": (
        "bijux_proteomics.workflow.benchmarks.public_benchmark_descriptors"
    ),
    "public_benchmark_subset.py": (
        "bijux_proteomics.workflow.benchmarks.public_benchmark_subset"
    ),
    "synthetic_quant_truth.py": (
        "bijux_proteomics.workflow.benchmarks.synthetic_quant_truth"
    ),
    "biological_report_assembly.py": (
        "bijux_proteomics.workflow.reports.biological_report_assembly"
    ),
    "biological_report_claims.py": (
        "bijux_proteomics.workflow.reports.biological_report_claims"
    ),
    "biological_report_html.py": (
        "bijux_proteomics.workflow.reports.biological_report_html"
    ),
    "biological_report_html_support.py": (
        "bijux_proteomics.workflow.reports.biological_report_html_support"
    ),
    "biological_report_models.py": (
        "bijux_proteomics.workflow.reports.biological_report_models"
    ),
    "biological_report_ranking.py": (
        "bijux_proteomics.workflow.reports.biological_report_ranking"
    ),
    "biological_report_rendering.py": (
        "bijux_proteomics.workflow.reports.biological_report_rendering"
    ),
    "biological_report_section_confidence.py": (
        "bijux_proteomics.workflow.reports.biological_report_section_confidence"
    ),
    "biological_report_selection.py": (
        "bijux_proteomics.workflow.reports.biological_report_selection"
    ),
    "biological_reporting.py": "bijux_proteomics.workflow.reports.biological_reporting",
    "biological_result_graph.py": (
        "bijux_proteomics.workflow.reports.biological_result_graph"
    ),
    "cross_study_effect_comparison.py": (
        "bijux_proteomics.workflow.studies.cross_study_effect_comparison"
    ),
    "cross_study_meta_analysis.py": (
        "bijux_proteomics.workflow.studies.cross_study_meta_analysis"
    ),
    "cross_study_pathway_comparison.py": (
        "bijux_proteomics.workflow.studies.cross_study_pathway_comparison"
    ),
    "cross_study_protein_harmonization.py": (
        "bijux_proteomics.workflow.studies.cross_study_protein_harmonization"
    ),
    "cross_species_effect_comparison.py": (
        "bijux_proteomics.workflow.studies.cross_species_effect_comparison"
    ),
    "public_dataset_comparison.py": (
        "bijux_proteomics.workflow.studies.public_dataset_comparison"
    ),
    "cross_study_evidence_cards.py": (
        "bijux_proteomics.workflow.cards.cross_study_evidence_cards"
    ),
    "protein_evidence_cards.py": (
        "bijux_proteomics.workflow.cards.protein_evidence_cards"
    ),
    "protein_mechanism_cards.py": (
        "bijux_proteomics.workflow.cards.protein_mechanism_cards"
    ),
    "artifact_layout.py": "bijux_proteomics.workflow.exports.artifact_layout",
    "interactive_result_bundle.py": (
        "bijux_proteomics.workflow.exports.interactive_result_bundle"
    ),
    "interactive_result_comparison.py": (
        "bijux_proteomics.workflow.exports.interactive_result_comparison"
    ),
    "output_validation.py": "bijux_proteomics.workflow.exports.output_validation",
    "result_archive.py": "bijux_proteomics.workflow.exports.result_archive",
    "result_manifest.py": "bijux_proteomics.workflow.exports.result_manifest",
    "result_search_index.py": ("bijux_proteomics.workflow.exports.result_search_index"),
    "scale_demo.py": "bijux_proteomics.workflow.pipelines.scale_demo",
    "cohort_stratification.py": (
        "bijux_proteomics.workflow.studies.cohort_stratification"
    ),
    "study_result.py": "bijux_proteomics.workflow.studies.study_result",
    "weak_evidence.py": "bijux_proteomics.workflow.pipelines.weak_evidence",
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
        if not (isinstance(node, ast.ImportFrom) and node.module == "__future__")
    ]


def test_workflow_root_wrappers_stay_thin_subpackage_facades() -> None:
    for filename, expected_target in _ROOT_WRAPPER_TARGETS.items():
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

    assert hasattr(exports, "synchronize_workflow_artifact_layout")
    assert hasattr(exports, "build_interactive_result_bundle_from_artifacts")
    assert hasattr(exports, "build_interactive_result_comparison_from_artifacts")
    assert hasattr(exports, "build_workflow_output_validation_report")
    assert hasattr(exports, "build_result_manifest_from_artifacts")
    assert hasattr(exports, "build_result_search_index_from_artifacts")
    assert hasattr(exports, "load_result_archive")

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
