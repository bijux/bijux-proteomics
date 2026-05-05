# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification.confidence import (
    build_dia_native_fdr_model_report,
)


def _records() -> tuple[PsmRecord, ...]:
    return (
        PsmRecord(
            spectrum_id="dia-runA_precursor1",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            charge=2,
            score=0.002,
            q_value=0.002,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="dia-runA_precursor2",
            peptide="PEPTIDER",
            canonical_peptide="PEPTIDER",
            charge=3,
            score=0.007,
            q_value=0.007,
            protein_refs=("P22222",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="dia-runA_precursor3",
            peptide="DECOYPEP",
            canonical_peptide="DECOYPEP",
            charge=2,
            score=0.08,
            q_value=0.08,
            protein_refs=("DECOY_P33333",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
    )


def test_dia_native_fdr_model_report_produces_multi_level_snapshots() -> None:
    report = build_dia_native_fdr_model_report(
        _records(),
        is_dia_context=True,
        score_orientation="lower_better",
    )

    assert report.compatible is True
    assert report.thresholds == (0.01, 0.05, 0.1)
    assert len(report.snapshots) == 3
    assert (
        report.snapshots[0].accepted_precursor_count
        <= report.snapshots[-1].accepted_precursor_count
    )


def test_dia_native_fdr_model_report_refuses_non_dia_context() -> None:
    report = build_dia_native_fdr_model_report(
        _records(),
        is_dia_context=False,
    )

    assert report.compatible is False
    assert report.refusal_issues[0].code == "non_dia_context"
