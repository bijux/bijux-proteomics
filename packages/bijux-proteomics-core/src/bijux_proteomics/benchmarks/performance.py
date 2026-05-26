# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Performance and reproducibility benchmark surfaces."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class MillionPsmIngestionBenchmarkInput(JsonModel):
    """Timing and memory observations for million-PSM ingestion benchmark."""

    model_config = ConfigDict(extra="forbid")

    psm_count: int = Field(..., ge=1)
    parse_seconds: float = Field(..., gt=0.0)
    normalize_seconds: float = Field(..., gt=0.0)
    fdr_seconds: float = Field(..., gt=0.0)
    trace_export_seconds: float = Field(..., gt=0.0)
    peak_memory_mb: float = Field(..., gt=0.0)


class MillionPsmIngestionBenchmarkReport(JsonModel):
    """Benchmark report for parsing/normalization/FDR/trace export at million-PSM scale."""

    model_config = ConfigDict(extra="forbid")

    psm_count: int = Field(..., ge=1)
    total_seconds: float = Field(..., gt=0.0)
    throughput_psm_per_second: float = Field(..., gt=0.0)
    peak_memory_mb: float = Field(..., gt=0.0)
    bottleneck_stage: str = Field(..., min_length=1)


def build_million_psm_ingestion_benchmark_report(
    payload: MillionPsmIngestionBenchmarkInput,
) -> MillionPsmIngestionBenchmarkReport:
    """Measure parse/normalize/FDR/trace-export throughput for large PSM corpora."""

    stage_durations = {
        "parse": payload.parse_seconds,
        "normalize": payload.normalize_seconds,
        "fdr": payload.fdr_seconds,
        "trace_export": payload.trace_export_seconds,
    }
    total_seconds = sum(stage_durations.values())
    throughput = payload.psm_count / total_seconds
    bottleneck_stage = max(stage_durations.items(), key=lambda row: row[1])[0]

    return MillionPsmIngestionBenchmarkReport(
        psm_count=payload.psm_count,
        total_seconds=total_seconds,
        throughput_psm_per_second=throughput,
        peak_memory_mb=payload.peak_memory_mb,
        bottleneck_stage=bottleneck_stage,
    )


class DenseQuantMatrixBenchmarkInput(JsonModel):
    """Timing and memory observations for dense quantification-matrix workloads."""

    model_config = ConfigDict(extra="forbid")

    matrix_rows: int = Field(..., ge=1)
    matrix_columns: int = Field(..., ge=1)
    normalization_seconds: float = Field(..., gt=0.0)
    rollup_seconds: float = Field(..., gt=0.0)
    missingness_seconds: float = Field(..., gt=0.0)
    da_prep_seconds: float = Field(..., gt=0.0)
    peak_memory_mb: float = Field(..., gt=0.0)
    output_size_mb: float = Field(..., gt=0.0)


class DenseQuantMatrixBenchmarkReport(JsonModel):
    """Benchmark report for dense quant normalization/rollup/missingness/DA prep."""

    model_config = ConfigDict(extra="forbid")

    matrix_rows: int = Field(..., ge=1)
    matrix_columns: int = Field(..., ge=1)
    matrix_cells: int = Field(..., ge=1)
    total_seconds: float = Field(..., gt=0.0)
    cells_per_second: float = Field(..., gt=0.0)
    peak_memory_mb: float = Field(..., gt=0.0)
    output_size_mb: float = Field(..., gt=0.0)
    bottleneck_stage: str = Field(..., min_length=1)


