# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import PsmRecord
from bijux_proteomics.identification.cross_run_reproducibility import (
    CrossRunReproducibilityClass,
    RunDetectionContext,
    build_peptide_cross_run_reproducibility_report,
    render_cross_run_reproducibility_entries_tsv,
    render_cross_run_reproducibility_summary_tsv,
)


def test_peptide_cross_run_reproducibility_scores_detection_frequency_and_specificity() -> (
    None
):
    records = (
        PsmRecord(
            run_id="run-a",
            spectrum_id="scan-001",
            peptide="PEPA",
            canonical_peptide="PEPA",
            charge=2,
            score=100.0,
            q_value=0.003,
            protein_refs=("P11111",),
        ),
        PsmRecord(
            run_id="run-b",
            spectrum_id="scan-002",
            peptide="PEPA",
            canonical_peptide="PEPA",
            charge=2,
            score=98.0,
            q_value=0.004,
            protein_refs=("P11111",),
        ),
        PsmRecord(
            run_id="run-c",
            spectrum_id="scan-003",
            peptide="PEPB",
            canonical_peptide="PEPB",
            charge=2,
            score=95.0,
            q_value=0.005,
            protein_refs=("P22222",),
        ),
    )
    run_contexts = (
        RunDetectionContext(
            run_id="run-a",
            sample_id="control-1",
            condition_id="control",
            replicate_id="1",
        ),
        RunDetectionContext(
            run_id="run-b",
            sample_id="control-2",
            condition_id="control",
            replicate_id="2",
        ),
        RunDetectionContext(
            run_id="run-c",
            sample_id="treated-1",
            condition_id="treated",
            replicate_id="1",
        ),
        RunDetectionContext(
            run_id="run-d",
            sample_id="treated-2",
            condition_id="treated",
            replicate_id="2",
        ),
    )

    report = build_peptide_cross_run_reproducibility_report(
        records,
        run_contexts=run_contexts,
    )
    by_peptide = {entry.entity_id: entry for entry in report.entries}

    assert report.summary.total_entries == 2
    assert report.summary.condition_specific_count == 1
    assert report.summary.single_run_only_count == 1
    assert by_peptide["PEPA"].detection_frequency == 0.5
    assert by_peptide["PEPA"].replicate_consistency == 1.0
    assert (
        by_peptide["PEPA"].reproducibility_class
        is CrossRunReproducibilityClass.CONDITION_SPECIFIC
    )
    assert by_peptide["PEPB"].detection_frequency == 0.25
    assert by_peptide["PEPB"].replicate_consistency == 0.5
    assert by_peptide["PEPB"].single_run_only is True
    assert (
        by_peptide["PEPB"].reproducibility_class
        is CrossRunReproducibilityClass.SINGLE_RUN_ONLY
    )

    summary_tsv = render_cross_run_reproducibility_summary_tsv(report)
    entries_tsv = render_cross_run_reproducibility_entries_tsv(report)

    assert "condition_specific_count\t1" in summary_tsv
    assert "single_run_only_count\t1" in summary_tsv
    assert "entity_type\tentity_id\tdetected_run_count" in entries_tsv
    assert "PEPB\t1\t4\t0.25" in entries_tsv


def test_cross_run_reproducibility_without_run_context_keeps_multi_spectrum_support() -> (
    None
):
    report = build_peptide_cross_run_reproducibility_report(
        (
            PsmRecord(
                spectrum_id="scan-010",
                peptide="PEPA",
                canonical_peptide="PEPA",
                charge=2,
                score=100.0,
                q_value=0.003,
                protein_refs=("P11111",),
            ),
            PsmRecord(
                spectrum_id="scan-011",
                peptide="PEPA",
                canonical_peptide="PEPA",
                charge=2,
                score=98.0,
                q_value=0.004,
                protein_refs=("P11111",),
            ),
        )
    )

    entry = report.entries[0]

    assert entry.entity_id == "PEPA"
    assert entry.detected_run_count == 1
    assert entry.run_ids == ()
    assert entry.replicate_consistency == 1.0
    assert entry.reproducibility_class is CrossRunReproducibilityClass.REPRODUCIBLE
