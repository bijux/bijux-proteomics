# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification.protein_grouping import (
    build_protein_grouping_report,
    render_protein_grouping_entries_tsv,
    render_protein_grouping_summary_tsv,
)


def _grouping_records() -> tuple[PsmRecord, ...]:
    return (
        PsmRecord(
            spectrum_id="scan=5001",
            peptide="PEPTIDEK",
            canonical_peptide="PEPTIDEK",
            charge=2,
            score=110.0,
            q_value=0.01,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=5002",
            peptide="SHAREDK",
            canonical_peptide="SHAREDK",
            charge=2,
            score=100.0,
            q_value=0.02,
            protein_refs=("P11111", "P22222", "P44444"),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=5003",
            peptide="GLYGLYK",
            canonical_peptide="GLYGLYK",
            charge=2,
            score=95.0,
            q_value=0.03,
            protein_refs=("P22222", "P44444"),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=5004",
            peptide="ALTPEPTIDE",
            canonical_peptide="ALTPEPTIDE",
            charge=2,
            score=90.0,
            q_value=0.04,
            protein_refs=("P33333",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
    )


def test_protein_grouping_report_keeps_indistinguishable_members_together() -> None:
    report = build_protein_grouping_report(_grouping_records())

    assert report.summary.total_groups == 3
    assert report.summary.ambiguous_group_count == 1
    ambiguous = next(
        group for group in report.groups if group.protein_refs == ("P22222", "P44444")
    )

    assert ambiguous.leading_protein == "P22222"
    assert ambiguous.leading_rationale == "lexicographic_tiebreak"
    assert ambiguous.unique_peptides == ()
    assert ambiguous.shared_peptides == ("GLYGLYK", "SHAREDK")
    assert ambiguous.peptides == ("GLYGLYK", "SHAREDK")


def test_protein_grouping_report_tracks_unique_and_shared_peptide_ledgers() -> None:
    report = build_protein_grouping_report(_grouping_records())

    p11111 = next(group for group in report.groups if group.leading_protein == "P11111")

    assert p11111.unique_peptides == ("PEPTIDEK",)
    assert p11111.shared_peptides == ("SHAREDK",)
    assert p11111.best_score == 110.0
    assert p11111.best_q_value == 0.01
    assert report.reproducibility_hash


def test_protein_grouping_renderers_emit_stable_ledgers() -> None:
    report = build_protein_grouping_report(_grouping_records())

    summary_tsv = render_protein_grouping_summary_tsv(report)
    entries_tsv = render_protein_grouping_entries_tsv(report)

    assert summary_tsv.startswith("metric\tvalue")
    assert "ambiguous_group_count\t1" in summary_tsv
    assert "reproducibility_hash\t" in summary_tsv
    assert entries_tsv.startswith(
        "group_id\trepresentative_protein\tleading_protein\tleading_rationale"
    )
    assert "P22222\tP22222\tlexicographic_tiebreak\tP22222;P44444" in entries_tsv
