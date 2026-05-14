# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_runtime.workflows.runs import (
    DdaSearchHitInput,
    run_dda_import_workflow_end_to_end,
    run_sequence_to_digest_workflow_end_to_end,
)


def test_run_sequence_to_digest_workflow_end_to_end_produces_deterministic_report() -> (
    None
):
    fasta = ">sp|P12345|PROT1 example\nMKWVTFISLLFLFSSAYSRGVFRR\n>sp|Q8ABC1|PROT2 example\nGASPVFTLDELRDEGKASSAK"

    report = run_sequence_to_digest_workflow_end_to_end(fasta)

    assert report.status.value == "completed"
    assert report.target_record_count == 2
    assert report.decoy_record_count == 2
    assert report.target_peptide_count >= 1
    assert report.decoy_peptide_count >= 1
    assert len(report.replay_cache_key) == 64
    assert [step.step_id for step in report.steps] == [
        "parse-fasta",
        "generate-decoys",
        "digest-targets",
        "digest-decoys",
    ]


def test_run_dda_import_workflow_end_to_end_tracks_psm_to_protein_qc() -> None:
    mgf = """BEGIN IONS
TITLE=scan=1
PEPMASS=500.2
CHARGE=2+
100.0 250.0
200.0 125.0
END IONS
BEGIN IONS
TITLE=scan=2
PEPMASS=620.3
CHARGE=2+
110.0 300.0
220.0 80.0
END IONS
"""
    hits = (
        DdaSearchHitInput(
            spectrum_id="scan=1",
            peptide="PEPTIDEK",
            protein_ref="P11111",
            score=42.1,
        ),
        DdaSearchHitInput(
            spectrum_id="scan=2",
            peptide="PEPTIDER",
            protein_ref="P11111",
            score=39.7,
        ),
        DdaSearchHitInput(
            spectrum_id="scan=missing",
            peptide="OTHERPEP",
            protein_ref="Q99999",
            score=12.0,
        ),
    )

    report = run_dda_import_workflow_end_to_end(mgf, search_hits=hits)

    assert report.status.value == "completed"
    assert report.spectrum_count == 2
    assert report.accepted_psm_count == 2
    assert report.rejected_psm_count == 1
    assert report.peptide_count == 2
    assert report.protein_count == 1
    assert report.qc_issue_count == 1
    assert report.steps[-1].step_id == "qc-evidence"
