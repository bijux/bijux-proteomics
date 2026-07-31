from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_root_readme_front_loads_scope_limits_and_reader_paths() -> None:
    readme = _read("README.md")

    assert "## Product Scope" in readme
    assert "## Current Credible Workflow Families" in readme
    assert "## Forbidden Claims" in readme
    assert "## Reader Paths" in readme
    assert readme.index("## Forbidden Claims") < readme.index(
        "<!-- bijux-proteomics-badges:generated:start -->"
    )
    assert readme.index(
        "<!-- bijux-proteomics-badges:generated:end -->"
    ) < readme.index("## Reader Paths")
    assert "Scientist: start with" in readme
    assert "Operator: start with the" in readme
    assert "Maintainer: start with" in readme
    assert "Public artifact index" in readme


def test_docs_home_routes_scientist_operator_and_maintainer_in_one_hop() -> None:
    docs_home = _read("docs/index.md")

    assert "## Product Scope" in docs_home
    assert "## Current Credible Workflow Families" in docs_home
    assert "## Forbidden Claims" in docs_home
    assert "## Reader Paths" in docs_home
    assert "## Reader-First Sections" in docs_home
    assert (
        "Product Overview" in docs_home
        and "Product Architecture" in docs_home
        and "Cross-Package Ownership" in docs_home
    )
    assert "Scientist:" in docs_home
    assert "Operator:" in docs_home
    assert "Maintainer:" in docs_home
    assert "Scientist Journey" in docs_home
    assert "Operator Rerun Journey" in docs_home
    assert "Maintainer Safe Change" in docs_home
    assert "Workflow Families" in docs_home
    assert "Decision Support" in docs_home


def test_docs_home_places_badges_after_product_introduction() -> None:
    docs_home = _read("docs/index.md")

    introduction_start = docs_home.index("# Bijux Proteomics")
    badges_start = docs_home.index("<!-- bijux-proteomics-badges:generated:start -->")
    first_section = docs_home.index("## Product Scope")

    assert introduction_start < badges_start < first_section
    assert "## " not in docs_home[introduction_start:badges_start]