def build_dense_quant_matrix_benchmark_report(
    payload: DenseQuantMatrixBenchmarkInput,
) -> DenseQuantMatrixBenchmarkReport:
    """Measure dense quant matrix normalization/rollup/missingness/DA-prep performance."""

    stage_durations = {
        "normalization": payload.normalization_seconds,
        "rollup": payload.rollup_seconds,
        "missingness": payload.missingness_seconds,
        "da_prep": payload.da_prep_seconds,
    }
    total_seconds = sum(stage_durations.values())
    matrix_cells = payload.matrix_rows * payload.matrix_columns
    cells_per_second = matrix_cells / total_seconds
    bottleneck_stage = max(stage_durations.items(), key=lambda row: row[1])[0]
    return DenseQuantMatrixBenchmarkReport(
        matrix_rows=payload.matrix_rows,
        matrix_columns=payload.matrix_columns,
        matrix_cells=matrix_cells,
        total_seconds=total_seconds,
        cells_per_second=cells_per_second,
        peak_memory_mb=payload.peak_memory_mb,
        output_size_mb=payload.output_size_mb,
        bottleneck_stage=bottleneck_stage,
    )


class LargeSpectraStreamingBenchmarkInput(JsonModel):
    """Observed metrics for large MGF/mzML streaming parse workloads."""

    model_config = ConfigDict(extra="forbid")

    format_name: str = Field(..., min_length=1)
    spectrum_count: int = Field(..., ge=1)
    input_size_mb: float = Field(..., gt=0.0)
    parse_seconds: float = Field(..., gt=0.0)
    peak_memory_mb: float = Field(..., gt=0.0)


class LargeSpectraStreamingBenchmarkReport(JsonModel):
    """Benchmark report for large spectra streaming throughput and memory behavior."""

    model_config = ConfigDict(extra="forbid")

    format_name: str = Field(..., min_length=1)
    spectrum_count: int = Field(..., ge=1)
    throughput_spectra_per_second: float = Field(..., gt=0.0)
    throughput_mb_per_second: float = Field(..., gt=0.0)
    peak_memory_mb: float = Field(..., gt=0.0)


def build_large_spectra_streaming_benchmark_report(
    payload: LargeSpectraStreamingBenchmarkInput,
) -> LargeSpectraStreamingBenchmarkReport:
    """Measure large MGF/mzML streaming throughput and memory footprint."""

    return LargeSpectraStreamingBenchmarkReport(
        format_name=payload.format_name,
        spectrum_count=payload.spectrum_count,
        throughput_spectra_per_second=payload.spectrum_count / payload.parse_seconds,
        throughput_mb_per_second=payload.input_size_mb / payload.parse_seconds,
        peak_memory_mb=payload.peak_memory_mb,
    )


class ParserMemoryBenchmarkInput(JsonModel):
    """Observed memory behavior for one generated parser workload."""

    model_config = ConfigDict(extra="forbid")

    parser_id: str = Field(..., min_length=1)
    workload_unit: str = Field(..., min_length=1)
    generated_unit_count: int = Field(..., ge=1)
    input_size_mb: float = Field(..., gt=0.0)
    peak_memory_mb: float = Field(..., gt=0.0)
    memory_ceiling_mb: float = Field(..., gt=0.0)


class ParserMemoryBenchmarkReport(JsonModel):
    """Benchmark report for parser memory ceilings under generated large inputs."""

    model_config = ConfigDict(extra="forbid")

    parser_id: str = Field(..., min_length=1)
    workload_unit: str = Field(..., min_length=1)
    generated_unit_count: int = Field(..., ge=1)
    input_size_mb: float = Field(..., gt=0.0)
    peak_memory_mb: float = Field(..., gt=0.0)
    memory_ceiling_mb: float = Field(..., gt=0.0)
    memory_headroom_mb: float
    ceiling_respected: bool
    memory_per_unit_kb: float = Field(..., ge=0.0)


def build_parser_memory_benchmark_report(
    payload: ParserMemoryBenchmarkInput,
) -> ParserMemoryBenchmarkReport:
    """Summarize one parser memory observation against its declared ceiling."""

    memory_headroom_mb = payload.memory_ceiling_mb - payload.peak_memory_mb
    return ParserMemoryBenchmarkReport(
        parser_id=payload.parser_id,
        workload_unit=payload.workload_unit,
        generated_unit_count=payload.generated_unit_count,
        input_size_mb=payload.input_size_mb,
        peak_memory_mb=payload.peak_memory_mb,
        memory_ceiling_mb=payload.memory_ceiling_mb,
        memory_headroom_mb=memory_headroom_mb,
        ceiling_respected=memory_headroom_mb >= 0.0,
        memory_per_unit_kb=(payload.peak_memory_mb * 1024.0)
        / payload.generated_unit_count,
    )


