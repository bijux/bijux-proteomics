# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification.picked_protein_fdr import (
    build_picked_protein_fdr_report_from_psm_records,
    render_picked_protein_pair_tsv,
)


def _picked_records() -> tuple[PsmRecord, ...]:
    return (
        PsmRecord(
            spectrum_id="scan=8001",
            peptide="PEPTIDEK",
            canonical_peptide="PEPTIDEK",
            charge=2,
            score=110.0,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=8002",
            peptide="M[Oxidation]PEPTIDEK",
            canonical_peptide="M[Oxidation]PEPTIDEK",
            charge=3,
            score=105.0,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=8003",
            peptide="SHAREDK",
            canonical_peptide="SHAREDK",
            charge=2,
            score=100.0,
            protein_refs=("P22222", "P33333"),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=8004",
            peptide="GLYGLYK",
            canonical_peptide="GLYGLYK",
            charge=2,
            score=98.0,
            protein_refs=("P22222",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=8008",
            peptide="TARGETK",
            canonical_peptide="TARGETK",
            charge=4,
            score=93.0,
            protein_refs=("P44444",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=8006",
            peptide="DECOYPEP",
            canonical_peptide="DECOYPEP",
            charge=2,
            score=96.0,
            protein_refs=("DECOY_P11111",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
        PsmRecord(
            spectrum_id="scan=8007",
            peptide="DECOYSHAREDK",
            canonical_peptide="DECOYSHAREDK",
            charge=2,
            score=94.0,
            protein_refs=("DECOY_P22222",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
        PsmRecord(
            spectrum_id="scan=8009",
            peptide="DECOYWINK",
            canonical_peptide="DECOYWINK",
            charge=2,
            score=92.0,
            protein_refs=("DECOY_P55555",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
        PsmRecord(
            spectrum_id="scan=8010",
            peptide="TARGETWINK",
            canonical_peptide="TARGETWINK",
            charge=2,
            score=89.0,
            protein_refs=("P55555",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
    )


def test_picked_protein_fdr_report_records_pair_winners_and_decoy_win_rejection() -> (
    None
):
    report = build_picked_protein_fdr_report_from_psm_records(
        _picked_records(),
        threshold=0.1,
    )

    assert report.summary.total_pair_count == 5
    assert report.summary.target_winner_count == 4
    assert report.summary.decoy_winner_count == 1
    by_base = {entry.base_accession: entry for entry in report.entries}
    assert by_base["P11111"].target_ref == "P11111"
    assert by_base["P11111"].decoy_ref == "DECOY_P11111"
    assert by_base["P11111"].winner_ref == "P11111"
    assert by_base["P55555"].winner_ref == "DECOY_P55555"
    assert by_base["P55555"].winner_target_decoy_label is TargetDecoyLabel.DECOY
    assert by_base["P55555"].accepted is False


def test_picked_protein_fdr_report_orders_pair_winners_by_competition_score() -> None:
    report = build_picked_protein_fdr_report_from_psm_records(
        _picked_records(),
        threshold=0.1,
    )

    assert [entry.winner_ref for entry in report.entries] == [
        "P11111",
        "P22222",
        "P33333",
        "P44444",
        "DECOY_P55555",
    ]
    assert [entry.q_value for entry in report.entries] == sorted(
        entry.q_value for entry in report.entries
    )


def test_picked_protein_fdr_pair_renderer_emits_competition_ledgers() -> None:
    report = build_picked_protein_fdr_report_from_psm_records(
        _picked_records(),
        threshold=0.1,
    )

    rendered = render_picked_protein_pair_tsv(report)

    assert rendered.startswith(
        "pair_id\tbase_accession\ttarget_ref\tdecoy_ref\ttarget_score\tdecoy_score"
    )
    assert (
        "picked:P55555\tP55555\tP55555\tDECOY_P55555\t89.0\t92.0\tDECOY_P55555"
        in rendered
    )
