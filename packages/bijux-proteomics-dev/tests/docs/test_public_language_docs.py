from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_public_language_glossary_doc_names_allowed_and_retired_terms() -> None:
    text = (
        REPO_ROOT
        / "docs"
        / "01-bijux-proteomics"
        / "foundation"
        / "public-language-glossary.md"
    ).read_text(encoding="utf-8")

    assert "# Public Language Glossary" in text
    assert "`workflow authority matrix`" in text
    assert "`canonical workflow`" in text
    assert "`reviewable-proteomics`" in text
    assert "`decision brief`" in text
    assert "validate_public_language()" in text
