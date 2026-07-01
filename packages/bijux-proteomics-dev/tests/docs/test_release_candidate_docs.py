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


def test_release_candidate_page_names_current_auditable_and_blocked_families() -> None:
    text = _read_foundation_doc("flagship-release-candidate.md")

    assert "flagship-release-candidate-bundle" in text
    assert (
        "full outsider-readable family packets: `dda`, `dia`, `lfq`, `ptm`, `targeted`"
        in text
    )
    assert "internal-support-only workflow families: `multiplex`" in text
    assert "family_stability_scorecard.json" in text
    assert "paired public benchmark packages" in text
    assert "requested-versus-observed outcome dossier" in text
    assert "independent rerun dossiers" in text
    assert "external review kits" in text
    assert "public artifact index" in text
    assert "Public Artifact Role Matrix" in text
    assert "Release Narrowing Protocol" in text
    assert "Hostile Review Kit" in text
    assert "Why This Repository Is Not Ready Yet" in text
    assert "What Would Make This Repository Ready" in text
    assert "stable coexistence map" in text
    assert "stable language-demotion rule set" in text
    assert "Open [Workflow Families]" in text
    assert "Open [Execution]" in text
    assert "Open [Decision Support]" in text


def test_elite_readiness_scorecard_blocks_repo_wide_elite_language() -> None:
    text = _read_foundation_doc("elite-readiness-scorecard.md")

    assert "| `dda` | `0.77` | yes | no |" in text
    assert "| `dia` | `0.81` | yes | no |" in text
    assert "| `lfq` | `0.81` | yes | no |" in text
    assert "| `ptm` | `0.81` | yes | no |" in text
    assert "| `targeted` | `0.81` | yes | no |" in text
    assert "repository-wide elite" in text
    assert "language remains blocked" in text
    assert "It does not count files, documents, governance volume" in text
    assert "lab-facing outcome dossiers and assay-worth-it ledgers" in text
