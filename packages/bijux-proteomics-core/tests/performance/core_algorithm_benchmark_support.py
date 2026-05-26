# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
import time

from bijux_proteomics.benchmarks import (
    CoreAlgorithmPerformanceBenchmarkInput,
    CoreAlgorithmPerformanceBenchmarkReport,
    build_core_algorithm_performance_benchmark_report,
)
from bijux_proteomics.identification import (
    PsmRecord,
    TargetDecoyLabel,
    build_psm_target_decoy_fdr_report,
)
from bijux_proteomics.quantification.contracts import (
    MissingValueKind,
    MissingValueSummaryEntry,
    MissingValueSummaryPolicy,
    MissingValueSummaryReport,
    QuantEntityLevel,
    QuantRollupMethod,
)
from bijux_proteomics.quantification.matrix.peptide_intensity_matrix import (
    PeptideIntensityMatrixReport,
    PeptideIntensityMatrixRow,
    PeptideIntensityMatrixSummary,
    PeptideIntensityMatrixValue,
    PeptideMatrixGroupingMode,
    PeptideMatrixSourceKind,
)
from bijux_proteomics.quantification.rollup.protein_lfq import (
    build_protein_lfq_report_from_peptides,
)
from bijux_proteomics.sequences import (
    build_peptide_uniqueness_index,
    digest_protein_records,
)
from bijux_proteomics.sequences.core import NormalizedProteinRecord

_AMINO_ACIDS = "ACDEFGHKMNPQRSTVWY"


@dataclass(frozen=True)
class CoreAlgorithmBenchmarkCase:
    algorithm_id: str
    workload_unit: str
    generated_unit_count: int
    baseline_seconds: float
    regression_threshold_ratio: float


def benchmark_digest_runtime() -> CoreAlgorithmPerformanceBenchmarkReport:
    """Benchmark governed protein digestion over a generated FASTA-like corpus."""

    case = CORE_ALGORITHM_BENCHMARK_CASES["digest"]
    records = _build_generated_protein_records(
        protein_count=case.generated_unit_count,
        peptides_per_protein=18,
    )
    started_at = time.perf_counter()
    digested = digest_protein_records(
        records,
        missed_cleavages=1,
        min_length=7,
        max_length=30,
    )
    observed_seconds = time.perf_counter() - started_at
    assert len(digested) > case.generated_unit_count * 5
    return _build_report(case, observed_seconds=observed_seconds)


def benchmark_peptide_index_runtime() -> CoreAlgorithmPerformanceBenchmarkReport:
    """Benchmark uniqueness indexing over a generated governed protein corpus."""

    case = CORE_ALGORITHM_BENCHMARK_CASES["peptide_index"]
    records = _build_generated_protein_records(
        protein_count=case.generated_unit_count,
        peptides_per_protein=18,
    )
    started_at = time.perf_counter()
    report = build_peptide_uniqueness_index(records, missed_cleavages=1)
    observed_seconds = time.perf_counter() - started_at
    assert report.summary.entry_count > case.generated_unit_count * 5
    return _build_report(case, observed_seconds=observed_seconds)


def benchmark_psm_fdr_runtime() -> CoreAlgorithmPerformanceBenchmarkReport:
    """Benchmark ranked PSM target-decoy FDR over a generated search-result set."""

    case = CORE_ALGORITHM_BENCHMARK_CASES["fdr"]
    records = _build_generated_psm_records(psm_count=case.generated_unit_count)
    started_at = time.perf_counter()
    report = build_psm_target_decoy_fdr_report(records, threshold=0.01)
    observed_seconds = time.perf_counter() - started_at
    assert report.summary.total_psm_count == case.generated_unit_count
    return _build_report(case, observed_seconds=observed_seconds)


def benchmark_matrix_rollup_runtime() -> CoreAlgorithmPerformanceBenchmarkReport:
    """Benchmark protein LFQ rollup over a generated peptide-intensity matrix."""

    case = CORE_ALGORITHM_BENCHMARK_CASES["matrix_rollup"]
    peptide_matrix = _build_generated_peptide_matrix_report(
        protein_target_count=case.generated_unit_count,
        peptides_per_protein=6,
        sample_count=16,
    )
    started_at = time.perf_counter()
    report = build_protein_lfq_report_from_peptides(peptide_matrix)
    observed_seconds = time.perf_counter() - started_at
    assert report.summary.protein_row_count == case.generated_unit_count
    return _build_report(case, observed_seconds=observed_seconds)


def _build_report(
    case: CoreAlgorithmBenchmarkCase,
    *,
    observed_seconds: float,
) -> CoreAlgorithmPerformanceBenchmarkReport:
    return build_core_algorithm_performance_benchmark_report(
        CoreAlgorithmPerformanceBenchmarkInput(
            algorithm_id=case.algorithm_id,
            workload_unit=case.workload_unit,
            generated_unit_count=case.generated_unit_count,
            observed_seconds=observed_seconds,
            baseline_seconds=case.baseline_seconds,
            regression_threshold_ratio=case.regression_threshold_ratio,
        )
    )


