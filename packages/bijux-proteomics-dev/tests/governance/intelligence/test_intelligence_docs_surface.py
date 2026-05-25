from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
INTELLIGENCE_ROOT = REPO_ROOT / "packages" / "bijux-proteomics-intelligence"


def _intelligence_docs() -> tuple[str, str, str, str, str]:
    return (
        (INTELLIGENCE_ROOT / "README.md").read_text(encoding="utf-8"),
        (INTELLIGENCE_ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8"),
        (INTELLIGENCE_ROOT / "docs" / "BOUNDARIES.md").read_text(encoding="utf-8"),
        (INTELLIGENCE_ROOT / "docs" / "CONTRACTS.md").read_text(encoding="utf-8"),
        (INTELLIGENCE_ROOT / "docs" / "INTERPRETATION.md").read_text(encoding="utf-8"),
    )


def test_intelligence_docs_name_live_owner_modules_and_analytical_bands() -> None:
    readme, architecture, boundaries, contracts, interpretation = _intelligence_docs()
    combined = "\n".join((readme, architecture, boundaries, contracts, interpretation))

    assert "governance/charter.py" in combined
    assert "candidates/ranking.py" in combined
    assert "posture/evidence.py" in combined
    assert "judgment/paths.py" in combined
    assert "reviews/benchmarks.py" in combined
    assert "learning/adaptation.py" in combined
    assert "judgment/recommendations.py" in combined
    assert "reviews/decision_briefs.py" in combined
    assert "judgment" in combined
    assert "posture" in combined
    assert "interpretation" in combined
    assert "review" in combined
    assert "learning" in combined


def test_intelligence_docs_teach_curated_namespaces_instead_of_symbol_menu_imports() -> (
    None
):
    readme, architecture, boundaries, contracts, interpretation = _intelligence_docs()
    combined = "\n".join((readme, architecture, boundaries, contracts, interpretation))

    assert (
        "from bijux_proteomics_intelligence.candidates.ranking import prioritize_candidates"
        in readme
    )
    assert (
        "from bijux_proteomics_intelligence.interpretation.runs import ("
        in interpretation
    )
    assert (
        "from bijux_proteomics_intelligence import prioritize_candidates"
        not in combined
    )
    assert (
        "from bijux_proteomics_intelligence import build_run_interpretation_summary"
        not in combined
    )
    assert (
        "from bijux_proteomics_intelligence import build_review_board_packet"
        not in combined
    )
