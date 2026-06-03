# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification import (
    SearchResultColumnMapping,
    build_picked_protein_fdr_review_report,
    parse_psm_tsv,
    render_picked_protein_fdr_entries_tsv,
    render_picked_protein_fdr_summary_tsv,
)


def _psm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "psm" / name


def _default_mapping() -> SearchResultColumnMapping:
    return SearchResultColumnMapping(
        spectrum_id="spectrum_id",
        peptide="peptide",
        charge="charge",
        score="score",
        q_value="q_value",
        protein_refs="proteins",
    )


def test_picked_protein_fdr_review_matches_curated_edge_case_fixture() -> None:
    report = parse_psm_tsv(
        _psm_fixture("grouped_picked_fdr_edge_cases.tsv"),
        mapping=_default_mapping(),
    )

    review = build_picked_protein_fdr_review_report(
        report.accepted_records,
        thresholds=(0.1,),
        score_orientation="higher_better",
    )

    assert review.thresholds == (0.1,)
    assert len(review.summaries) == 1
    summary = review.summaries[0]
    assert summary.total_count == 5
    assert summary.total_target_count == 4
    assert summary.total_decoy_count == 1
    assert summary.grouped_protein_count == 2
    assert summary.accepted_count == 4
    assert summary.accepted_target_count == 4
    assert summary.accepted_decoy_count == 0
    entry_index = {entry.protein_ref: entry for entry in review.entries}
    assert entry_index["P11111"].pair_id == "picked:P11111"
    assert entry_index["P11111"].base_accession == "P11111"
    assert entry_index["P11111"].partner_ref == "DECOY_P11111"
    assert entry_index["P11111"].target_score == 110.0
    assert entry_index["P11111"].decoy_score == 96.0
    assert entry_index["P11111"].protein_group_ids == ()
    assert len(entry_index["P22222"].protein_group_ids) == 1
    assert entry_index["DECOY_P55555"].partner_ref == "P55555"
    assert entry_index["DECOY_P55555"].winner_target_decoy_label.value == "decoy"
    assert entry_index["DECOY_P55555"].accepted is False


def test_picked_protein_fdr_review_renders_summary_and_entry_ledgers() -> None:
    report = parse_psm_tsv(
        _psm_fixture("grouped_picked_fdr_edge_cases.tsv"),
        mapping=_default_mapping(),
    )

    review = build_picked_protein_fdr_review_report(
        report.accepted_records,
        thresholds=(0.1,),
        score_orientation="higher_better",
    )
    summary_tsv = render_picked_protein_fdr_summary_tsv(review)
    entries_tsv = render_picked_protein_fdr_entries_tsv(review)

    assert summary_tsv.startswith(
        "threshold\ttotal_count\ttotal_target_count\ttotal_decoy_count"
    )
    assert "0.1\t5\t4\t1\t0\t2\t4\t4\t0\t0\t2" in summary_tsv
    assert entries_tsv.startswith(
        "threshold\tpair_id\tbase_accession\tprotein_ref\tpartner_ref\ttarget_ref"
    )
    assert (
        "0.1\tpicked:P22222\tP22222\tP22222\tDECOY_P22222\tP22222\tDECOY_P22222"
        in entries_tsv
    )
    assert "\t100.0\t94.0\tP22222\ttarget\tpg-" in entries_tsv
