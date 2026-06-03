# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification.protein_target_decoy_fdr import (
    build_protein_target_decoy_fdr_report,
    render_protein_target_decoy_fdr_summary_tsv,
    render_protein_target_decoy_fdr_tsv,
)


def _higher_better_records() -> tuple[PsmRecord, ...]:
    return (
        PsmRecord(
            spectrum_id="scan=1001",
            peptide="PEPA",
            canonical_peptide="PEPA",
            charge=2,
            score=100.0,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=1002",
            peptide="SHAREDK",
            canonical_peptide="SHAREDK",
            charge=2,
            score=95.0,
            protein_refs=("P11111", "P22222"),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=1003",
            peptide="TARGETK",
            canonical_peptide="TARGETK",
            charge=2,
            score=90.0,
            protein_refs=("P33333",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=1004",
            peptide="DECOYPEP",
            canonical_peptide="DECOYPEP",
            charge=2,
            score=85.0,
            protein_refs=("DECOY_P11111",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
    )


def test_protein_target_decoy_fdr_report_uses_protein_entities_not_psm_counts() -> None:
    report = build_protein_target_decoy_fdr_report(
        _higher_better_records(),
        threshold=0.5,
    )

    assert report.summary.total_protein_count == 4
    assert report.summary.target_protein_count == 3
    assert report.summary.decoy_protein_count == 1
    assert report.summary.q_values_monotonic is True
    assert [entry.evidence.protein_ref for entry in report.entries] == [
        "P11111",
        "P22222",
        "P33333",
        "DECOY_P11111",
    ]
    assert [entry.cumulative_targets for entry in report.entries] == [1, 2, 3, 3]
    assert [entry.cumulative_decoys for entry in report.entries] == [0, 0, 0, 1]
    assert [entry.raw_fdr for entry in report.entries] == [0.0, 0.0, 0.0, 1 / 3]
    assert [entry.q_value for entry in report.entries] == [0.0, 0.0, 0.0, 1 / 3]


def test_combined_evidence_policy_uses_peptide_support_to_break_score_ties() -> None:
    records = (
        PsmRecord(
            spectrum_id="scan=2001",
            peptide="PEPA",
            canonical_peptide="PEPA",
            charge=2,
            score=50.0,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=2002",
            peptide="PEPB",
            canonical_peptide="PEPB",
            charge=2,
            score=50.0,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=2003",
            peptide="PEPC",
            canonical_peptide="PEPC",
            charge=2,
            score=50.0,
            protein_refs=("P22222",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
    )

    report = build_protein_target_decoy_fdr_report(
        records,
        evidence_policy="combined_evidence",
    )

    assert [entry.evidence.protein_ref for entry in report.entries] == [
        "P11111",
        "P22222",
    ]
    assert report.entries[0].evidence.peptide_count == 2
    assert report.entries[1].evidence.peptide_count == 1


def test_protein_target_decoy_fdr_renderers_emit_stable_ledgers() -> None:
    report = build_protein_target_decoy_fdr_report(
        _higher_better_records(),
        threshold=0.5,
    )

    summary_tsv = render_protein_target_decoy_fdr_summary_tsv(report)
    entries_tsv = render_protein_target_decoy_fdr_tsv(report)

    assert summary_tsv.startswith(
        "score_orientation\tevidence_policy\tthreshold\ttotal_protein_count"
    )
    assert "reproducibility_hash" in summary_tsv
    assert entries_tsv.startswith(
        "rank\ttie_group_rank\ttie_group_size\tprotein_ref\tbest_score"
    )
    assert "P11111\t100.0" in entries_tsv
