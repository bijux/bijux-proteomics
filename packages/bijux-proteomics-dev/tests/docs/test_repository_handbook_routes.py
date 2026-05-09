from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_repository_handbook_routes_product_owners_and_reader_intent() -> None:
    handbook = (
        REPO_ROOT / "docs" / "01-bijux-proteomics" / "index.md"
    ).read_text(encoding="utf-8")

    assert "Product Architecture" in handbook
    assert "Cross-Package Ownership" in handbook
    assert "Release Readiness Matrix" in handbook
    assert "## Reader Routes" in handbook
    assert "Scientist:" in handbook
    assert "Operator:" in handbook
    assert "Maintainer:" in handbook
