# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
import importlib
from pathlib import Path

_REVIEW_ROOT = (
    Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics" / "review"
)
_ROOT_WRAPPER_TARGETS = {
    "analysis_recommendations.py": "bijux_proteomics.review.claims.analysis_recommendations",
    "belief_audit.py": "bijux_proteomics.review.belief.belief_audit",
    "biological_claim_validation.py": (
        "bijux_proteomics.review.claims.biological_claim_validation"
    ),
    "biological_hypotheses.py": "bijux_proteomics.review.claims.biological_hypotheses",
    "biomarker_candidate_ranking.py": (
        "bijux_proteomics.review.belief.biomarker_candidate_ranking"
    ),
    "collaboration.py": "bijux_proteomics.review.cards.collaboration",
    "compact_result_summary.py": "bijux_proteomics.review.cards.compact_result_summary",
    "contracts.py": "bijux_proteomics.review.belief.contracts",
    "evidence_aware_ranking.py": (
        "bijux_proteomics.review.belief.evidence_aware_ranking"
    ),
    "evidence_chain_reconstruction.py": (
        "bijux_proteomics.review.evidence_graph.evidence_chain_reconstruction"
    ),
    "evidence_graph_confidence.py": (
        "bijux_proteomics.review.evidence_graph.evidence_graph_confidence"
    ),
    "evidence_graph_contradictions.py": (
        "bijux_proteomics.review.evidence_graph.evidence_graph_contradictions"
    ),
    "evidence_graph_downgrades.py": (
        "bijux_proteomics.review.evidence_graph.evidence_graph_downgrades"
    ),
    "evidence_graph_export.py": (
        "bijux_proteomics.review.evidence_graph.evidence_graph_export"
    ),
    "evidence_graph_queries.py": (
        "bijux_proteomics.review.evidence_graph.evidence_graph_queries"
    ),
    "evidence_graph_run_diff.py": (
        "bijux_proteomics.review.evidence_graph.evidence_graph_run_diff"
    ),
    "failure_explanations.py": (
        "bijux_proteomics.review.explanations.failure_explanations"
    ),
    "flagship_kernel.py": "bijux_proteomics.review.belief.flagship_kernel",
    "inference_packets.py": "bijux_proteomics.review.cards.inference_packets",
    "protein_family_graphs.py": ("bijux_proteomics.review.cards.protein_family_graphs"),
    "result_explanations.py": (
        "bijux_proteomics.review.explanations.result_explanations"
    ),
    "result_queries.py": "bijux_proteomics.review.claims.result_queries",
    "scientific_conflicts.py": (
        "bijux_proteomics.review.explanations.scientific_conflicts"
    ),
    "scientific_failure_atlas.py": (
        "bijux_proteomics.review.explanations.scientific_failure_atlas"
    ),
    "scientific_story.py": "bijux_proteomics.review.explanations.scientific_story",
    "volcano_plots.py": "bijux_proteomics.review.explanations.volcano_plots",
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


def test_review_root_wrappers_stay_thin_subpackage_facades() -> None:
    for filename, expected_target in _ROOT_WRAPPER_TARGETS.items():
        nodes = _significant_nodes(_REVIEW_ROOT / filename)
        assert nodes, f"{filename} should contain a compatibility re-export"
        assert all(isinstance(node, ast.ImportFrom) for node in nodes), (
            f"{filename} should stay a thin compatibility facade"
        )
        assert any(
            node.module == expected_target
            for node in nodes
            if isinstance(node, ast.ImportFrom)
        ), f"{filename} should re-export its canonical review owner"


def test_review_subpackages_export_representative_owner_surfaces() -> None:
    evidence_graph = importlib.import_module("bijux_proteomics.review.evidence_graph")
    claims = importlib.import_module("bijux_proteomics.review.claims")
    cards = importlib.import_module("bijux_proteomics.review.cards")
    belief = importlib.import_module("bijux_proteomics.review.belief")
    explanations = importlib.import_module("bijux_proteomics.review.explanations")

    assert hasattr(evidence_graph, "build_proteomics_evidence_graph")
    assert hasattr(evidence_graph, "load_lazy_proteomics_evidence_graph")
    assert hasattr(evidence_graph, "render_evidence_graph_final_results_tsv")
    assert hasattr(evidence_graph, "query_protein_evidence_summary")

    assert hasattr(claims, "build_biological_hypothesis_report")
    assert hasattr(claims, "build_result_query_report_from_artifacts")
    assert hasattr(claims, "build_analysis_recommendation_report_from_artifacts")

    assert hasattr(cards, "build_external_reviewer_bundle")
    assert hasattr(cards, "load_standard_card_index")
    assert hasattr(cards, "render_compact_result_summary_markdown")
    assert hasattr(cards, "build_protein_family_evidence_graph")

    assert hasattr(belief, "build_belief_audit_report_from_artifacts")
    assert hasattr(belief, "build_evidence_aware_ranking_report")
    assert hasattr(belief, "decompose_trust_score")

    assert hasattr(explanations, "build_failure_explanation_report")
    assert hasattr(explanations, "evaluate_domain_conflicts")
    assert hasattr(explanations, "build_ptm_volcano_review")


def test_evidence_graph_layer_stays_independent_from_workflow_report_rendering() -> (
    None
):
    evidence_graph_root = _REVIEW_ROOT / "evidence_graph"
    forbidden_modules = {
        "bijux_proteomics.workflow.reports",
        "bijux_proteomics.workflow.reports.biological_report_rendering",
        "bijux_proteomics.workflow.reports.biological_reporting",
        "bijux_proteomics.workflow.biological_report_rendering",
        "bijux_proteomics.workflow.biological_reporting",
    }

    for path in sorted(evidence_graph_root.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in forbidden_modules:
                raise AssertionError(
                    f"{path.name} must not depend on workflow report rendering"
                )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in forbidden_modules:
                        raise AssertionError(
                            f"{path.name} must not depend on workflow report rendering"
                        )