class EvidenceGraphScaleBenchmarkInput(JsonModel):
    """Stage timings for evidence-graph build/query/packet/export at scale."""

    model_config = ConfigDict(extra="forbid")

    node_count: int = Field(..., ge=1)
    edge_count: int = Field(..., ge=0)
    build_seconds: float = Field(..., gt=0.0)
    query_seconds: float = Field(..., gt=0.0)
    packet_seconds: float = Field(..., gt=0.0)
    export_seconds: float = Field(..., gt=0.0)


class EvidenceGraphScaleBenchmarkReport(JsonModel):
    """Scale benchmark report for evidence-graph processing surfaces."""

    model_config = ConfigDict(extra="forbid")

    node_count: int = Field(..., ge=1)
    edge_count: int = Field(..., ge=0)
    total_seconds: float = Field(..., gt=0.0)
    edges_processed_per_second: float = Field(..., gt=0.0)
    bottleneck_stage: str = Field(..., min_length=1)


def build_evidence_graph_scale_benchmark_report(
    payload: EvidenceGraphScaleBenchmarkInput,
) -> EvidenceGraphScaleBenchmarkReport:
    """Measure evidence-graph build/query/review-packet/export bottlenecks."""

    durations = {
        "build": payload.build_seconds,
        "query": payload.query_seconds,
        "packet": payload.packet_seconds,
        "export": payload.export_seconds,
    }
    total = sum(durations.values())
    edges_processed = max(1, payload.edge_count)
    return EvidenceGraphScaleBenchmarkReport(
        node_count=payload.node_count,
        edge_count=payload.edge_count,
        total_seconds=total,
        edges_processed_per_second=edges_processed / total,
        bottleneck_stage=max(durations.items(), key=lambda row: row[1])[0],
    )


class ReviewPacketScaleBenchmarkInput(JsonModel):
    """Scale observations for rendering and navigating large decision briefs."""

    model_config = ConfigDict(extra="forbid")

    candidate_count: int = Field(..., ge=1)
    evidence_entry_count: int = Field(..., ge=0)
    render_seconds: float = Field(..., gt=0.0)
    navigation_seconds: float = Field(..., gt=0.0)
    export_seconds: float = Field(..., gt=0.0)


class ReviewPacketScaleBenchmarkReport(JsonModel):
    """Scale benchmark report for large decision brief surfaces."""

    model_config = ConfigDict(extra="forbid")

    candidate_count: int = Field(..., ge=1)
    evidence_entry_count: int = Field(..., ge=0)
    total_seconds: float = Field(..., gt=0.0)
    candidates_per_second: float = Field(..., gt=0.0)
    bottleneck_stage: str = Field(..., min_length=1)


def build_review_packet_scale_benchmark_report(
    payload: ReviewPacketScaleBenchmarkInput,
) -> ReviewPacketScaleBenchmarkReport:
    """Measure review-packet render/navigation/export behavior at large candidate counts."""

    durations = {
        "render": payload.render_seconds,
        "navigation": payload.navigation_seconds,
        "export": payload.export_seconds,
    }
    total = sum(durations.values())
    return ReviewPacketScaleBenchmarkReport(
        candidate_count=payload.candidate_count,
        evidence_entry_count=payload.evidence_entry_count,
        total_seconds=total,
        candidates_per_second=payload.candidate_count / total,
        bottleneck_stage=max(durations.items(), key=lambda row: row[1])[0],
    )


