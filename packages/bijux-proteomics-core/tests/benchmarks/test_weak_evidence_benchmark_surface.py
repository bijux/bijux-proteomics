# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.benchmarks import (
    WeakEvidenceBenchmarkStatus,
    build_flagship_weak_evidence_benchmark_descriptor,
    render_weak_evidence_benchmark_criteria_tsv,
    render_weak_evidence_benchmark_summary_tsv,
    run_weak_evidence_benchmark,
)
from bijux_proteomics.study.qc_benchmarks import QcPromotionBlockObservation


def _multiplex_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def _write_positive_tmt_fixture(path: Path) -> None:
    path.write_text(
        "\n".join(
            (
                "id\tModified sequence\tLeading proteins\tExperiment\tIsolation interference [%]\tReporter intensity corrected 126\tReporter intensity corrected 127N\tReporter intensity corrected 128N",
                "1\tPEPTIDE\tP001\tplex-a\t4\t1200\t2400\t6000",
                "2\tDPEPTIDE\tP001\tplex-a\t6\t1000\t2000\t6100",
                "3\tPEPTIDE\tP001\tplex-b\t5\t1300\t2600\t6200",
                "4\tDPEPTIDE\tP001\tplex-b\t7\t1050\t2100\t6000",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def test_run_weak_evidence_benchmark_demonstrates_required_negative_surfaces(
    tmp_path: Path,
) -> None:
    report = run_weak_evidence_benchmark(
        build_flagship_weak_evidence_benchmark_descriptor(tmp_path / "weak_evidence")
    )

    criteria_tsv = render_weak_evidence_benchmark_criteria_tsv(report)
    summary_tsv = render_weak_evidence_benchmark_summary_tsv(report)

    assert report.summary.status is WeakEvidenceBenchmarkStatus.PASSED
    assert report.output_root == tmp_path / "weak_evidence"
    assert report.summary.failed_qc_block_count >= 1
    assert report.summary.refused_claim_count >= 1
    assert report.summary.downgraded_protein_count >= 1
    assert report.summary.ambiguous_ptm_count >= 1
    assert report.summary.invalid_or_blocked_contrast_count >= 1
    assert not report.summary.all_outputs_positive_or_accepted
    assert all(criterion.observed for criterion in report.criteria)
    assert report.lfq_sparse_report is not None
    assert report.lfq_sparse_report.status == "passed"
    assert report.ptm_report is not None
    assert report.ptm_report.status == "passed"
    assert report.tmt_report is not None
    assert report.tmt_report.summary.downgraded_protein_count >= 1
    assert "refused_claim" in criteria_tsv
    assert "ambiguous_ptm" in criteria_tsv
    assert "invalid_or_blocked_contrast" in criteria_tsv
    assert "refused_claim_count\t" in summary_tsv
    assert "all_outputs_positive_or_accepted\tfalse" in summary_tsv


def test_run_weak_evidence_benchmark_fails_when_all_evaluated_outputs_are_positive(
    tmp_path: Path,
) -> None:
    positive_tmt = tmp_path / "positive_tmt.tsv"
    _write_positive_tmt_fixture(positive_tmt)
    report = run_weak_evidence_benchmark(
        build_flagship_weak_evidence_benchmark_descriptor(
            tmp_path / "positive_only_run"
        ).model_copy(
            update={
                "lfq_sparse_descriptor_path": None,
                "ptm_descriptor_path": None,
                "tmt_result_tsv_path": positive_tmt,
                "tmt_design_tsv_path": _multiplex_fixture("tmt.design.tsv"),
                "qc_promotion_observations": (
                    QcPromotionBlockObservation(
                        run_id="run_clean_qc_only",
                        failed_qc=False,
                        attempted_decision_promotion=True,
                        promotion_prevented=False,
                        blocking_reason="qc_clean_decision_allowed",
                    ),
                ),
            }
        )
    )

    assert report.summary.status is WeakEvidenceBenchmarkStatus.FAILED
    assert report.output_root == tmp_path / "positive_only_run"
    assert report.summary.all_outputs_positive_or_accepted
    assert report.summary.observed_negative_surface_count == 0
    assert report.summary.downgraded_protein_count == 0
    assert report.summary.failed_qc_block_count == 0
    assert any(not criterion.observed for criterion in report.criteria)
