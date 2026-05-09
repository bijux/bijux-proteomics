from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _read_core_doc(name: str) -> str:
    return (
        REPO_ROOT / "docs" / "04-bijux-proteomics-core" / "foundation" / name
    ).read_text(encoding="utf-8")


def test_benchmark_asset_audit_doc_covers_all_public_roots() -> None:
    text = _read_core_doc("benchmark-asset-audit.md")

    assert "# Benchmark Asset Audit" in text
    assert "outsider-findable raw source" in text
    assert "primary flagship package" in text
    assert "companion generalization package" in text
    assert "dda_reviewable_run" in text
    assert "targeted_carryover_review_package" in text
    assert "workflow_generalization_assets refresh" in text
    assert "flagship_asset_maintenance refresh" in text


def test_family_lineage_docs_and_core_indexes_link_to_audit_surfaces() -> None:
    dda = _read_core_doc("dda-benchmark-lineage.md")
    multiplex = _read_core_doc("multiplex-benchmark-lineage.md")
    licensing = _read_core_doc("benchmark-licensing-and-redistribution.md")
    incompleteness = _read_core_doc("benchmark-incompleteness-ledger.md")
    foundation_index = _read_core_doc("index.md")
    asset_handbook = _read_core_doc("flagship-benchmark-assets.md")

    assert "# DDA Benchmark Lineage" in dda
    assert "cross_package_generalization.json" in dda
    assert "primary flagship package" in dda
    assert "# Multiplex Benchmark Lineage" in multiplex
    assert "companion generalization package" in multiplex
    assert "# Benchmark Licensing and Redistribution" in licensing
    assert "redistributes as governed evidence" in licensing
    assert "dataset reuse note" in licensing
    assert "# Benchmark Incompleteness Ledger" in incompleteness
    assert "Non-transfer zones" in incompleteness
    assert "Expected failure conditions" in incompleteness
    assert "Benchmark Asset Audit" in foundation_index
    assert "Benchmark Licensing and Redistribution" in foundation_index
    assert "Benchmark Incompleteness Ledger" in foundation_index
    assert "DDA Benchmark Lineage" in foundation_index
    assert "Targeted Benchmark Lineage" in foundation_index
    assert "Benchmark Asset Audit" in asset_handbook
    assert "Benchmark Licensing and Redistribution" in asset_handbook
    assert "Benchmark Incompleteness Ledger" in asset_handbook
    assert "Multiplex Benchmark Lineage" in asset_handbook