class WorkflowStartupBenchmarkInput(JsonModel):
    """Startup timing observations for local workflow initialization."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    setup_seconds: float = Field(..., gt=0.0)
    artifact_initialization_seconds: float = Field(..., gt=0.0)
    bundle_initialization_seconds: float = Field(..., gt=0.0)


class WorkflowStartupBenchmarkReport(JsonModel):
    """Benchmark report for local workflow setup and initial artifact/bundle prep."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    total_startup_seconds: float = Field(..., gt=0.0)
    bottleneck_stage: str = Field(..., min_length=1)


def build_workflow_startup_benchmark_report(
    payload: WorkflowStartupBenchmarkInput,
) -> WorkflowStartupBenchmarkReport:
    """Measure local workflow startup bottlenecks before scientific execution."""

    durations = {
        "setup": payload.setup_seconds,
        "artifact_initialization": payload.artifact_initialization_seconds,
        "bundle_initialization": payload.bundle_initialization_seconds,
    }
    return WorkflowStartupBenchmarkReport(
        workflow_id=payload.workflow_id,
        total_startup_seconds=sum(durations.values()),
        bottleneck_stage=max(durations.items(), key=lambda row: row[1])[0],
    )


class BenchmarkCorpusClass(StrEnum):
    """Corpus classes for separating benchmark intent and expectations."""

    SMOKE = "smoke"
    REGRESSION = "regression"
    SCALE = "scale"
    SCIENTIFIC_COMPARISON = "scientific_comparison"
    PUBLICATION_DEMO = "publication_demo"


class BenchmarkCorpusDescriptor(JsonModel):
    """Descriptor for one benchmark corpus and its intended class."""

    model_config = ConfigDict(extra="forbid")

    corpus_id: str = Field(..., min_length=1)
    spectrum_count: int = Field(..., ge=0)
    has_scientific_ground_truth: bool
    intended_publication_demo: bool
    class_label: BenchmarkCorpusClass


def classify_benchmark_corpus(
    *,
    corpus_id: str,
    spectrum_count: int,
    has_scientific_ground_truth: bool,
    intended_publication_demo: bool,
) -> BenchmarkCorpusDescriptor:
    """Classify corpus into smoke/regression/scale/scientific-comparison/publication-demo."""

    if intended_publication_demo:
        class_label = BenchmarkCorpusClass.PUBLICATION_DEMO
    elif has_scientific_ground_truth:
        class_label = BenchmarkCorpusClass.SCIENTIFIC_COMPARISON
    elif spectrum_count >= 1_000_000:
        class_label = BenchmarkCorpusClass.SCALE
    elif spectrum_count >= 10_000:
        class_label = BenchmarkCorpusClass.REGRESSION
    else:
        class_label = BenchmarkCorpusClass.SMOKE

    return BenchmarkCorpusDescriptor(
        corpus_id=corpus_id,
        spectrum_count=spectrum_count,
        has_scientific_ground_truth=has_scientific_ground_truth,
        intended_publication_demo=intended_publication_demo,
        class_label=class_label,
    )


class BenchmarkMetricEntry(JsonModel):
    """One metric item attached to a benchmark output bundle."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    value: float
    unit: str = Field(..., min_length=1)


class BenchmarkOutputBundle(JsonModel):
    """Bundle containing corpus, environment, metrics, artifacts, and caveats."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1)
    corpus_id: str = Field(..., min_length=1)
    environment_fingerprint: str = Field(..., min_length=8)
    metrics: tuple[BenchmarkMetricEntry, ...] = Field(default_factory=tuple)
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    caveats: tuple[str, ...] = Field(default_factory=tuple)


def build_benchmark_output_bundle(
    *,
    bundle_id: str,
    corpus_id: str,
    environment_fingerprint: str,
    metrics: tuple[BenchmarkMetricEntry, ...],
    artifact_paths: tuple[str, ...],
    caveats: tuple[str, ...],
) -> BenchmarkOutputBundle:
    """Bundle benchmark corpus, environment, metrics, artifacts, and caveat metadata."""

    return BenchmarkOutputBundle(
        bundle_id=bundle_id,
        corpus_id=corpus_id,
        environment_fingerprint=environment_fingerprint,
        metrics=tuple(sorted(metrics, key=lambda metric: metric.name)),
        artifact_paths=tuple(sorted(set(artifact_paths))),
        caveats=tuple(sorted(set(caveats))),
    )


