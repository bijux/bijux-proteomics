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
