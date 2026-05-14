from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics_dev.release.governance.public_language import (
    PUBLIC_LANGUAGE_GLOSSARY_PATH,
    build_public_language_glossary,
    run,
    validate_public_language,
)

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_public_language_glossary_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_public_language_real_repo_has_no_retired_terms_left() -> None:
    assert validate_public_language(REPO_ROOT) == ()


def test_public_language_flags_retired_phrase(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = tmp_path
    (repo_root / "docs" / "01-bijux-proteomics" / "foundation").mkdir(parents=True)
    (
        repo_root
        / "packages"
        / "bijux-proteomics-runtime"
        / "src"
        / "bijux_proteomics_runtime"
        / "api"
        / "routes"
    ).mkdir(parents=True)
    (
        repo_root / "docs" / "08-bijux-proteomics-maintain" / "bijux-proteomics-dev"
    ).mkdir(parents=True)
    (repo_root / "packages" / "bijux-proteomics-foundation").mkdir(parents=True)
    (repo_root / "README.md").write_text("canonical workflow\n", encoding="utf-8")
    (repo_root / "docs" / "index.md").write_text("", encoding="utf-8")
    (
        repo_root
        / "docs"
        / "08-bijux-proteomics-maintain"
        / "bijux-proteomics-dev"
        / "release-support.md"
    ).write_text("", encoding="utf-8")
    (
        repo_root
        / "packages"
        / "bijux-proteomics-runtime"
        / "src"
        / "bijux_proteomics_runtime"
        / "api"
        / "routes"
        / "decision_briefs.py"
    ).write_text("", encoding="utf-8")
    (repo_root / "packages" / "bijux-proteomics-foundation" / "README.md").write_text(
        "", encoding="utf-8"
    )
    (
        repo_root
        / "docs"
        / "01-bijux-proteomics"
        / "foundation"
        / PUBLIC_LANGUAGE_GLOSSARY_PATH.name
    ).write_text("", encoding="utf-8")

    issues = validate_public_language(repo_root)

    assert any(issue.code == "retired-public-language" for issue in issues)


def test_public_language_glossary_declares_review_packet_as_route_contract() -> None:
    glossary = build_public_language_glossary()

    review_packet_term = next(
        term for term in glossary.allowed_terms if term.term == "decision brief"
    )
    assert review_packet_term.allowed_surfaces == (
        "packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/api/routes/decision_briefs.py",
    )
