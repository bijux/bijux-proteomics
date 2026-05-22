# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import build_diann_vs_dda_psm_comparison_report


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_build_diann_vs_dda_psm_comparison_report_keeps_protein_overlap_visible() -> None:
    report = build_diann_vs_dda_psm_comparison_report(
        _workflow_fixture("dia_dda_comparison_diann.tsv"),
        _workflow_fixture("dia_dda_comparison_dda_psms.tsv"),
    )

    assert report.summary.dia_protein_count == 3
    assert report.summary.dda_protein_count == 3
    assert report.summary.shared_protein_count == 2
    assert report.summary.dia_only_protein_count == 1
    assert report.summary.dda_only_protein_count == 1
    assert report.protein_overlap[0].protein_ref == "P11111"
    assert report.protein_overlap[0].overlap_class == "shared"
    dia_only_entry = next(
        entry
        for entry in report.protein_overlap
        if entry.protein_ref == "P55555"
    )
    assert dia_only_entry.overlap_class == "dia_only"
    assert dia_only_entry.dia_total_intensity == 2000000.0
    dda_only_entry = next(
        entry
        for entry in report.protein_overlap
        if entry.protein_ref == "P33333"
    )
    assert dda_only_entry.overlap_class == "dda_only"
    assert dda_only_entry.dda_total_intensity == 1340000.0


def test_build_diann_vs_dda_psm_comparison_report_keeps_peptide_overlap_visible() -> None:
    report = build_diann_vs_dda_psm_comparison_report(
        _workflow_fixture("dia_dda_comparison_diann.tsv"),
        _workflow_fixture("dia_dda_comparison_dda_psms.tsv"),
    )

    assert report.summary.dia_peptide_count == 3
    assert report.summary.dda_peptide_count == 3
    assert report.summary.shared_peptide_count == 2
    assert report.summary.dia_only_peptide_count == 1
    assert report.summary.dda_only_peptide_count == 1
    shared_entry = next(
        entry
        for entry in report.peptide_overlap
        if entry.peptide_sequence == "PESTIDE"
    )
    assert shared_entry.overlap_class == "shared"
    assert shared_entry.dia_protein_refs == ("P11111",)
    dia_only_entry = next(
        entry
        for entry in report.peptide_overlap
        if entry.peptide_sequence == "DIAONLY"
    )
    assert dia_only_entry.overlap_class == "dia_only"
    dda_only_entry = next(
        entry
        for entry in report.peptide_overlap
        if entry.peptide_sequence == "DDAONLY"
    )
    assert dda_only_entry.overlap_class == "dda_only"


def test_build_diann_vs_dda_psm_comparison_report_keeps_exclusive_evidence_visible() -> None:
    report = build_diann_vs_dda_psm_comparison_report(
        _workflow_fixture("dia_dda_comparison_diann.tsv"),
        _workflow_fixture("dia_dda_comparison_dda_psms.tsv"),
    )

    assert report.summary.exclusive_evidence_entry_count == 4
    dia_only_protein = next(
        entry
        for entry in report.exclusive_evidence
        if entry.source_kind == "dia"
        and entry.entity_level == "protein"
        and entry.entity_id == "P55555"
    )
    assert dia_only_protein.total_intensity == 2000000.0
    dda_only_peptide = next(
        entry
        for entry in report.exclusive_evidence
        if entry.source_kind == "dda"
        and entry.entity_level == "peptide"
        and entry.entity_id == "DDAONLY"
    )
    assert dda_only_peptide.protein_refs == ("P33333",)


def test_build_diann_vs_dda_psm_comparison_report_keeps_shared_intensity_correlation_visible() -> None:
    report = build_diann_vs_dda_psm_comparison_report(
        _workflow_fixture("dia_dda_comparison_diann.tsv"),
        _workflow_fixture("dia_dda_comparison_dda_psms.tsv"),
    )

    assert report.summary.shared_intensity_correlation_entry_count == 4
    assert report.summary.protein_correlation_entry_count == 2
    assert report.summary.peptide_correlation_entry_count == 2
    peptide_entry = next(
        entry
        for entry in report.shared_intensity_correlation
        if entry.entity_level == "peptide" and entry.entity_id == "PESTIDE"
    )
    assert peptide_entry.shared_sample_count == 2
    assert peptide_entry.pearson_correlation == 1.0
    protein_entry = next(
        entry
        for entry in report.shared_intensity_correlation
        if entry.entity_level == "protein" and entry.entity_id == "P22222"
    )
    assert protein_entry.shared_sample_count == 2
    assert protein_entry.pearson_correlation == 1.0
