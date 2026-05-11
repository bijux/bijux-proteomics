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
        / "flagship-benchmark-assets.md"
    ).read_text(encoding="utf-8")


def test_flagship_benchmark_assets_doc_names_product_owned_asset_root() -> None:
    text = _read_doc()

    assert "# Flagship Benchmark Assets" in text
    assert "benchmark-assets/flagship-public-packages" in text
    assert "asset_root_contract.json" in text
    assert "freshness_report.json" in text
    assert "obsolescence_audit.json" in text
    assert "Benchmark Freshness Review" in text


def test_flagship_benchmark_assets_doc_names_refresh_command_and_per_package_support_files() -> (
    None
):
    text = _read_doc()

    assert "flagship_asset_maintenance refresh" in text
    assert "source_locator_manifest.json" in text
    assert "citation_manifest.json" in text
    assert "generated_boundary.json" in text
    assert "rebuild_instructions.md" in text


def test_foundation_index_links_to_benchmark_freshness_review() -> None:
    text = (
        REPO_ROOT / "docs" / "04-bijux-proteomics-core" / "foundation" / "index.md"
    ).read_text(encoding="utf-8")

    assert "Benchmark Freshness Review" in text
    assert "benchmark-freshness-review" in text
