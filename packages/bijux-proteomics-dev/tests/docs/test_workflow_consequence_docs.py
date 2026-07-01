from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.release.governance.workflow_consequence_docs import run

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_workflow_consequence_docs_are_up_to_date() -> None:
    assert run(check=True) == 0


def test_workflow_consequence_maps_doc_covers_all_families_and_decision_grade_limits() -> (
    None
):
    text = _read("docs/01-bijux-proteomics/foundation/workflow-consequence-maps.md")

    assert "# Workflow Consequence Maps" in text
    for workflow_family in ("dda", "dia", "lfq", "multiplex", "ptm", "targeted"):
        assert f"### `{workflow_family}`" in text
    assert "current strongest allowed posture" in text
    assert "decision-grade remains blocked" in text
    assert "What Changed The Recommendation" in text
    assert "Outcome Learning Loops" in text
    assert "Workflow Refusal Handbook" in text


def test_what_changed_the_recommendation_doc_names_counterfactual_and_outcome_drivers() -> (
    None
):
    text = _read(
        "docs/01-bijux-proteomics/foundation/what-changed-the-recommendation.md"
    )

    assert "# What Changed The Recommendation" in text
    assert "without comparator evidence" in text
    assert "without literature evidence" in text
    assert "with doubled lab burden" in text
    assert "matrix-shift repeat exposed library-conditioned fragility" in text
    assert (
        "targeted follow-up delivered useful calibration and interference clarification"
        in text
    )


def test_outcome_learning_loops_doc_names_requested_observed_and_next_adjustments() -> (
    None
):
    text = _read("docs/07-bijux-proteomics-lab/foundation/outcome-learning-loops.md")

    assert "# Outcome Learning Loops" in text
    assert "requested assays" in text
    assert "observed assays" in text
    assert "next adjustments" in text
    assert (
        "no shipped requested-versus-observed outcome loop exists for this family yet"
        in text
    )
    assert (
        "feed the revised follow-up result back into future recommendation posture"
        in text
    )


def test_workflow_refusal_handbook_doc_names_stop_rerun_narrow_and_refuse() -> None:
    text = _read("docs/07-bijux-proteomics-lab/foundation/workflow-refusal-handbook.md")

    assert "# Workflow Refusal Handbook" in text
    assert "stop when" in text
    assert "rerun when" in text
    assert "narrow when" in text
    assert "refuse when" in text
    assert (
        "keep multiplex at internal support until the family earns its own outsider review and lab consequence closure"
        in text
    )