def _build_generated_protein_records(
    *,
    protein_count: int,
    peptides_per_protein: int,
) -> tuple[NormalizedProteinRecord, ...]:
    records: list[NormalizedProteinRecord] = []
    for index in range(protein_count):
        residues = "M" + "".join(
            _amino_acid_token(index * peptides_per_protein + offset) + "K"
            for offset in range(peptides_per_protein)
        )
        records.append(
            NormalizedProteinRecord(
                source_header=f"sp|P{index:05d}|PROT{index:05d}",
                source_identifier=f"sp|P{index:05d}|PROT{index:05d}",
                accession_namespace="uniprot",
                canonical_accession=f"P{index:05d}",
                isoform=None,
                display_name=f"Protein {index}",
                gene=f"GENE{index:05d}",
                organism="human",
                description="generated benchmark protein",
                residues=residues,
                residue_count=len(residues),
                sequence_checksum=hashlib.sha256(residues.encode("utf-8")).hexdigest(),
            )
        )
    return tuple(records)


def _amino_acid_token(index: int, *, length: int = 8) -> str:
    characters: list[str] = []
    alphabet_size = len(_AMINO_ACIDS)
    value = index
    for _ in range(length):
        characters.append(_AMINO_ACIDS[value % alphabet_size])
        value //= alphabet_size
    return "".join(characters)


def _build_generated_psm_records(*, psm_count: int) -> tuple[PsmRecord, ...]:
    records: list[PsmRecord] = []
    for index in range(psm_count):
        target = index % 7 != 0
        peptide = _amino_acid_token(index % 5_000) + "K"
        records.append(
            PsmRecord(
                run_id=f"run-{index % 24:02d}",
                spectrum_id=f"scan={index}",
                peptide=peptide,
                canonical_peptide=peptide,
                charge=2 + index % 3,
                score=200.0 - (index % 500) * 0.1 - (0.0 if target else 30.0),
                protein_refs=(
                    (f"P{index % 1_200:05d}",)
                    if target
                    else (f"DECOY_P{index % 1_200:05d}",)
                ),
                target_decoy_label=(
                    TargetDecoyLabel.TARGET if target else TargetDecoyLabel.DECOY
                ),
            )
        )
    return tuple(records)


def _build_generated_peptide_matrix_report(
    *,
    protein_target_count: int,
    peptides_per_protein: int,
    sample_count: int,
) -> PeptideIntensityMatrixReport:
    sample_ids = tuple(f"S{index:02d}" for index in range(sample_count))
    rows: list[PeptideIntensityMatrixRow] = []
    for protein_index in range(protein_target_count):
        protein_ref = f"P{protein_index:05d}"
        for peptide_index in range(peptides_per_protein):
            peptide = (
                _amino_acid_token(protein_index * peptides_per_protein + peptide_index)
                + "K"
            )
            rows.append(
                PeptideIntensityMatrixRow(
                    entity_id=f"{peptide}:{protein_ref}",
                    peptide_sequence=peptide,
                    modified_peptides=(peptide,),
                    charge_states=(2,),
                    protein_refs=(protein_ref,),
                    values=tuple(
                        PeptideIntensityMatrixValue(
                            sample_id=sample_id,
                            abundance=float(
                                (protein_index + 1)
                                * (peptide_index + 2)
                                * (sample_offset + 1)
                            ),
                            missing_value_kind=MissingValueKind.OBSERVED,
                            source_record_count=1,
                        )
                        for sample_offset, sample_id in enumerate(sample_ids)
                    ),
                )
            )

    return PeptideIntensityMatrixReport(
        source_kind=PeptideMatrixSourceKind.FEATURE,
        grouping_mode=PeptideMatrixGroupingMode.PEPTIDE_SEQUENCE,
        separate_charge_states=False,
        aggregation_method=QuantRollupMethod.SUM,
        sample_ids=sample_ids,
        rows=tuple(rows),
        aggregation_entries=(),
        missing_summary=MissingValueSummaryReport(
            entity_level=QuantEntityLevel.PEPTIDE,
            policy=MissingValueSummaryPolicy(),
            entries=tuple(
                MissingValueSummaryEntry(
                    sample_id=sample_id,
                    observed_count=len(rows),
                    zero_count=0,
                    not_observed_count=0,
                    filtered_count=0,
                )
                for sample_id in sample_ids
            ),
            included_entity_ids=tuple(row.entity_id for row in rows),
            excluded_entity_ids=(),
        ),
        summary=PeptideIntensityMatrixSummary(
            accepted_source_record_count=len(rows) * len(sample_ids),
            skipped_source_record_count=0,
            sample_count=len(sample_ids),
            peptide_row_count=len(rows),
            observed_cell_count=len(rows) * len(sample_ids),
            zero_cell_count=0,
            missing_cell_count=0,
            filtered_cell_count=0,
        ),
        note="generated benchmark peptide matrix",
    )


def _benchmark_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "benchmarks" / name


def _load_benchmark_cases() -> dict[str, CoreAlgorithmBenchmarkCase]:
    payload = json.loads(
        _benchmark_fixture("core_algorithm_performance_baselines.json").read_text(
            encoding="utf-8"
        )
    )
    return {
        case["algorithm_id"]: CoreAlgorithmBenchmarkCase(
            algorithm_id=case["algorithm_id"],
            workload_unit=case["workload_unit"],
            generated_unit_count=case["generated_unit_count"],
            baseline_seconds=case["baseline_seconds"],
            regression_threshold_ratio=case["regression_threshold_ratio"],
        )
        for case in payload["cases"]
    }


CORE_ALGORITHM_BENCHMARK_CASES = _load_benchmark_cases()
