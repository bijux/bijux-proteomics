from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _read_runtime_doc(name: str) -> str:
    return (REPO_ROOT / "docs" / "09-bijux-proteomics-runtime" / name).read_text(
        encoding="utf-8"
    )


def test_runtime_benchmark_rerun_docs_name_primary_and_companion_paths() -> None:
    kits = _read_runtime_doc("benchmark-rerun-kits.md")
    comparability = _read_runtime_doc("benchmark-comparability-matrix.md")

    assert "# Benchmark Rerun Kits" in kits
    assert "primary runtime entrypoint" in kits
    assert "companion runtime entrypoint" in kits
    assert "not published for this family" in kits
    assert "dda_reviewable_run" in kits
    assert "multiplex_channel_stress_review_package" in kits
    assert "# Benchmark Comparability Matrix" in comparability
    assert "stability score" in comparability
    assert "cross_package_generalization.json" in comparability
    assert "collapsed claims" in comparability


def test_runtime_index_links_to_rerun_and_comparability_surfaces() -> None:
    text = _read_runtime_doc("index.md")

    assert "Benchmark Rerun Kits" in text
    assert "Benchmark Comparability Matrix" in text
