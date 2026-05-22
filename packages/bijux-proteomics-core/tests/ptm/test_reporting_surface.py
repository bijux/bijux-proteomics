# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    build_ptm_report_bundle,
    parse_ptm_localization_tsv,
    render_ptm_report_localization_tsv,
    render_ptm_report_peptide_tsv,
    render_ptm_report_summary_tsv,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _ptm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _protein_sequences() -> dict[str, str]:
    fasta = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "fasta"
        / "ptm_sites.fasta"
    )
    report = parse_fasta_document(fasta.read_text(), mode=FastaParseMode.STRICT)
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def test_ptm_report_bundle_builds_core_peptide_and_site_surfaces() -> None:
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))

    report = build_ptm_report_bundle(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )

    assert report.summary.accepted_evidence_count == 8
    assert report.summary.peptide_entry_count == 8
    assert report.summary.site_row_count == 5
    assert report.summary.ambiguous_site_count == 2
    assert report.summary.modified_peptide_count == 3
    assert report.summary.localization_entry_count == 8
    assert any(
        entry.localized_peptide == "S[Phospho]PEPTIDEK"
        for entry in report.peptide_entries
    )
    assert any(
        entry.site_key == "P11111:S5:Phospho"
        for entry in report.site_table
    )


def test_ptm_report_bundle_renderers_keep_peptide_and_localization_sections_explicit() -> (
    None
):
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))

    report = build_ptm_report_bundle(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
        fragment_ion_support_by_spectrum={
            "scan=ptm-001": ("b5", "y7"),
            "scan=ptm-005": ("b2",),
        },
    )

    summary_lines = render_ptm_report_summary_tsv(report).splitlines()
    peptide_lines = render_ptm_report_peptide_tsv(report).splitlines()
    localization_lines = render_ptm_report_localization_tsv(report).splitlines()

    assert summary_lines[0] == (
        "accepted_evidence_count\tpeptide_entry_count\tsite_row_count\t"
        "ambiguous_site_count\tmodified_peptide_count\tlocalization_entry_count"
    )
    assert peptide_lines[0].startswith(
        "spectrum_id\tsample_id\tlocalized_peptide\tcanonical_peptide"
    )
    assert any("S[Phospho]PEPTIDEK" in line for line in peptide_lines)
    assert localization_lines[0].startswith(
        "spectrum_id\tsample_id\tlocalized_peptide\tcanonical_peptide\tmodification_name"
    )
