# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import (
    SurprisingDemoConfig,
    SurprisingDemoFindingKind,
    render_surprising_demo_findings_tsv,
    render_surprising_demo_summary_tsv,
    run_surprising_demo,
)


def test_run_surprising_demo_preserves_required_findings_and_outputs(
    tmp_path: Path,
) -> None:
    report = run_surprising_demo(
        SurprisingDemoConfig(output_dir=tmp_path / "surprising_demo_run")
    )

    output_dir = tmp_path / "surprising_demo_run"
    summary_tsv = render_surprising_demo_summary_tsv(report)
    findings_tsv = render_surprising_demo_findings_tsv(report)
    findings = {entry.finding_kind: entry.subject_id for entry in report.findings}

    assert report.summary.within_local_ten_minute_budget is True
    assert report.summary.elapsed_seconds < 600.0
    assert report.summary.strong_protein_count >= 1
    assert report.summary.downgraded_protein_count >= 1
    assert report.summary.ambiguous_ptm_count >= 1
    assert report.summary.qc_issue_count >= 1
    assert report.summary.validation_candidate_count >= 1
    assert findings[SurprisingDemoFindingKind.STRONG_PROTEIN] == "P11111"
    assert findings[SurprisingDemoFindingKind.WEAK_OR_DOWNGRADED_PROTEIN] == "P22222"
    assert findings[SurprisingDemoFindingKind.PTM_AMBIGUITY] == "P11111:S17:Phospho"
    assert findings[SurprisingDemoFindingKind.QC_ISSUE] == "protein:P001"
    assert findings[SurprisingDemoFindingKind.VALIDATION_CANDIDATE] == "protein:P001"
    assert "strong_protein_count" in summary_tsv
    assert "weak_or_downgraded_protein" in findings_tsv
    assert (output_dir / report.artifacts.summary_tsv).exists()
    assert (output_dir / report.artifacts.findings_tsv).exists()
    assert (output_dir / report.artifacts.report_json).exists()
    assert (output_dir / report.artifacts.tmt_output_dir).is_dir()
    assert (output_dir / report.artifacts.ptm_output_dir).is_dir()
    assert (output_dir / report.artifacts.targeted_output_dir).is_dir()
    assert (
        output_dir
        / report.artifacts.tmt_output_dir
        / report.tmt_report.manifest.artifacts.evidence_card_tsv
    ).exists()
    assert (
        output_dir
        / report.artifacts.ptm_output_dir
        / report.ptm_report.manifest.artifacts.excluded_ambiguous_sites_tsv
    ).exists()
    assert (
        output_dir
        / report.artifacts.targeted_output_dir
        / report.targeted_report.manifest.artifacts.assay_qc_unreliable_targets_tsv
    ).exists()
