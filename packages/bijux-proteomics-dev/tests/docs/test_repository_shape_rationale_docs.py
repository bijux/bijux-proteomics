from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_repository_shape_rationale_names_durable_splits_and_temporary_compat() -> None:
    text = _read("docs/01-bijux-proteomics/foundation/repository-shape-rationale.md")

    assert "# Repository Shape Rationale" in text
    assert "## Durable Splits" in text
    assert "## Temporary Compatibility Split" in text
    assert "## Candidate Future Merges" in text
    assert "`agentic-proteins` is not a seventh product owner" in text
    assert "`bijux-proteomics-foundation`" in text
    assert "`bijux-proteomics-core`" in text
    assert "`bijux-proteomics-runtime`" in text
    assert "`bijux-proteomics-knowledge`" in text
    assert "`bijux-proteomics-intelligence`" in text
    assert "`bijux-proteomics-lab`" in text


def test_dda_cross_package_handbook_routes_all_six_product_packages() -> None:
    text = _read("docs/01-bijux-proteomics/foundation/dda-cross-package-handbook.md")

    assert "# DDA Cross-Package Handbook" in text
    for package_name in (
        "`bijux-proteomics-foundation`",
        "`bijux-proteomics-core`",
        "`bijux-proteomics-runtime`",
        "`bijux-proteomics-knowledge`",
        "`bijux-proteomics-intelligence`",
        "`bijux-proteomics-lab`",
    ):
        assert package_name in text
    assert "import_only" in text
    assert "Why Trust DDA" in text
    assert "Repository Shape Rationale" in text
