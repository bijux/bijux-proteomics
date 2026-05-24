# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import build_public_benchmark_trust_bundle


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_build_public_benchmark_trust_bundle_preserves_generated_assets(
    tmp_path: Path,
) -> None:
    report = build_public_benchmark_trust_bundle(
        _repo_root() / "benchmarks" / "public",
        output_dir=tmp_path / "trust_bundle",
    )

    output_dir = Path(report.output_dir)
    assert report.suite_report.passed_count == 5
    assert report.suite_report.failed_count == 5
    assert (output_dir / "benchmark_results" / "summary.tsv").exists()
    assert (output_dir / "benchmark_results" / "failures.tsv").exists()
    assert (output_dir / "benchmark_results" / "source_audits.tsv").exists()
    assert (output_dir / "benchmark_results" / "verified_counts.tsv").exists()
    assert (output_dir / "rejected_evidence" / "index.tsv").exists()
    assert (output_dir / "qc_failures" / "index.tsv").exists()
    assert (output_dir / "cards" / "index.tsv").exists()
    assert (output_dir / "comparison_tables" / "index.tsv").exists()
    assert (output_dir / "trust_bundle_manifest.json").exists()
    assert Path(report.html_index_path).exists()

    cards_index = (output_dir / "cards" / "index.tsv").read_text(encoding="utf-8")
    assert "lfq_cohort_review_package" in cards_index
    assert "protein_cards.tsv" in cards_index or "protein_card" in cards_index

    benchmark_summary = (output_dir / "benchmark_results" / "summary.tsv").read_text(
        encoding="utf-8"
    )
    assert "dia_diann_benchmark_dataset" in benchmark_summary
    assert "fragpipe_msfragger_benchmark_dataset" in benchmark_summary
    assert "maxquant_lfq_benchmark_dataset" in benchmark_summary
    assert "ptm_localization_review_package" in benchmark_summary
    assert "lfq_cohort_review_package" in benchmark_summary

    html_index = Path(report.html_index_path).read_text(encoding="utf-8")
    assert "Proteomics Trust Bundle" in html_index
    assert "workflow outputs" in html_index
