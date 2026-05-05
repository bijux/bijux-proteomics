from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
INTELLIGENCE_ROOT = REPO_ROOT / "packages" / "bijux-proteomics-intelligence"


def _combined_docs() -> str:
    parts = [
        (INTELLIGENCE_ROOT / "README.md").read_text(encoding="utf-8"),
        (INTELLIGENCE_ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8"),
        (INTELLIGENCE_ROOT / "docs" / "BOUNDARIES.md").read_text(encoding="utf-8"),
        (INTELLIGENCE_ROOT / "docs" / "CONTRACTS.md").read_text(encoding="utf-8"),
        (INTELLIGENCE_ROOT / "docs" / "INTERPRETATION.md").read_text(
            encoding="utf-8"
        ),
    ]
    return "\n".join(parts)


def test_intelligence_docs_keep_refusal_and_downgrade_boundaries_explicit() -> None:
    text = _combined_docs()

    assert "must refuse or downgrade" in text
    assert "does not own scientific truth" in text
    assert "does not own runtime transport" in text
    assert "does not own laboratory scheduling" in text
    assert "cautious interpretation" in text
    assert "unresolved questions visible" in text


def test_intelligence_docs_reject_analytical_depth_overclaim() -> None:
    text = _combined_docs().lower()

    banned_claims = (
        "fully automated progression approval",
        "authoritative scientific truth",
        "causal proof from descriptive enrichment",
        "replaces bijux-proteomics-core",
        "owns lab scheduling authority",
        "owns runtime execution authority",
    )

    for claim in banned_claims:
        assert claim not in text
