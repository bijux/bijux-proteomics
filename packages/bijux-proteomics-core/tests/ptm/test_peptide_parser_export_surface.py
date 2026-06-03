# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    parse_ptm_peptide_tsv,
    render_ptm_peptide_record_tsv,
    render_ptm_peptide_rejected_tsv,
    render_ptm_peptide_site_tsv,
    render_ptm_peptide_summary_tsv,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def test_ptm_peptide_renderers_keep_summary_record_and_site_views() -> None:
    report = parse_ptm_peptide_tsv(_fixture_path("ptm_peptides.tsv"))

    summary_lines = render_ptm_peptide_summary_tsv(report).splitlines()
    record_lines = render_ptm_peptide_record_tsv(report).splitlines()
    site_lines = render_ptm_peptide_site_tsv(report).splitlines()
    rejected_lines = render_ptm_peptide_rejected_tsv(report).splitlines()

    assert summary_lines[0].startswith(
        "accepted_record_count\trejected_row_count\tparsed_site_count"
    )
    assert summary_lines[1] == "3\t2\t5\t4\t1"
    assert record_lines[0].startswith(
        "localized_peptide\tcanonical_peptide\tsequence\tprotein_ref"
    )
    assert any(
        "AAS[Phospho]PEP\tAAS[Phospho]PEP\tAASPEP\tP11111\t4" in line
        for line in record_lines
    )
    assert site_lines[0].startswith(
        "localized_peptide\tcanonical_peptide\tprotein_ref\tsample_id"
    )
    assert any(
        line
        == "AAS[Phospho]PEP\tAAS[Phospho]PEP\tP11111\tC1\tscan=ptm-peptide-001\tPhospho\tUNIMOD:21\tS\t3\t6\tanywhere"
        for line in site_lines
    )
    assert rejected_lines[0] == "row_number\tissues\traw_fields"
    assert any(
        line.startswith("5\tinvalid_peptide_start_position\tpeptide=M[Oxidation]PEP")
        for line in rejected_lines
    )
