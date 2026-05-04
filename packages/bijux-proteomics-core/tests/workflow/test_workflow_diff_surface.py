# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.workflow.reproducibility import (
    WorkflowRunDiffCategory,
    WorkflowRunSnapshot,
    build_workflow_run_diff_report,
)


def test_build_workflow_run_diff_report_captures_quant_qc_and_lab_changes() -> None:
    baseline = WorkflowRunSnapshot(
        run_id="run-001",
        study_id="study-a",
        sample_id="sample-01",
        input_fingerprint="a" * 16,
        engine_fingerprint="b" * 16,
        parameter_fingerprint="c" * 16,
        confidence_fingerprint="d" * 16,
        quant_fingerprint="e" * 16,
        qc_fingerprint="f" * 16,
        evidence_fingerprint="1" * 16,
        lab_handoff_fingerprint="2" * 16,
    )
    candidate = WorkflowRunSnapshot(
        run_id="run-002",
        study_id="study-a",
        sample_id="sample-01",
        input_fingerprint="a" * 16,
        engine_fingerprint="b" * 16,
        parameter_fingerprint="9" * 16,
        confidence_fingerprint="d" * 16,
        quant_fingerprint="8" * 16,
        qc_fingerprint="7" * 16,
        evidence_fingerprint="1" * 16,
        lab_handoff_fingerprint="3" * 16,
    )

    report = build_workflow_run_diff_report(baseline, candidate)

    assert report.same_study is True
    assert report.same_sample is True
    categories = {entry.category for entry in report.entries}
    assert WorkflowRunDiffCategory.PARAMETER in categories
    assert WorkflowRunDiffCategory.QUANT in categories
    assert WorkflowRunDiffCategory.QC in categories
    assert WorkflowRunDiffCategory.LAB_CONSEQUENCE in categories
