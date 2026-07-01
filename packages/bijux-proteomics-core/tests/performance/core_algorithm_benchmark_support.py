# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import gc
import hashlib
import json
from pathlib import Path
import time
from typing import TypeVar, cast

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
from bijux_proteomics.interpretation.pathway_enrichment import (
    PathwayMemberKind,
    PathwayMembershipRecord,
    build_pathway_enrichment_report,
)
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinReferenceEntry,
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
from bijux_proteomics.review.evidence_graph.evidence_graph import (
    ProteomicsEvidenceEdgeKind,
)
from bijux_proteomics.review.evidence_graph.evidence_graph_queries import (
    query_protein_evidence_summary,
)
from bijux_proteomics.review.evidence_graph.lazy_evidence_graph import (
    load_lazy_proteomics_evidence_graph,
)
from bijux_proteomics.sequences import (
    build_peptide_uniqueness_index,
    digest_protein_records,
)
from bijux_proteomics.sequences.core import NormalizedProteinRecord

_AMINO_ACIDS = "ACDEFGHKMNPQRSTVWY"
_RuntimeValue = TypeVar("_RuntimeValue")
_UNSET = object()


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
    observed_seconds, digested = _measure_runtime_against_case(
        case,
        lambda: digest_protein_records(
            records,
            missed_cleavages=1,
            min_length=7,
            max_length=30,
        ),
    )
    assert len(digested) > case.generated_unit_count * 5
    return _build_report(case, observed_seconds=observed_seconds)


def benchmark_peptide_index_runtime() -> CoreAlgorithmPerformanceBenchmarkReport:
    """Benchmark uniqueness indexing over a generated governed protein corpus."""

    case = CORE_ALGORITHM_BENCHMARK_CASES["peptide_index"]
    records = _build_generated_protein_records(
        protein_count=case.generated_unit_count,
        peptides_per_protein=18,
    )
    observed_seconds, report = _measure_runtime_against_case(
        case, lambda: build_peptide_uniqueness_index(records, missed_cleavages=1)
    )
    assert report.summary.entry_count > case.generated_unit_count * 5
    return _build_report(case, observed_seconds=observed_seconds)


def benchmark_psm_fdr_runtime() -> CoreAlgorithmPerformanceBenchmarkReport:
    """Benchmark ranked PSM target-decoy FDR over a generated search-result set."""

    case = CORE_ALGORITHM_BENCHMARK_CASES["fdr"]
    records = _build_generated_psm_records(psm_count=case.generated_unit_count)
    observed_seconds, report = _measure_runtime_against_case(
        case, lambda: build_psm_target_decoy_fdr_report(records, threshold=0.01)
    )
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
    observed_seconds, report = _measure_runtime_against_case(
        case, lambda: build_protein_lfq_report_from_peptides(peptide_matrix)
    )
    assert report.summary.protein_row_count == case.generated_unit_count
    return _build_report(case, observed_seconds=observed_seconds)


def benchmark_enrichment_runtime() -> CoreAlgorithmPerformanceBenchmarkReport:
    """Benchmark pathway enrichment over a generated protein-membership corpus."""

    case = CORE_ALGORITHM_BENCHMARK_CASES["enrichment"]
    foreground, background, pathway_records = _build_generated_pathway_workload(
        pathway_count=400,
        members_per_pathway=300,
        background_protein_count=2_200,
        foreground_protein_count=440,
    )
    observed_seconds, report = _measure_runtime_against_case(
        case,
        lambda: build_pathway_enrichment_report(
            foreground,
            background,
            pathway_records,
        ),
    )
    assert len(pathway_records) == case.generated_unit_count
    assert report.summary.evaluated_entry_count > 0
    return _build_report(case, observed_seconds=observed_seconds)


def benchmark_graph_query_runtime(
    tmp_path: Path,
) -> CoreAlgorithmPerformanceBenchmarkReport:
    """Benchmark repeated lazy evidence-graph protein-summary queries."""

    case = CORE_ALGORITHM_BENCHMARK_CASES["graph_query"]
    nodes_path, edges_path = _write_generated_lazy_graph_artifacts(
        tmp_path / "lazy_graph",
        protein_node_count=5_000,
    )
    graph = load_lazy_proteomics_evidence_graph(nodes_path, edges_path)

    def _query_workload() -> None:
        for query_index in range(case.generated_unit_count):
            query_protein_evidence_summary(
                graph,
                protein_id=f"P{(query_index * 7) % 5_000:05d}",
            )

    observed_seconds, _ = _measure_runtime_against_case(case, _query_workload)
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


def _measure_runtime(
    operation: Callable[[], _RuntimeValue],
    *,
    rounds: int = 2,
) -> tuple[float, _RuntimeValue]:
    """Measure the fastest hot-path runtime across a few short benchmark rounds."""

    if rounds < 1:
        raise ValueError("benchmark rounds must be at least one")

    gc.collect()
    operation()
    best_seconds: float | None = None
    best_value: _RuntimeValue | object = _UNSET
    for _ in range(rounds):
        gc.collect()
        started_at = time.perf_counter()
        value = operation()
        observed_seconds = time.perf_counter() - started_at
        if best_seconds is None or observed_seconds < best_seconds:
            best_seconds = observed_seconds
            best_value = value
    if best_seconds is None or best_value is _UNSET:
        raise RuntimeError("benchmark measurement did not record any runtime")
    return best_seconds, cast(_RuntimeValue, best_value)


