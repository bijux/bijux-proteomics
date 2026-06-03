# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics.workflow import (
    build_flagship_trust_bundle_descriptors,
    build_public_benchmark_trust_bundle,
    build_trust_bundle,
    public_benchmark_root,
)


@pytest.mark.slow
def test_build_public_benchmark_trust_bundle_preserves_generated_assets(
    tmp_path: Path,
) -> None:
    report = build_public_benchmark_trust_bundle(
        public_benchmark_root(),
        output_dir=tmp_path / "trust_bundle",
    )

    output_dir = Path(report.output_dir)
    assert report.suite_report.passed_count == 8
    assert report.suite_report.failed_count == 3
    assert (output_dir / "benchmark_results" / "summary.tsv").exists()
    assert (output_dir / "benchmark_results" / "failures.tsv").exists()
    assert (output_dir / "benchmark_results" / "source_audits.tsv").exists()
    assert (output_dir / "benchmark_results" / "verified_counts.tsv").exists()
    assert (output_dir / "evidence_graphs" / "index.tsv").exists()
    assert (output_dir / "rejected_evidence" / "index.tsv").exists()
    assert (output_dir / "qc_failures" / "index.tsv").exists()
    assert (output_dir / "cards" / "index.tsv").exists()
    assert (output_dir / "comparison_tables" / "index.tsv").exists()
    assert (output_dir / "trust_bundle_manifest.json").exists()
    assert Path(report.html_index_path).exists()
    assert (
        output_dir
        / "benchmark_results"
        / "weak_evidence"
        / "flagship_weak_evidence_benchmark"
        / "summary.tsv"
    ).exists()
    assert (
        output_dir
        / "benchmark_results"
        / "weak_evidence"
        / "flagship_weak_evidence_benchmark"
        / "criteria.tsv"
    ).exists()
    assert report.handwritten_result_table_count == 0
    assert report.descriptor_count == 12

    cards_index = (output_dir / "cards" / "index.tsv").read_text(encoding="utf-8")
    assert "lfq_cohort_review_package" in cards_index
    assert "protein_cards.tsv" in cards_index or "protein_card" in cards_index

    evidence_graph_index = (output_dir / "evidence_graphs" / "index.tsv").read_text(
        encoding="utf-8"
    )
    assert "biological_evidence_graph_nodes.tsv" in evidence_graph_index
    assert "biological_evidence_graph_edges.tsv" in evidence_graph_index

    benchmark_summary = (output_dir / "benchmark_results" / "summary.tsv").read_text(
        encoding="utf-8"
    )
    assert "dia_diann_benchmark_dataset" in benchmark_summary
    assert "fragpipe_msfragger_benchmark_dataset" in benchmark_summary
    assert "maxquant_lfq_benchmark_dataset" in benchmark_summary
    assert "multiplex_tmtpro_review_package" in benchmark_summary
    assert "ptm_localization_review_package" in benchmark_summary
    assert "lfq_cohort_review_package" in benchmark_summary
    assert "lfq_sparse_contrast_benchmark_dataset" in benchmark_summary
    assert "targeted_transition_review_package" in benchmark_summary

    weak_summary = (
        output_dir
        / "benchmark_results"
        / "weak_evidence"
        / "flagship_weak_evidence_benchmark"
        / "summary.tsv"
    ).read_text(encoding="utf-8")
    assert "flagship_weak_evidence_benchmark" in weak_summary
    assert "downgraded_protein_count" in weak_summary
    assert not list(output_dir.rglob("skyline_targeted_qc_results.tsv"))
    assert not list(output_dir.rglob("targeted_benchmark_qc.tsv"))

    html_index = Path(report.html_index_path).read_text(encoding="utf-8")
    assert "Proteomics Trust Bundle" in html_index
    assert "Evidence Graphs" in html_index
    assert "workflow outputs" in html_index


@pytest.mark.slow
def test_build_trust_bundle_uses_explicit_descriptor_set(
    tmp_path: Path,
) -> None:
    report = build_trust_bundle(
        build_flagship_trust_bundle_descriptors(
            tmp_path / "descriptor_bound_trust_bundle"
        ),
        tmp_path / "descriptor_bound_trust_bundle",
    )

    assert report.descriptor_count == 12
    assert any(
        run.dataset_id == "flagship_weak_evidence_benchmark" for run in report.runs
    )
