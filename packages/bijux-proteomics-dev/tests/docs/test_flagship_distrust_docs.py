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
        / "01-bijux-proteomics"
        / "foundation"
        / name
    ).read_text(encoding="utf-8")


def test_flagship_distrust_pages_exist_for_incomplete_workflows() -> None:
    expected_files = (
        "why-not-trust-lfq-yet.md",
        "why-not-trust-ptm-yet.md",
        "why-not-trust-targeted-yet.md",
    )
    for name in expected_files:
        text = _read_doc(name)
        assert "# Why Not Trust" in text
        assert "Current Blockers" in text
        assert "What Would Need To Change" in text


def test_distrust_pages_name_real_missing_substance() -> None:
    lfq = _read_doc("why-not-trust-lfq-yet.md")
    ptm = _read_doc("why-not-trust-ptm-yet.md")
    targeted = _read_doc("why-not-trust-targeted-yet.md")

    assert "lfq-cohort-review-corpus" in lfq
    assert "public package" in lfq
    assert "ptm-localization-review-corpus" in ptm
    assert "public comparator-backed claim support is still refused" in ptm
    assert "targeted-transition-review-corpus" in targeted
    assert "operational burden remains too high for a justified recommendation" in targeted
