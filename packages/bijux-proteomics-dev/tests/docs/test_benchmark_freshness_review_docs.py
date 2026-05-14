from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_benchmark_freshness_review_doc_names_release_floor_and_evidence() -> None:
    text = (
        REPO_ROOT
        / "docs"
        / "04-bijux-proteomics-core"
        / "foundation"
        / "benchmark-freshness-review.md"
    ).read_text(encoding="utf-8")

    assert "# Benchmark Freshness Review" in text
    assert "release language floor" in text
    assert "freshness_report.json" in text
    assert "obsolescence_audit.json" in text
    assert "recorded_available" in text
