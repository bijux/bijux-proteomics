# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.dia import build_diann_library_coverage_report


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def _diann_fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "diann"
        / name
    )


def test_build_diann_library_coverage_report_summarizes_library_scope() -> None:
    report = build_diann_library_coverage_report(
        _diann_fixture("diann_library_coverage.tsv"),
        _format_fixture("diann_library_coverage.msp"),
        design_path=_format_fixture("diann_library_coverage.design.tsv"),
    )

    assert report.source_name == "DIA-NN"
    assert report.library_source_format == "msp"
    assert report.summary.library_peptide_count == 5
    assert report.summary.detected_peptide_count == 4
    assert report.summary.observed_outside_library_peptide_count == 1
    assert report.summary.library_protein_count == 5
    assert report.summary.detected_protein_count == 4
    assert report.summary.observed_outside_library_protein_count == 1
    assert report.summary.sample_count == 3
    assert report.summary.condition_count == 2
    assert report.summary.peptide_coverage_fraction == 0.8
    assert report.summary.protein_coverage_fraction == 0.8
    assert "absent from the imported library as separate ledgers" in report.note

    assert len(report.peptide_entries) == 5
    assert report.peptide_entries[0].canonical_peptide == "LIVNLY"
    assert report.peptide_entries[0].protein_refs == ("P44444",)
    assert report.peptide_entries[0].detected_overall is False
    assert report.peptide_entries[0].detected_sample_count == 0
    assert report.peptide_entries[0].detected_condition_count == 0
    assert report.peptide_entries[1].canonical_peptide == "PEPALFA"
    assert report.peptide_entries[1].protein_refs == ("P11111",)
    assert report.peptide_entries[1].detected_overall is True
    assert report.peptide_entries[1].detected_sample_count == 3
    assert report.peptide_entries[1].detected_condition_count == 2

    assert len(report.protein_entries) == 5
    assert report.protein_entries[0].protein_ref == "P11111"
    assert report.protein_entries[0].detected_overall is True
    assert report.protein_entries[0].detected_sample_count == 3
    assert report.protein_entries[0].detected_condition_count == 2
    assert report.protein_entries[-1].protein_ref == "P44444"
    assert report.protein_entries[-1].detected_overall is False
    assert report.protein_entries[-1].detected_sample_count == 0
    assert report.protein_entries[-1].detected_condition_count == 0

    assert len(report.observed_outside_library_peptide_entries) == 1
    assert (
        report.observed_outside_library_peptide_entries[0].canonical_peptide
        == "PEPNOVEL"
    )
    assert report.observed_outside_library_peptide_entries[0].protein_refs == (
        "P55555",
    )
    assert report.observed_outside_library_peptide_entries[0].sample_ids == (
        "sample_A",
    )
    assert report.observed_outside_library_peptide_entries[0].condition_ids == (
        "control",
    )
    assert report.observed_outside_library_peptide_entries[0].detected_sample_count == 1
    assert (
        report.observed_outside_library_peptide_entries[0].detected_condition_count == 1
    )

    assert len(report.observed_outside_library_protein_entries) == 1
    assert report.observed_outside_library_protein_entries[0].protein_ref == "P55555"
    assert report.observed_outside_library_protein_entries[0].sample_ids == (
        "sample_A",
    )
    assert report.observed_outside_library_protein_entries[0].condition_ids == (
        "control",
    )
    assert report.observed_outside_library_protein_entries[0].detected_sample_count == 1
    assert (
        report.observed_outside_library_protein_entries[0].detected_condition_count == 1
    )

    assert report.sample_entries[0].sample_id == "sample_A"
    assert report.sample_entries[0].detected_peptide_count == 4
    assert report.sample_entries[0].detected_protein_count == 4
    assert report.sample_entries[2].sample_id == "sample_C"
    assert report.sample_entries[2].detected_peptide_count == 1
    assert report.sample_entries[2].detected_protein_count == 1

    assert report.condition_entries[0].condition == "control"
    assert report.condition_entries[0].sample_ids == ("sample_A", "sample_B")
    assert report.condition_entries[0].detected_peptide_count == 4
    assert report.condition_entries[0].detected_protein_count == 4
    assert report.condition_entries[1].condition == "treatment"
    assert report.condition_entries[1].detected_peptide_count == 1
    assert report.condition_entries[1].detected_protein_count == 1
