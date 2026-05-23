# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import (
    build_protein_grouping_review_report,
    filter_psms_by_fdr,
    parse_psm_tsv,
    render_protein_grouping_entries_tsv,
    render_protein_grouping_summary_tsv,
)

from .test_identification_surface import _default_mapping, _psm_fixture


def test_protein_grouping_review_reports_leading_protein_and_peptide_ledgers() -> None:
    report = parse_psm_tsv(
        _psm_fixture("protein_inference_results.tsv"), mapping=_default_mapping()
    )
    accepted = filter_psms_by_fdr(report.accepted_records, threshold=0.05)

    grouping = build_protein_grouping_review_report(accepted)

    assert grouping.summary.total_groups == 3
    assert grouping.reproducibility_hash
    assert grouping.summary.total_proteins == 4
    assert grouping.summary.singleton_group_count == 2
    assert grouping.summary.ambiguous_group_count == 1
    assert grouping.summary.grouped_protein_count == 2
    assert grouping.summary.target_group_count == 3

    p11111 = next(
        entry for entry in grouping.groups if entry.representative_protein == "P11111"
    )
    ambiguous = next(
        entry for entry in grouping.groups if entry.protein_refs == ("P22222", "P44444")
    )

    assert p11111.leading_protein == "P11111"
    assert p11111.leading_rationale == "singleton_group"
    assert p11111.unique_peptides == ("PEPTIDEK",)
    assert p11111.shared_peptides == ("SHAREDK",)

    assert ambiguous.leading_protein == "P22222"
    assert ambiguous.leading_rationale == "lexicographic_tiebreak"
    assert ambiguous.unique_peptides == ()
    assert ambiguous.shared_peptides == ("GLYGLYK", "SHAREDK")
    assert ambiguous.peptide_count == 2

    summary_tsv = render_protein_grouping_summary_tsv(grouping)
    entries_tsv = render_protein_grouping_entries_tsv(grouping)

    assert "ambiguous_group_count\t1" in summary_tsv
    assert "grouped_protein_count\t2" in summary_tsv
    assert "P22222;P44444\tGLYGLYK;SHAREDK\t\tGLYGLYK;SHAREDK\t2\t0\t2\t95.0" in (
        entries_tsv
    )
