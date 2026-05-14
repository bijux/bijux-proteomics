# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import (
    PsmRecord,
    TargetDecoyLabel,
    build_evidence_level_fdr_review_report,
    render_evidence_level_fdr_entries_tsv,
    render_evidence_level_fdr_summary_tsv,
)


def _review_records() -> tuple[PsmRecord, ...]:
    return (
        PsmRecord(
            spectrum_id="scan=1001",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            charge=2,
            score=100.0,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=1002",
            peptide="AKTIDEK",
            canonical_peptide="AKTIDEK",
            charge=2,
            score=95.0,
            protein_refs=("CON__KERATIN_HUMAN",),
            target_decoy_label=TargetDecoyLabel.TARGET,
            contaminant_flag=True,
        ),
        PsmRecord(
            spectrum_id="scan=1003",
            peptide="DECOYPEP",
            canonical_peptide="DECOYPEP",
            charge=2,
            score=90.0,
            protein_refs=("DECOY_P99999",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
    )


def test_evidence_level_fdr_review_reports_level_counts_at_standard_thresholds() -> (
    None
):
    report = build_evidence_level_fdr_review_report(_review_records())

    assert report.thresholds == (0.01, 0.05, 0.1)
    assert len(report.summaries) == 9
    summary_index = {
        (summary.threshold, summary.evidence_level.value): summary
        for summary in report.summaries
    }
    psm_at_one_percent = summary_index[(0.01, "psm")]
    assert psm_at_one_percent.total_count == 3
    assert psm_at_one_percent.total_target_count == 2
    assert psm_at_one_percent.total_decoy_count == 1
    assert psm_at_one_percent.total_contaminant_count == 1
    assert psm_at_one_percent.accepted_count == 2
    assert psm_at_one_percent.accepted_target_count == 2
    assert psm_at_one_percent.accepted_decoy_count == 0
    assert psm_at_one_percent.accepted_contaminant_count == 1
    peptide_at_five_percent = summary_index[(0.05, "peptide")]
    assert peptide_at_five_percent.accepted_count == 2
    protein_at_ten_percent = summary_index[(0.1, "protein")]
    assert protein_at_ten_percent.accepted_count == 2


def test_evidence_level_fdr_review_renders_summary_and_accepted_entry_ledgers() -> None:
    report = build_evidence_level_fdr_review_report(_review_records())

    summary_tsv = render_evidence_level_fdr_summary_tsv(report)
    entries_tsv = render_evidence_level_fdr_entries_tsv(report)

    assert summary_tsv.startswith(
        "threshold\tevidence_level\ttotal_count\ttotal_target_count"
    )
    assert "0.01\tpsm\t3\t2\t1\t0\t0\t1\t2\t2\t0\t0\t0\t1" in summary_tsv
    assert entries_tsv.startswith(
        "threshold\tevidence_level\tentity_id\trank\tscore\tq_value"
    )
    assert (
        "0.05\tprotein\tCON__KERATIN_HUMAN\t2\t95.0\t0.0\ttarget\ttrue\t1\tCON__KERATIN_HUMAN"
        in entries_tsv
    )