class ReproducibilityReleaseRun(JsonModel):
    """One release-tagged run snapshot used for long-horizon drift analysis."""

    model_config = ConfigDict(extra="forbid")

    release_tag: str = Field(..., min_length=1)
    workflow_id: str = Field(..., min_length=1)
    output_fingerprint: str = Field(..., min_length=8)


class ReproducibilityDriftEntry(JsonModel):
    """Drift comparison between two release-tagged runs."""

    model_config = ConfigDict(extra="forbid")

    from_release: str = Field(..., min_length=1)
    to_release: str = Field(..., min_length=1)
    changed: bool


class LongHorizonReproducibilityReport(JsonModel):
    """Report describing workflow drift across repeated releases."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    drift_entries: tuple[ReproducibilityDriftEntry, ...] = Field(default_factory=tuple)
    drift_count: int = Field(..., ge=0)


def build_long_horizon_reproducibility_report(
    runs: tuple[ReproducibilityReleaseRun, ...],
) -> LongHorizonReproducibilityReport:
    """Rerun workflow snapshots across releases and report reproducibility drift."""

    if not runs:
        raise ValueError(
            "long-horizon reproducibility report requires at least one run"
        )

    sorted_runs = sorted(runs, key=lambda run: run.release_tag)
    entries = []
    for previous, current in zip(sorted_runs, sorted_runs[1:], strict=False):
        entries.append(
            ReproducibilityDriftEntry(
                from_release=previous.release_tag,
                to_release=current.release_tag,
                changed=previous.output_fingerprint != current.output_fingerprint,
            )
        )

    drift_count = sum(1 for entry in entries if entry.changed)
    return LongHorizonReproducibilityReport(
        workflow_id=sorted_runs[0].workflow_id,
        drift_entries=tuple(entries),
        drift_count=drift_count,
    )


class DependencyUpdateRecord(JsonModel):
    """One dependency/tool/container/model update record."""

    model_config = ConfigDict(extra="forbid")

    dependency_id: str = Field(..., min_length=1)
    surface: str = Field(..., min_length=1)
    previous_version: str = Field(..., min_length=1)
    updated_version: str = Field(..., min_length=1)


class WorkflowDependencyMapping(JsonModel):
    """Declared dependency surfaces for one workflow."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    dependency_surfaces: tuple[str, ...] = Field(default_factory=tuple)


class DependencyUpdateReplayAction(JsonModel):
    """Replay action required for one workflow after dependency updates."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    replay_required: bool
    triggered_by: tuple[str, ...] = Field(default_factory=tuple)


class DependencyUpdateReplayReport(JsonModel):
    """Report of workflows requiring replay after dependency updates."""

    model_config = ConfigDict(extra="forbid")

    actions: tuple[DependencyUpdateReplayAction, ...] = Field(default_factory=tuple)


def build_dependency_update_replay_report(
    *,
    updates: tuple[DependencyUpdateRecord, ...],
    mappings: tuple[WorkflowDependencyMapping, ...],
) -> DependencyUpdateReplayReport:
    """Replay affected workflows after dependency/tool/container/model updates."""

    updated_surfaces = {update.surface for update in updates}
    actions = []
    for mapping in mappings:
        triggered = tuple(
            sorted(
                surface
                for surface in mapping.dependency_surfaces
                if surface in updated_surfaces
            )
        )
        actions.append(
            DependencyUpdateReplayAction(
                workflow_id=mapping.workflow_id,
                replay_required=bool(triggered),
                triggered_by=triggered,
            )
        )

    actions.sort(key=lambda action: action.workflow_id)
    return DependencyUpdateReplayReport(actions=tuple(actions))
