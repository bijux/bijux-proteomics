# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import (
    build_protein_ambiguity_review_report,
    parse_psm_tsv,
    render_protein_ambiguity_entries_tsv,
    render_protein_ambiguity_summary_tsv,
)

from .test_identification_surface import _default_mapping, _psm_fixture


def test_protein_ambiguity_review_reports_mixed_external_and_indistinguishable_groups() -> (
    None
):
    report = parse_psm_tsv(
        _psm_fixture("protein_ambiguity_cases.tsv"), mapping=_default_mapping()
    )

    review = build_protein_ambiguity_review_report(
        report.accepted_records,
        threshold=0.05,
    )

    assert review.summary.total_ambiguity_groups == 3
    assert review.summary.ambiguous_protein_count == 5
    assert review.summary.indistinguishable_group_count == 1
    assert review.summary.external_shared_group_count == 1
    assert review.summary.mixed_group_count == 1
    assert review.summary.high_confidence_group_count == 0
    assert review.summary.medium_confidence_group_count == 1
    assert review.summary.low_confidence_group_count == 2

    mixed = next(
        entry for entry in review.entries if entry.protein_refs == ("P10001", "P20002")
    )
    external = next(
        entry for entry in review.entries if entry.protein_refs == ("P30003",)
    )
    indistinguishable = next(
        entry for entry in review.entries if entry.protein_refs == ("P40004", "P50005")
    )

    assert mixed.ambiguity_reason.value == "mixed"
    assert mixed.protein_refs == ("P10001", "P20002")
    assert mixed.indistinguishable_proteins == ("P10001", "P20002")
    assert mixed.shared_peptides == ("SHAREDX", "SHAREDY")
    assert mixed.outside_group_proteins == ("P30003",)
    assert mixed.unique_peptides == ()
    assert mixed.evidence_tier.value == "ambiguous"
    assert tuple(reason.value for reason in mixed.downgrade_reasons) == (
        "shared_peptide_only",
    )
    assert mixed.confidence_label.value == "low"

    assert external.ambiguity_reason.value == "external_shared_peptides"
    assert external.protein_refs == ("P30003",)
    assert external.indistinguishable_proteins == ()
    assert external.shared_peptides == ("SHAREDX",)
    assert external.unique_peptides == ("UNIQUEB",)
    assert external.outside_group_proteins == ("P10001", "P20002")
    assert external.evidence_tier.value == "moderate"
    assert external.confidence_label.value == "moderate"

    assert indistinguishable.ambiguity_reason.value == "indistinguishable_members"
    assert indistinguishable.protein_refs == ("P40004", "P50005")
    assert indistinguishable.shared_peptides == ("INTERNALQ",)
    assert indistinguishable.outside_group_proteins == ()
    assert indistinguishable.evidence_tier.value == "ambiguous"
    assert indistinguishable.confidence_label.value == "low"


def test_protein_ambiguity_review_renders_summary_and_entry_ledgers() -> None:
    report = parse_psm_tsv(
        _psm_fixture("protein_ambiguity_cases.tsv"), mapping=_default_mapping()
    )

    review = build_protein_ambiguity_review_report(
        report.accepted_records,
        threshold=0.05,
    )

    summary_tsv = render_protein_ambiguity_summary_tsv(review)
    entries_tsv = render_protein_ambiguity_entries_tsv(review)

    assert "total_ambiguity_groups\t3" in summary_tsv
    assert "indistinguishable_group_count\t1" in summary_tsv
    assert "external_shared_group_count\t1" in summary_tsv
    assert "mixed_group_count\t1" in summary_tsv
    assert (
        "P10001\tP10001;P20002\tP10001;P20002\tSHAREDX;SHAREDY\t\tP30003\tmixed"
        in entries_tsv
    )
    assert (
        "P30003\tP30003\t\tSHAREDX\tUNIQUEB\tP10001;P20002\texternal_shared_peptides"
        in entries_tsv
    )
