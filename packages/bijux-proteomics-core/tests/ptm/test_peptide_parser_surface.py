# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import parse_ptm_peptide, parse_ptm_peptide_tsv


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def test_parse_ptm_peptide_extracts_type_residue_and_positions() -> None:
    record = parse_ptm_peptide(
        "AAS[Phospho]PEP",
        protein_ref="P11111",
        peptide_start_position=4,
        sample_id="C1",
        spectrum_id="scan=1",
    )

    assert record.canonical_peptide == "AAS[Phospho]PEP"
    assert record.modification_names == ("Phospho",)
    assert tuple(site.to_dict() for site in record.sites) == (
        {
            "modification_name": "Phospho",
            "controlled_id": "UNIMOD:21",
            "residue": "S",
            "peptide_position": 3,
            "protein_position": 6,
            "site_kind": "anywhere",
        },
    )


def test_parse_ptm_peptide_handles_multiple_modifications_and_terminal_sites() -> None:
    record = parse_ptm_peptide(
        "[Acetyl]-M[Oxidation]STY[Phospho]K",
        protein_ref="P22222",
        peptide_start_position=15,
    )

    assert record.sequence == "MSTYK"
    assert record.modification_names == ("Acetyl", "Oxidation", "Phospho")
    assert [site.modification_name for site in record.sites] == [
        "Acetyl",
        "Oxidation",
        "Phospho",
    ]
    assert [site.residue for site in record.sites] == ["M", "M", "Y"]
    assert [site.peptide_position for site in record.sites] == [1, 1, 4]
    assert [site.protein_position for site in record.sites] == [15, 15, 18]
    assert [site.site_kind.value for site in record.sites] == [
        "peptide_n_term",
        "anywhere",
        "anywhere",
    ]


def test_parse_ptm_peptide_tsv_reports_rejections_and_mapped_sites() -> None:
    report = parse_ptm_peptide_tsv(_fixture_path("ptm_peptides.tsv"))

    assert report.total_rows == 5
    assert report.summary.accepted_record_count == 3
    assert report.summary.rejected_row_count == 2
    assert report.summary.parsed_site_count == 5
    assert report.summary.protein_mapped_site_count == 4
    assert report.summary.multi_modified_record_count == 1

    codes = {issue.code for row in report.rejected_rows for issue in row.issues}
    assert codes == {"invalid_peptide_start_position", "missing_peptide"}

    deamidated = next(
        record
        for record in report.accepted_records
        if record.spectrum_id == "scan=ptm-peptide-003"
    )
    assert deamidated.sites[0].modification_name == "Deamidated"
    assert deamidated.sites[0].residue == "N"
    assert deamidated.sites[0].peptide_position == 1
    assert deamidated.sites[0].protein_position is None
