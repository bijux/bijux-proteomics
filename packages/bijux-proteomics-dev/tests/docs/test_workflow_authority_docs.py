from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _read_doc(name: str) -> str:
    return (REPO_ROOT / "docs" / "01-bijux-proteomics" / "foundation" / name).read_text(
        encoding="utf-8"
    )


def test_workflow_authority_matrix_doc_names_outsider_and_internal_support_sets() -> (
    None
):
    text = _read_doc("workflow-claim-limits.md")

    assert "# Workflow Claim Limits" in text
    assert (
        "Outsider-auditable workflow families today: `dda`, `dia`, `lfq`, `ptm`, `targeted`."
        in text
    )
    assert "Internal-support-only workflow families today: `multiplex`." in text
    assert "family_stability_scorecard.json" in text
    assert "two public benchmark packages plus one" in text
    assert "requested-versus-observed outcome dossier" in text
    assert "assay-worth-it ledger row" in text


def test_multiplex_boundary_doc_keeps_internal_support_limit_explicit() -> None:
    text = _read_doc("why-multiplex-stops-at-internal-support.md")

    assert "# Why Multiplex Stops At Internal Support" in text
    assert "Internal Support Only" in text
    assert "outsider-auditable flagship family" in text
    assert (
        "multiplex_channel_stress_review_package/cross_package_generalization.json"
        in text
    )
    assert "fragile_transfer" in text
    assert "requested-versus-observed outcome dossier" in text


def test_current_capability_limits_keep_consequence_boundary_explicit() -> None:
    text = _read_doc("current-capability-limits.md")

    assert "LFQ, PTM, and targeted remain bounded" in text
    assert "exploratory-only follow-up" in text
    assert "doubled assay burden" in text
    assert "workflow-consequence-maps.md" in text
    assert "what-changed-the-recommendation.md" in text
