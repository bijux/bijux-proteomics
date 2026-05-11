from __future__ import annotations

from pathlib import Path

import pytest

import bijux_proteomics_dev.release.governance.workflow_consequence_chain as chain_module
from bijux_proteomics_dev.release.governance.workflow_consequence_chain import (
    RecommendationStrength,
    WorkflowConsequenceCoherenceIssue,
    WorkflowConsequenceMap,
    build_workflow_consequence_maps,
    build_workflow_outcome_learning_loops,
    build_workflow_recommendation_changes,
    validate_workflow_consequence_coherence,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_workflow_consequence_maps_keep_shared_posture_per_family() -> None:
    maps = build_workflow_consequence_maps()
    by_family = {entry.workflow_family: entry for entry in maps}

    assert tuple(entry.workflow_family for entry in maps) == (
        KnowledgeWorkflowFamily.DDA,
        KnowledgeWorkflowFamily.DIA,
        KnowledgeWorkflowFamily.LFQ,
        KnowledgeWorkflowFamily.MULTIPLEX,
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.TARGETED,
    )
    assert (
        by_family[KnowledgeWorkflowFamily.MULTIPLEX].weakest_allowed_strength
        is RecommendationStrength.DO_NOT_RECOMMEND
    )
    for workflow_family in (
        KnowledgeWorkflowFamily.LFQ,
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.TARGETED,
    ):
        assert (
            by_family[workflow_family].weakest_allowed_strength
            is RecommendationStrength.RECOMMEND_WITH_DOWNGRADE
        )


def test_workflow_recommendation_changes_capture_counterfactuals_and_outcomes() -> None:
    changes = {
        entry.workflow_family: entry
        for entry in build_workflow_recommendation_changes()
    }

    assert (
        changes[KnowledgeWorkflowFamily.DIA].observed_outcome_strength
        is RecommendationStrength.DO_NOT_RECOMMEND
    )
    assert (
        changes[KnowledgeWorkflowFamily.PTM].observed_outcome_strength
        is RecommendationStrength.RECOMMEND_WITH_DOWNGRADE
    )
    assert (
        changes[KnowledgeWorkflowFamily.MULTIPLEX].primary_change_driver
        == "no public counterfactual report is shipped for this family because recommendation posture is already held below outsider-facing consequence closure"
    )


def test_workflow_outcome_learning_loops_cover_all_families() -> None:
    loops = {
        entry.workflow_family: entry
        for entry in build_workflow_outcome_learning_loops()
    }

    assert tuple(loops) == (
        KnowledgeWorkflowFamily.DDA,
        KnowledgeWorkflowFamily.DIA,
        KnowledgeWorkflowFamily.LFQ,
        KnowledgeWorkflowFamily.MULTIPLEX,
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.TARGETED,
    )
    assert loops[KnowledgeWorkflowFamily.MULTIPLEX].learning_points == (
        "no shipped requested-versus-observed outcome loop exists for this family yet",
    )
    assert (
        loops[KnowledgeWorkflowFamily.TARGETED].revised_strength
        is RecommendationStrength.RECOMMEND_WITH_DOWNGRADE
    )


def test_workflow_consequence_coherence_matches_current_repo_docs() -> None:
    assert validate_workflow_consequence_coherence(REPO_ROOT) == ()


def test_workflow_consequence_coherence_blocks_cross_package_posture_drift(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        chain_module,
        "build_workflow_consequence_maps",
        lambda: (
            WorkflowConsequenceMap(
                workflow_family=KnowledgeWorkflowFamily.DDA,
                benchmark_id="benchmark:dda_search_reproducibility",
                knowledge_strength=RecommendationStrength.RECOMMEND_WITH_DOWNGRADE,
                intelligence_strength=RecommendationStrength.RECOMMEND,
                lab_strength=RecommendationStrength.RECOMMEND_WITH_DOWNGRADE,
                weakest_allowed_strength=RecommendationStrength.RECOMMEND_WITH_DOWNGRADE,
                contradiction_summary="bounded contradiction",
                contradiction_next_action="keep downgrade visible",
                recommendation_summary="current recommendation posture is strong",
                recommendation_blockers=(),
                lab_summary="exploratory only",
                control_demands=(),
                burden_tradeoffs=(),
                cost_of_being_wrong=(),
                evidence_paths=(
                    "artifacts/intelligence/recommendation-packets/dda.json",
                ),
            ),
        ),
    )
    consequence_doc = tmp_path / "workflow-consequence-maps.md"
    change_doc = tmp_path / "what-changed-the-recommendation.md"
    learning_doc = tmp_path / "outcome-learning-loops.md"
    refusal_doc = tmp_path / "workflow-refusal-handbook.md"
    consequence_doc.write_text(
        "### `dda`\n- current strongest allowed posture: `recommend_with_downgrade`\n- decision-grade remains blocked when the weakest downstream boundary stays below a full recommendation.\n### `lfq`\n- current strongest allowed posture: `recommend_with_downgrade`\n- decision-grade remains blocked when the weakest downstream boundary stays below a full recommendation.\n### `ptm`\n- current strongest allowed posture: `recommend_with_downgrade`\n- decision-grade remains blocked when the weakest downstream boundary stays below a full recommendation.\n### `targeted`\n- current strongest allowed posture: `recommend_with_downgrade`\n- decision-grade remains blocked when the weakest downstream boundary stays below a full recommendation.\n",
        encoding="utf-8",
    )
    for path in (change_doc, learning_doc, refusal_doc):
        path.write_text(
            "### `lfq`\n### `ptm`\n### `targeted`\n",
            encoding="utf-8",
        )
    monkeypatch.setattr(chain_module, "WORKFLOW_CONSEQUENCE_MAPS_PATH", consequence_doc)
    monkeypatch.setattr(chain_module, "RECOMMENDATION_CHANGE_PATH", change_doc)
    monkeypatch.setattr(
        chain_module, "LAB_CONSEQUENCE_OUTCOME_LEARNING_PATH", learning_doc
    )
    monkeypatch.setattr(
        chain_module, "LAB_CONSEQUENCE_REFUSAL_HANDBOOK_PATH", refusal_doc
    )

    issues = validate_workflow_consequence_coherence(REPO_ROOT)

    assert (
        WorkflowConsequenceCoherenceIssue(
            code="cross-package-posture-disagreement",
            detail=(
                "dda disagrees across knowledge, intelligence, and lab: "
                "recommend_with_downgrade, recommend, recommend_with_downgrade"
            ),
        )
        in issues
    )
    assert (
        WorkflowConsequenceCoherenceIssue(
            code="recommendation-strength-exceeds-downstream-boundary",
            detail=(
                "dda intelligence posture recommend exceeds weakest downstream boundary "
                "recommend_with_downgrade"
            ),
        )
        in issues
    )
