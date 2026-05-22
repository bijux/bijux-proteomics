# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.sequences import (
    DuplicateAccessionPolicy,
    FastaParseMode,
    build_fasta_stats,
    deduplicate_fasta_records,
    parse_fasta_document,
)


def test_fasta_stats_count_isoforms_as_distinct_reviewed_accessions() -> None:
    report = parse_fasta_document(
        (
            ">sp|P12345|PROT_HUMAN canonical\nMPEPTIDEK\n"
            ">sp|P12345-2|PROT_HUMAN isoform 2\nMPEPTIDER\n"
        ),
        mode=FastaParseMode.STRICT,
    )

    stats = build_fasta_stats(report.accepted_records)

    assert stats.total_records == 2
    assert stats.unique_accessions == 2


def test_fasta_deduplication_keeps_distinct_isoform_accessions() -> None:
    report = parse_fasta_document(
        (
            ">sp|P12345|PROT_HUMAN canonical\nMPEPTIDEK\n"
            ">sp|P12345-2|PROT_HUMAN isoform 2\nMPEPTIDER\n"
            ">sp|P12345-2|PROT_HUMAN_DUP isoform 2 duplicate\nMPEPTIDER\n"
        ),
        mode=FastaParseMode.PERMISSIVE,
        duplicate_accession_policy=DuplicateAccessionPolicy.ACCEPT_WITH_WARNING,
    )

    records, dedup_report = deduplicate_fasta_records(report.accepted_records)

    assert report.duplicate_accessions == ("uniprot:P12345-2",)
    assert len(records) == 2
    assert {record.isoform for record in records} == {None, 2}
    assert dedup_report.duplicate_accessions == ("sp|P12345-2|PROT_HUMAN_DUP",)
