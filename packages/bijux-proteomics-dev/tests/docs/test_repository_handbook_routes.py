from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_repository_handbook_routes_product_owners_and_reader_intent() -> None:
    handbook = (REPO_ROOT / "docs" / "01-bijux-proteomics" / "index.md").read_text(
        encoding="utf-8"
    )

    assert "## Resolve The Governing Authority" in handbook
    assert "Product Architecture" in handbook
    assert "Cross-Package Ownership" in handbook
    assert "Repository Shape Rationale" in handbook
    assert "Release Readiness Matrix" in handbook
    assert "## Continue By Objective" in handbook
    assert "## Shared Reader Routes" not in handbook
    assert "## Reader Routes" not in handbook
    assert "Product Overview" in handbook
    assert "Workflow Families" in handbook
    assert "Maintenance" in handbook
    assert "Scientist Journey" in handbook
    assert "Operator Rerun Journey" in handbook
    assert "Maintainer Safe Change" in handbook
