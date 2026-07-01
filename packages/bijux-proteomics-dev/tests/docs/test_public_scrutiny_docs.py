from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _read_foundation_doc(name: str) -> str:
    return (REPO_ROOT / "docs" / "01-bijux-proteomics" / "foundation" / name).read_text(
        encoding="utf-8"
    )


def test_public_scrutiny_foundation_pages_exist_and_name_real_surfaces() -> None:
    reruns = _read_foundation_doc("independent-rerun-dossiers.md")
    kits = _read_foundation_doc("external-review-kits.md")
    index = _read_foundation_doc("public-artifact-index.md")
    role_matrix = _read_foundation_doc("public-artifact-role-matrix.md")
    narrowing = _read_foundation_doc("release-narrowing-protocol.md")
    hostile = _read_foundation_doc("hostile-review-kit.md")
    why_not_ready = _read_foundation_doc("why-this-repository-is-not-ready-yet.md")
    what_makes_ready = _read_foundation_doc("what-would-make-this-repository-ready.md")

    assert "cross-engine Comet companion package" in reruns
    assert "study-scale cohort lane plus sparse-contrast companion lane" in reruns
    assert "outsider packet" in kits
    assert "independent rerun dossier" in kits
    assert "owner package" in index
    assert "bijux-proteomics-intelligence" in index
    assert "coexistence rationale" in index
    assert "weaker artifact" in role_matrix
    assert "stronger artifact" in role_matrix
    assert "allowed language" in narrowing
    assert "benchmark-asset-quality" in narrowing
    assert "flagship-release-candidate-bundle" in hostile
    assert "whole-repository challenge route" in hostile
    assert "blocked release bars" in why_not_ready
    assert "Benchmark asset quality" in why_not_ready
    assert "Package-boundary stability" not in why_not_ready
    assert "Package-quality gaps" in what_makes_ready
    assert "Docs failures" in what_makes_ready


def test_existing_release_pages_link_to_public_scrutiny_surfaces() -> None:
    release_candidate = _read_foundation_doc("flagship-release-candidate.md")
    scorecard = _read_foundation_doc("elite-readiness-scorecard.md")
    foundation_index = _read_foundation_doc("index.md")
    release_support = (
        REPO_ROOT
        / "docs"
        / "08-bijux-proteomics-maintain"
        / "bijux-proteomics-dev"
        / "release-support.md"
    ).read_text(encoding="utf-8")
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "independent rerun dossiers" in release_candidate
    assert "external review kits" in release_candidate
    assert "public artifact index" in release_candidate
    assert "Public Artifact Role Matrix" in release_candidate
    assert "Release Narrowing Protocol" in release_candidate
    assert "Hostile Review Kit" in release_candidate
    assert "Why This Repository Is Not Ready Yet" in release_candidate
    assert "What Would Make This Repository Ready" in release_candidate
    assert "independent rerun dossiers" in scorecard.lower()
    assert "Release Narrowing Protocol" in foundation_index
    assert "Hostile Review Kit" in foundation_index
    assert "What Would Make This Repository Ready" in foundation_index
    assert "Public Artifact Index" in foundation_index
    assert "Public Artifact Role Matrix" in foundation_index
    assert "workflow_public_scrutiny.py" in release_support
    assert "hostile_review_pages.py" in release_support
    assert "release_narrowing_protocol.py" in release_support
    assert "final_preflight.py" in release_support
    assert "make release-preflight" in release_support
    assert "validate_workflow_public_scrutiny()" in release_support
    assert "Public artifact index" in readme
