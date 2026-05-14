# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_runtime.workflows.runs import (
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
