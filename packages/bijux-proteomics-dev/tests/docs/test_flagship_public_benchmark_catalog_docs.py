from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _read_doc() -> str:
    return (
        REPO_ROOT
        / "docs"
        / "04-bijux-proteomics-core"
        / "foundation"
        / "flagship-public-benchmark-catalog.md"
    ).read_text(encoding="utf-8")


def test_flagship_public_benchmark_catalog_doc_lists_all_six_workflow_families() -> None:
    text = _read_doc()

    assert "# Flagship Public Benchmark Catalog" in text
    for workflow_family in ("dda", "dia", "lfq", "multiplex", "ptm", "targeted"):
        assert f"`{workflow_family}`" in text


def test_flagship_public_benchmark_catalog_doc_names_machine_readable_package_surfaces() -> None:
    text = _read_doc()

    assert "artifact inventory" in text
    assert "quality posture" in text
    assert "lifecycle posture" in text
    assert "benchmark-assets/flagship-public-packages" in text
    assert "family-transfer report" in text
    assert "companion package root" in text


def test_flagship_public_benchmark_catalog_doc_points_to_asset_root_handbook() -> None:
    text = _read_doc()

    assert "Flagship Benchmark Assets" in text


def test_flagship_public_benchmark_catalog_doc_keeps_multiplex_internal_support_explicit() -> None:
    text = _read_doc()

    assert "internal-support family" in text
    assert "collapses outsider-facing trust" in text