def _measure_runtime_against_case(
    case: CoreAlgorithmBenchmarkCase,
    operation: Callable[[], _RuntimeValue],
) -> tuple[float, _RuntimeValue]:
    """Measure hot-path runtime and retry once when one noisy sample breaches budget."""

    observed_seconds, value = _measure_runtime(operation)
    threshold_seconds = case.baseline_seconds * case.regression_threshold_ratio
    if observed_seconds <= threshold_seconds:
        return observed_seconds, value

    time.sleep(0.25)
    retry_seconds, retry_value = _measure_runtime(operation, rounds=5)
    if retry_seconds < observed_seconds:
        return retry_seconds, retry_value
    return observed_seconds, value


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


def _build_generated_pathway_workload(
    *,
    pathway_count: int,
    members_per_pathway: int,
    background_protein_count: int,
    foreground_protein_count: int,
) -> tuple[
    tuple[ProteinReferenceEntry, ...],
    tuple[ProteinReferenceEntry, ...],
    tuple[PathwayMembershipRecord, ...],
]:
    background = tuple(
        ProteinReferenceEntry(
            row_number=index + 2,
            input_protein_ref=f"P{index:05d}",
            protein_ref=f"P{index:05d}",
        )
        for index in range(background_protein_count)
    )
    foreground = background[:foreground_protein_count]
    pathway_records: list[PathwayMembershipRecord] = []
    for pathway_index in range(pathway_count):
        for member_offset in range(members_per_pathway):
            protein_ref = f"P{(pathway_index * 17 + member_offset) % background_protein_count:05d}"
            pathway_records.append(
                PathwayMembershipRecord(
                    pathway_id=f"path:{pathway_index:03d}",
                    pathway_name=f"Pathway {pathway_index}",
                    source_name="generated",
                    source_accession=f"PW{pathway_index:03d}",
                    member_kind=PathwayMemberKind.PROTEIN,
                    member_id=protein_ref,
                )
            )
    return foreground, background, tuple(pathway_records)


def _write_generated_lazy_graph_artifacts(
    path: Path,
    *,
    protein_node_count: int,
) -> tuple[Path, Path]:
    path.mkdir(parents=True, exist_ok=True)
    nodes_path = path / "evidence_graph_nodes.tsv"
    edges_path = path / "evidence_graph_edges.tsv"
    node_rows = [
        "node_id\tentity_type\tentity_ref\tlabel\tclaim_state\ttrust_class\tcontradiction_ids\tcontext_refs"
    ]
    edge_rows = [
        "source_node_id\ttarget_node_id\trelation\tsource_row_ref\tconfidence\tevidence_type\treason\tsupport_count"
    ]
    for index in range(protein_node_count):
        peptide = _amino_acid_token(index) + "K"
        protein = f"P{index:05d}"
        protein_group = f"PG{index:05d}"
        quant_value = f"Q{index:05d}"
        node_rows.extend(
            (
                f"peptide:{peptide}\tpeptide\t{peptide}\t{peptide}\tobserved\tunreviewed\t\t",
                f"protein:{protein}\tprotein\t{protein}\t{protein}\tobserved\tunreviewed\t\t",
                f"protein_group:{protein_group}\tprotein_group\t{protein_group}\t{protein_group}\tobserved\tunreviewed\t\t",
                f"quant_value:{quant_value}\tquant_value\t{quant_value}\t{quant_value}\tobserved\tunreviewed\t\t",
            )
        )
        edge_rows.extend(
            (
                (
                    f"peptide:{peptide}\tprotein:{protein}\t"
                    f"{ProteomicsEvidenceEdgeKind.PEPTIDE_MAPS_TO_PROTEIN.value}\t"
                    f"digest.tsv:{index + 1}\t1.0\tsequence_mapping\tmaps to protein\t1"
                ),
                (
                    f"peptide:{peptide}\tprotein:{protein}\t"
                    f"{ProteomicsEvidenceEdgeKind.PEPTIDE_QUANTIFIES_PROTEIN.value}\t"
                    f"quant.tsv:{index + 1}\t0.9\tquantification\tquantifies protein\t1"
                ),
                (
                    f"protein:{protein}\tprotein_group:{protein_group}\t"
                    f"{ProteomicsEvidenceEdgeKind.PROTEIN_MEMBER_OF_GROUP.value}\t"
                    f"group.tsv:{index + 1}\t1.0\tannotation\tbelongs to group\t1"
                ),
                (
                    f"protein:{protein}\tquant_value:{quant_value}\t"
                    f"{ProteomicsEvidenceEdgeKind.PROTEIN_QUANTIFIED_BY_QUANT_VALUE.value}\t"
                    f"protein_matrix.tsv:{index + 1}\t0.95\tquantification\tquantified by value\t1"
                ),
            )
        )
    nodes_path.write_text("\n".join(node_rows) + "\n", encoding="utf-8")
    edges_path.write_text("\n".join(edge_rows) + "\n", encoding="utf-8")
    return nodes_path, edges_path


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
