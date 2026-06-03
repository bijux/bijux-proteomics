# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import (
    ProteomicsStudyConclusionKind,
    WeakEvidenceReportSectionKey,
    build_flagship_weak_evidence_benchmark_descriptor,
    run_weak_evidence_benchmark,
)


def test_run_weak_evidence_benchmark_preserves_refused_claim_section(
    tmp_path: Path,
) -> None:
    report = run_weak_evidence_benchmark(
        build_flagship_weak_evidence_benchmark_descriptor(tmp_path / "weak_evidence")
    )

    assert report.summary.refused_claim_count >= 1
    assert report.refused_claims
    assert report.lfq_sparse_study_result is not None
    assert any(
        entry.kind is ProteomicsStudyConclusionKind.REFUSED_CLAIM
        for entry in report.lfq_sparse_study_result.biological_conclusions
    )
    assert report.sections[0].section_key is WeakEvidenceReportSectionKey.REFUSED_CLAIMS
    assert report.sections[0].claim_ids == tuple(
        entry.claim_id for entry in report.refused_claims
    )
    assert any(
        "low_robustness" in entry.reason_codes
        or "weak_evidence_tier" in entry.reason_codes
        for entry in report.refused_claims
    )
