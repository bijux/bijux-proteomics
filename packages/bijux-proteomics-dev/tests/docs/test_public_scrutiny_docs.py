from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _read_foundation_doc(name: str) -> str:
    return (
        REPO_ROOT / "docs" / "01-bijux-proteomics" / "foundation" / name
    ).read_text(encoding="utf-8")


def test_public_scrutiny_foundation_pages_exist_and_name_real_surfaces() -> None:
    reruns = _read_foundation_doc("independent-rerun-dossiers.md")
    kits = _read_foundation_doc("external-review-kits.md")
    index = _read_foundation_doc("public-artifact-index.md")
    breaks = _read_foundation_doc("what-breaks-elite-trust.md")
    next_page = _read_foundation_doc("what-earns-elite-trust-next.md")

    assert "cross-engine Comet companion package" in reruns
    assert "study-scale cohort lane plus sparse-contrast companion lane" in reruns
    assert "outsider packet" in kits
    assert "independent rerun dossier" in kits
    assert "reverse-engineering the repository package" in index
    assert "companion rerun dossier" in breaks
    assert "independent rerun dossier" in next_page
    assert "external review kit" in next_page


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
    assert "What Breaks Elite Trust" in release_candidate
    assert "What Earns Elite Trust Next" in release_candidate
    assert "independent rerun dossiers" in scorecard.lower()
    assert "Public Artifact Index" in foundation_index
    assert "workflow_public_scrutiny.py" in release_support
    assert "validate_workflow_public_scrutiny()" in release_support
    assert "Public artifact index" in readme
