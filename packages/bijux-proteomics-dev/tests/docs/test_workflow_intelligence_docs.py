from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _read_doc(name: str) -> str:
    return (
        REPO_ROOT
        / "docs"
        / "05-bijux-proteomics-intelligence"
        / "foundation"
        / name
    ).read_text(encoding="utf-8")


def test_workflow_recommendation_challenge_doc_lists_family_artifacts() -> None:
    text = _read_doc("workflow-recommendation-challenges.md")

    assert "# Workflow Recommendation Challenges" in text
    assert "dda_blinded_recommendation_challenge.json" in text
    assert "dia_blinded_recommendation_challenge.json" in text
    assert "lfq_blinded_recommendation_challenge.json" in text
    assert "ptm_blinded_recommendation_challenge.json" in text
    assert "targeted_blinded_recommendation_challenge.json" in text
    assert "`targeted`: `1` hit, `1` overconfidence, `1` miss" in text


def test_workflow_recommendation_confidence_doc_points_to_audit_bundle() -> None:
    text = _read_doc("workflow-recommendation-confidence.md")

    assert "# Workflow Recommendation Confidence" in text
    assert "counterfactual_recommendations.json" in text
    assert "workflow_overconfidence_audit.json" in text
    assert "workflow_underconfidence_audit.json" in text
    assert "recommendation_regret_ledger.json" in text
    assert "targeted currently carries the strongest overconfidence score at `0.67`" in text
