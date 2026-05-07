# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification.contracts import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification.target_decoy_benchmarks import (
    TargetDecoyCalibrationBenchmarkInput,
    build_target_decoy_calibration_benchmark_report,
)
from bijux_proteomics.sequences.core import (
    DecoyGenerationMode,
    NormalizedProteinRecord,
    sequence_checksum,
)


def _protein(accession: str, sequence: str) -> NormalizedProteinRecord:
    return NormalizedProteinRecord(
        source_header=accession,
        source_identifier=accession,
        accession_namespace="uniprot",
        canonical_accession=accession,
        display_name=accession,
        residues=sequence,
        residue_count=len(sequence),
        sequence_checksum=sequence_checksum(sequence),
    )


def _psm_records() -> tuple[PsmRecord, ...]:
    return (
        PsmRecord(
            spectrum_id="s001",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            charge=2,
            score=125.0,
            q_value=0.001,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="s002",
            peptide="PEPTIDER",
            canonical_peptide="PEPTIDER",
            charge=2,
            score=112.0,
            q_value=0.002,
            protein_refs=("P22222",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="s003",
            peptide="DECOYPEP",
            canonical_peptide="DECOYPEP",
            charge=2,
            score=18.0,
            q_value=0.25,
            protein_refs=("DECOY_P11111",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
    )


def test_target_decoy_calibration_benchmark_report_checks_decoy_modes() -> None:
    proteins = (_protein("P11111", "PEPTIDEK"), _protein("P22222", "PEPTIDER"))
    report = build_target_decoy_calibration_benchmark_report(
        (
            TargetDecoyCalibrationBenchmarkInput(
                benchmark_id="reverse",
                decoy_mode=DecoyGenerationMode.REVERSE,
                target_records=proteins,
                psm_records=_psm_records(),
            ),
            TargetDecoyCalibrationBenchmarkInput(
                benchmark_id="shuffle",
                decoy_mode=DecoyGenerationMode.SHUFFLE,
                target_records=proteins,
                psm_records=_psm_records(),
            ),
        )
    )

    assert report.release_blocked is False
    assert len(report.entries) == 2
    assert {entry.decoy_mode for entry in report.entries} == {
        DecoyGenerationMode.REVERSE,
        DecoyGenerationMode.SHUFFLE,
    }
    assert all(entry.database_valid for entry in report.entries)
    assert all(entry.top_fraction_decoy_interval_width >= 0.0 for entry in report.entries)
