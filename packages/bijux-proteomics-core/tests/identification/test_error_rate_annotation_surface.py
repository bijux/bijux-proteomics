# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification.contracts import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification.error_rate_annotation import (
    ErrorRateProvenanceFlag,
    annotate_psm_error_rates,
    build_psm_error_rate_annotation_report,
    render_psm_error_rate_annotation_summary_tsv,
    render_psm_error_rate_annotation_tsv,
)


def test_error_rate_annotation_prefers_imported_pep_without_mislabeling_local_fdr() -> (
    None
):
    records = (
        PsmRecord(
            spectrum_id="scan=pep-1001",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            charge=2,
            score=100.0,
            posterior_error_probability=0.002,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=pep-1002",
            peptide="DECOYPEP",
            canonical_peptide="DECOYPEP",
            charge=2,
            score=95.0,
            posterior_error_probability=0.12,
            protein_refs=("DECOY_P99999",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
    )

    report = build_psm_error_rate_annotation_report(
        records,
        local_window_size=3,
    )

    assert report.summary.imported_pep_count == 2
    assert report.summary.computed_local_fdr_count == 0
    assert report.entries[0].provenance_flag is ErrorRateProvenanceFlag.IMPORTED_PEP
    assert report.entries[0].imported_pep == 0.002
    assert report.entries[0].computed_local_fdr is None
    assert report.entries[0].psm.error_rate_provenance == "imported_pep"


def test_error_rate_annotation_computes_local_fdr_when_engine_pep_is_absent() -> None:
    records = (
        PsmRecord(
            spectrum_id="scan=lfdr-1001",
            peptide="PEPA",
            canonical_peptide="PEPA",
            charge=2,
            score=100.0,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="scan=lfdr-1002",
            peptide="DECA",
            canonical_peptide="DECA",
            charge=2,
            score=95.0,
            protein_refs=("DECOY_P99999",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
        PsmRecord(
            spectrum_id="scan=lfdr-1003",
            peptide="PEPB",
            canonical_peptide="PEPB",
            charge=2,
            score=90.0,
            protein_refs=("P22222",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
    )

    report = build_psm_error_rate_annotation_report(
        records,
        local_window_size=3,
    )
    annotated = annotate_psm_error_rates(records, local_window_size=3)
    entries_tsv = render_psm_error_rate_annotation_tsv(report)
    summary_tsv = render_psm_error_rate_annotation_summary_tsv(report)

    assert report.summary.imported_pep_count == 0
    assert report.summary.computed_local_fdr_count == 3
    assert report.entries[0].computed_local_fdr == 1.0
    assert report.entries[1].computed_local_fdr == 0.5
    assert annotated[0].error_rate_provenance == "computed_local_fdr"
    assert annotated[1].local_fdr == 0.5
    assert entries_tsv.startswith(
        "spectrum_id\tcanonical_peptide\tcharge\tscore\ttarget_decoy_label"
    )
    assert "computed_local_fdr_count" in summary_tsv
