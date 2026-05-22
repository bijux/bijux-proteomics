# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.comet_import import (
    CometImportKind,
    build_comet_import_report,
    render_comet_canonical_psm_tsv,
    render_comet_psm_tsv,
    render_comet_summary_tsv,
)


def _bundle_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "comet"
    )


def test_comet_tabular_import_preserves_scores_modifications_and_proteins() -> None:
    root = _bundle_root()

    report = build_comet_import_report(
        root / "comet_psm.tsv",
        config_path=root / "comet.params",
    )

    assert report.import_kind is CometImportKind.TABULAR
    assert report.summary.accepted_psm_count == 3
    assert report.summary.rejected_psm_count == 0
    assert report.summary.canonical_psm_count == 3
    assert report.summary.modified_psm_count == 2
    assert report.summary.xcorr_psm_count == 3
    assert report.summary.delta_cn_psm_count == 3
    assert report.summary.expectation_value_psm_count == 3
    assert report.summary.multi_protein_psm_count == 1
    assert report.summary.target_psm_count == 2
    assert report.summary.decoy_psm_count == 1
    assert report.parameter_report is not None
    assert report.parameter_report.enzyme == "trypsin"
    assert report.canonical_psms[0].record.peptide == "PEP[+79.966331]TIDE"
    assert report.canonical_psms[0].record.modified_peptide == "PEP[+79.966331]TIDE"
    assert (
        report.canonical_psms[1].record.modified_peptide
        == "AC[Carbamidomethyl]DM[Oxidation]K"
    )
    assert report.canonical_psms[1].record.protein_refs == (
        "sp|P23456|TRANSFER_HUMAN",
        "sp|P34567|TRANSFER_MOUSE",
    )
    assert report.canonical_psms[1].delta_cn == 0.11
    assert report.psm_rows[0].modification_count == 1
    assert report.psm_rows[0].xcorr == 3.21
    assert report.psm_rows[1].protein_refs == (
        "sp|P23456|TRANSFER_HUMAN",
        "sp|P34567|TRANSFER_MOUSE",
    )
    assert "modified_peptide" in render_comet_canonical_psm_tsv(report.canonical_psms)
    assert "xcorr_psm_count" in render_comet_summary_tsv(report.summary)
    assert "delta_cn" in render_comet_psm_tsv(report.psm_rows)


def test_comet_pepxml_import_reads_scores_and_target_decoy_labels() -> None:
    report = build_comet_import_report(_bundle_root() / "comet_results.pepxml")

    assert report.import_kind is CometImportKind.PEPXML
    assert report.summary.accepted_psm_count == 3
    assert report.summary.canonical_psm_count == 3
    assert report.summary.modified_psm_count == 2
    assert report.canonical_psms[0].record.run_id == "run01.mzML"
    assert report.canonical_psms[0].record.modified_peptide == "PEP[+79.966331]TIDE"
    assert report.canonical_psms[1].record.protein_refs == (
        "sp|P23456|TRANSFER_HUMAN",
        "sp|P34567|TRANSFER_MOUSE",
    )
    assert (
        report.canonical_psms[1].record.canonical_peptide
        == "AC[Carbamidomethyl]DM[Oxidation]K"
    )
    assert report.psm_rows[0].peptide == "PEP[+79.966331]TIDE"
    assert report.psm_rows[0].expectation_value == 0.00031
    assert report.psm_rows[1].protein_refs == (
        "sp|P23456|TRANSFER_HUMAN",
        "sp|P34567|TRANSFER_MOUSE",
    )
    assert report.psm_rows[2].target_decoy_label.value == "decoy"
