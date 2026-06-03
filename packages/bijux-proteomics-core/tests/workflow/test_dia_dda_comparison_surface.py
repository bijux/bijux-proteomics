# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import build_diann_vs_dda_psm_comparison_report


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_build_diann_vs_dda_psm_comparison_report_keeps_protein_overlap_visible() -> (
    None
):
    report = build_diann_vs_dda_psm_comparison_report(
        _workflow_fixture("dia_dda_comparison_diann.tsv"),
        _workflow_fixture("dia_dda_comparison_dda_psms.tsv"),
    )

    assert report.summary.dia_protein_count == 4
    assert report.summary.dda_protein_count == 4
    assert report.summary.shared_protein_count == 2
    assert report.summary.dia_only_protein_count == 2
    assert report.summary.dda_only_protein_count == 2
    assert report.protein_overlap[0].protein_ref == "P11111"
    assert report.protein_overlap[0].overlap_class == "shared"
    dia_only_entry = next(
        entry for entry in report.protein_overlap if entry.protein_ref == "P55555"
    )
    assert dia_only_entry.overlap_class == "dia_only"
    assert dia_only_entry.dia_total_intensity == 2000000.0
    dda_only_entry = next(
        entry for entry in report.protein_overlap if entry.protein_ref == "P33333"
    )
    assert dda_only_entry.overlap_class == "dda_only"
    assert dda_only_entry.dda_total_intensity == 1340000.0
    conflicting_support_dia_only = next(
        entry for entry in report.protein_overlap if entry.protein_ref == "P77777"
    )
    assert conflicting_support_dia_only.overlap_class == "dia_only"
    conflicting_support_dda_only = next(
        entry for entry in report.protein_overlap if entry.protein_ref == "P88888"
    )
    assert conflicting_support_dda_only.overlap_class == "dda_only"


def test_build_diann_vs_dda_psm_comparison_report_keeps_peptide_overlap_visible() -> (
    None
):
    report = build_diann_vs_dda_psm_comparison_report(
        _workflow_fixture("dia_dda_comparison_diann.tsv"),
        _workflow_fixture("dia_dda_comparison_dda_psms.tsv"),
    )

    assert report.summary.dia_peptide_count == 4
    assert report.summary.dda_peptide_count == 4
    assert report.summary.shared_peptide_count == 2
    assert report.summary.dia_only_peptide_count == 1
    assert report.summary.dda_only_peptide_count == 1
    assert report.summary.conflicting_peptide_count == 1
    shared_entry = next(
        entry for entry in report.peptide_overlap if entry.peptide_sequence == "PESTIDE"
    )
    assert shared_entry.overlap_class == "shared"
    assert shared_entry.dia_protein_refs == ("P11111",)
    dia_only_entry = next(
        entry for entry in report.peptide_overlap if entry.peptide_sequence == "DIAONLY"
    )
    assert dia_only_entry.overlap_class == "dia_only"
    dda_only_entry = next(
        entry for entry in report.peptide_overlap if entry.peptide_sequence == "DDAONLY"
    )
    assert dda_only_entry.overlap_class == "dda_only"
    conflicting_entry = next(
        entry
        for entry in report.peptide_overlap
        if entry.peptide_sequence == "CONFLICTSEQ"
    )
    assert conflicting_entry.overlap_class == "conflicting"
    assert conflicting_entry.dia_protein_refs == ("P77777",)
    assert conflicting_entry.dda_protein_refs == ("P88888",)


def test_build_diann_vs_dda_psm_comparison_report_keeps_exclusive_and_conflicting_evidence_visible() -> (
    None
):
    report = build_diann_vs_dda_psm_comparison_report(
        _workflow_fixture("dia_dda_comparison_diann.tsv"),
        _workflow_fixture("dia_dda_comparison_dda_psms.tsv"),
    )

    assert report.summary.exclusive_evidence_entry_count == 6
    assert report.summary.conflicting_evidence_entry_count == 1
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
    conflicting_peptide = report.conflicting_evidence[0]
    assert conflicting_peptide.entity_level == "peptide"
    assert conflicting_peptide.entity_id == "CONFLICTSEQ"
    assert conflicting_peptide.reason_code == "protein_assignment_mismatch"
    assert conflicting_peptide.dia_protein_refs == ("P77777",)
    assert conflicting_peptide.dda_protein_refs == ("P88888",)


def test_build_diann_vs_dda_psm_comparison_report_keeps_shared_intensity_correlation_visible() -> (
    None
):
    report = build_diann_vs_dda_psm_comparison_report(
        _workflow_fixture("dia_dda_comparison_diann.tsv"),
        _workflow_fixture("dia_dda_comparison_dda_psms.tsv"),
    )

    assert report.summary.shared_intensity_correlation_entry_count == 5
    assert report.summary.protein_correlation_entry_count == 2
    assert report.summary.peptide_correlation_entry_count == 3
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


def test_build_diann_vs_dda_psm_comparison_report_keeps_differential_disagreement_visible() -> (
    None
):
    report = build_diann_vs_dda_psm_comparison_report(
        _workflow_fixture("dia_dda_comparison_diann.tsv"),
        _workflow_fixture("dia_dda_comparison_dda_psms.tsv"),
        dia_differential_tsv_path=_workflow_fixture(
            "dia_dda_comparison_dia_differential.tsv"
        ),
        dda_differential_tsv_path=_workflow_fixture(
            "dia_dda_comparison_dda_differential.tsv"
        ),
    )

    assert report.summary.differential_comparison_entry_count == 4
    assert report.summary.shared_differential_count == 1
    assert report.summary.dia_only_differential_count == 1
    assert report.summary.dda_only_differential_count == 1
    assert report.summary.conflicting_differential_count == 1
    shared_entry = next(
        entry for entry in report.differential_comparison if entry.entity_id == "P11111"
    )
    assert shared_entry.comparison_class == "shared"
    dia_only_entry = next(
        entry for entry in report.differential_comparison if entry.entity_id == "P22222"
    )
    assert dia_only_entry.comparison_class == "dia_only"
    assert dia_only_entry.reason_code == "significant_only_in_dia"
    dda_only_entry = next(
        entry for entry in report.differential_comparison if entry.entity_id == "P33333"
    )
    assert dda_only_entry.comparison_class == "dda_only"
    assert dda_only_entry.reason_code == "significant_only_in_dda"
    conflicting_entry = next(
        entry for entry in report.differential_comparison if entry.entity_id == "P44444"
    )
    assert conflicting_entry.comparison_class == "conflicting"
    assert conflicting_entry.reason_code == "differential_direction_mismatch"
