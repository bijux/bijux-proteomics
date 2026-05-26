# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Generated local scale demo over parsing, quantification, graph, and reporting."""

from __future__ import annotations

from bijux_proteomics._atomic_files import atomic_write_text
from bijux_proteomics._output_tables import write_output_table_tsv

import csv
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from time import perf_counter
import tracemalloc

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification import (
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    parse_ms1_feature_table,
)
from bijux_proteomics.review.evidence_graph import load_lazy_proteomics_evidence_graph
from bijux_proteomics.workflow.exports import validate_workflow_artifact_manifest
from bijux_proteomics.workflow.reports.biological_reporting import (
    BiologicalResultReportExportManifest,
    BiologicalResultSelectionPolicy,
    build_biological_result_report_bundle_from_quant_table,
    write_biological_result_report_bundle,
)
from bijux_proteomics_foundation import JsonModel


class ScaleDemoConfig(JsonModel):
    """Config for one generated local scale demo run."""

    model_config = ConfigDict(extra="forbid")

    output_dir: Path
    protein_count: int = Field(default=180, ge=12, le=2000)
    peptides_per_protein: int = Field(default=4, ge=2, le=12)
    replicates_per_condition: int = Field(default=6, ge=2, le=24)
    pathway_count: int = Field(default=18, ge=3, le=240)


class ScaleDemoStageMetric(JsonModel):
    """One measured stage over the generated scale demo."""

    model_config = ConfigDict(extra="forbid")

    stage_name: str = Field(..., min_length=1)
    elapsed_seconds: float = Field(..., ge=0.0)
    peak_memory_mib: float = Field(..., ge=0.0)
    primary_row_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class ScaleDemoValidation(JsonModel):
    """Validation results over exported scale-demo artifacts."""

    model_config = ConfigDict(extra="forbid")

    outputs_validated: bool
    manifest_artifact_count: int = Field(..., ge=0)
    differential_row_count: int = Field(..., ge=0)
    protein_card_row_count: int = Field(..., ge=0)
    supported_claim_row_count: int = Field(..., ge=0)
    graph_node_row_count: int = Field(..., ge=0)
    graph_edge_row_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class ScaleDemoSummary(JsonModel):
    """Compact performance and scale summary for one generated local demo."""

    model_config = ConfigDict(extra="forbid")

    elapsed_seconds: float = Field(..., ge=0.0)
    peak_memory_mib: float = Field(..., ge=0.0)
    sample_count: int = Field(..., ge=0)
    protein_count: int = Field(..., ge=0)
    peptide_count: int = Field(..., ge=0)
    generated_feature_row_count: int = Field(..., ge=0)
    parsed_feature_row_count: int = Field(..., ge=0)
    quant_value_row_count: int = Field(..., ge=0)
    graph_node_count: int = Field(..., ge=0)
    graph_edge_count: int = Field(..., ge=0)
    differential_row_count: int = Field(..., ge=0)
    protein_card_row_count: int = Field(..., ge=0)
    exported_artifact_count: int = Field(..., ge=0)
    outputs_validated: bool


class ScaleDemoArtifactPaths(JsonModel):
    """Stable artifact locations written by the generated local scale demo."""

    model_config = ConfigDict(extra="forbid")

    feature_tsv: str = Field(..., min_length=1)
    design_tsv: str = Field(..., min_length=1)
    proteins_fasta: str = Field(..., min_length=1)
    pathways_tsv: str = Field(..., min_length=1)
    summary_tsv: str = Field(..., min_length=1)
    stage_metrics_tsv: str = Field(..., min_length=1)
    validation_tsv: str = Field(..., min_length=1)
    report_json: str = Field(..., min_length=1)
    biological_output_dir: str = Field(..., min_length=1)
    biological_report_manifest_json: str = Field(..., min_length=1)
    biological_report_html: str = Field(..., min_length=1)
    evidence_graph_nodes_tsv: str = Field(..., min_length=1)
    evidence_graph_edges_tsv: str = Field(..., min_length=1)
    protein_cards_tsv: str = Field(..., min_length=1)
    supported_claims_tsv: str = Field(..., min_length=1)


class ScaleDemoReport(JsonModel):
    """Execution report for one generated local scale demo."""

    model_config = ConfigDict(extra="forbid")

    config: ScaleDemoConfig
    summary: ScaleDemoSummary
    stage_metrics: tuple[ScaleDemoStageMetric, ...] = Field(default_factory=tuple)
    validation: ScaleDemoValidation
    artifacts: ScaleDemoArtifactPaths
    biological_report_manifest: BiologicalResultReportExportManifest
    note: str = Field(..., min_length=1)


@dataclass(frozen=True, slots=True)
class _GeneratedScaleDataset:
    feature_path: Path
    design_path: Path
    proteins_fasta_path: Path
    pathway_path: Path
    sample_count: int
    protein_count: int
    peptide_count: int
    feature_row_count: int


@dataclass(frozen=True, slots=True)
class _StageMeasurement:
    elapsed_seconds: float
    peak_memory_mib: float


_AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"


def run_scale_demo(config: ScaleDemoConfig) -> ScaleDemoReport:
    """Generate a local scale dataset, run owned reporting, and validate outputs."""

    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_input_dir = output_dir / "generated_inputs"
    biological_output_dir = output_dir / "biological_report"

    total_start = perf_counter()

    dataset, generation_measurement = _measure_stage(
        lambda: _generate_scale_demo_dataset(config, generated_input_dir)
    )
    (feature_parse_report, design_entries), parsing_measurement = _measure_stage(
        lambda: _parse_scale_demo_inputs(dataset)
    )
    quant_table, quant_measurement = _measure_stage(
        lambda: _build_scale_demo_quant_table(
            feature_parse_report.accepted_records,
            peptides_per_protein=config.peptides_per_protein,
        )
    )
    report_bundle, report_measurement = _measure_stage(
        lambda: _build_scale_demo_report_bundle(
            quant_table,
            design_entries,
            proteins_fasta_path=dataset.proteins_fasta_path,
            pathway_path=dataset.pathway_path,
        )
    )
    (biological_manifest, validation), export_measurement = _measure_stage(
        lambda: _export_and_validate_scale_demo(
            report_bundle,
            biological_output_dir=biological_output_dir,
        )
    )

    stage_metrics = (
        ScaleDemoStageMetric(
            stage_name="generate_inputs",
            elapsed_seconds=round(generation_measurement.elapsed_seconds, 6),
            peak_memory_mib=round(generation_measurement.peak_memory_mib, 6),
            primary_row_count=dataset.feature_row_count,
            note=(
                "generated deterministic feature, design, fasta, and pathway inputs "
                "under the local output directory without external files"
            ),
        ),
        ScaleDemoStageMetric(
            stage_name="parse_inputs",
            elapsed_seconds=round(parsing_measurement.elapsed_seconds, 6),
            peak_memory_mib=round(parsing_measurement.peak_memory_mib, 6),
            primary_row_count=len(feature_parse_report.accepted_records),
            note=(
                "parsed the generated MS1 feature table and experimental design "
                "through canonical owned table readers"
            ),
        ),
        ScaleDemoStageMetric(
            stage_name="build_quant_table",
            elapsed_seconds=round(quant_measurement.elapsed_seconds, 6),
            peak_memory_mib=round(quant_measurement.peak_memory_mib, 6),
            primary_row_count=len(quant_table.values),
            note=(
                "aggregated parsed feature rows into one governed protein-level "
                "label-free quantification table"
            ),
        ),
        ScaleDemoStageMetric(
            stage_name="build_report_bundle",
            elapsed_seconds=round(report_measurement.elapsed_seconds, 6),
            peak_memory_mib=round(report_measurement.peak_memory_mib, 6),
            primary_row_count=report_bundle.graph_report.graph.summary.node_count,
            note=(
                "built the biological report bundle, differential surfaces, and "
                "evidence graph over the generated cohort"
            ),
        ),
        ScaleDemoStageMetric(
            stage_name="export_and_validate",
            elapsed_seconds=round(export_measurement.elapsed_seconds, 6),
            peak_memory_mib=round(export_measurement.peak_memory_mib, 6),
            primary_row_count=validation.manifest_artifact_count,
            note=(
                "wrote governed report artifacts, validated the managed manifest, and "
                "round-tripped the exported evidence graph from TSV artifacts"
            ),
        ),
    )

    summary = ScaleDemoSummary(
        elapsed_seconds=round(perf_counter() - total_start, 6),
        peak_memory_mib=round(
            max(metric.peak_memory_mib for metric in stage_metrics),
            6,
        ),
        sample_count=dataset.sample_count,
        protein_count=dataset.protein_count,
        peptide_count=dataset.peptide_count,
        generated_feature_row_count=dataset.feature_row_count,
        parsed_feature_row_count=len(feature_parse_report.accepted_records),
        quant_value_row_count=len(quant_table.values),
        graph_node_count=report_bundle.graph_report.graph.summary.node_count,
        graph_edge_count=report_bundle.graph_report.graph.summary.edge_count,
        differential_row_count=len(report_bundle.differential_report.entries),
        protein_card_row_count=len(report_bundle.protein_cards.cards),
        exported_artifact_count=validation.manifest_artifact_count,
        outputs_validated=validation.outputs_validated,
    )

    artifacts = _write_scale_demo_artifacts(
        output_dir=output_dir,
        dataset=dataset,
        biological_manifest=biological_manifest,
        stage_metrics=stage_metrics,
        summary=summary,
        validation=validation,
    )
    report = ScaleDemoReport(
        config=config,
        summary=summary,
        stage_metrics=stage_metrics,
        validation=validation,
        artifacts=artifacts,
        biological_report_manifest=biological_manifest,
        note=(
            "The scale demo generates deterministic local inputs, parses them through "
            "owned quant readers, builds a governed protein report and evidence graph, "
            "writes review artifacts, and validates the export layout so readers can "
            "exercise larger local performance surfaces without depending on external "
            "datasets."
        ),
    )
    atomic_write_text(output_dir / artifacts.report_json, report.to_stable_json() + "\n")
    return report


def render_scale_demo_summary_tsv(report: ScaleDemoReport) -> str:
    """Render one compact summary TSV for the local scale demo."""

    return _dict_rows_to_tsv(
        [
            {
                "elapsed_seconds": round(report.summary.elapsed_seconds, 6),
                "peak_memory_mib": round(report.summary.peak_memory_mib, 6),
                "sample_count": report.summary.sample_count,
                "protein_count": report.summary.protein_count,
                "peptide_count": report.summary.peptide_count,
                "generated_feature_row_count": report.summary.generated_feature_row_count,
                "parsed_feature_row_count": report.summary.parsed_feature_row_count,
                "quant_value_row_count": report.summary.quant_value_row_count,
                "graph_node_count": report.summary.graph_node_count,
                "graph_edge_count": report.summary.graph_edge_count,
                "differential_row_count": report.summary.differential_row_count,
                "protein_card_row_count": report.summary.protein_card_row_count,
                "exported_artifact_count": report.summary.exported_artifact_count,
                "outputs_validated": str(report.summary.outputs_validated).lower(),
            }
        ]
    )


def render_scale_demo_stage_metrics_tsv(report: ScaleDemoReport) -> str:
    """Render one stage-by-stage performance TSV for the local scale demo."""

    return _dict_rows_to_tsv(
        [
            {
                "stage_name": metric.stage_name,
                "elapsed_seconds": round(metric.elapsed_seconds, 6),
                "peak_memory_mib": round(metric.peak_memory_mib, 6),
                "primary_row_count": metric.primary_row_count,
                "note": metric.note,
            }
            for metric in report.stage_metrics
        ]
    )


def render_scale_demo_validation_tsv(report: ScaleDemoReport) -> str:
    """Render one output-validation TSV for the local scale demo."""

    return _dict_rows_to_tsv(
        [
            {
                "outputs_validated": str(report.validation.outputs_validated).lower(),
                "manifest_artifact_count": report.validation.manifest_artifact_count,
                "differential_row_count": report.validation.differential_row_count,
                "protein_card_row_count": report.validation.protein_card_row_count,
                "supported_claim_row_count": report.validation.supported_claim_row_count,
                "graph_node_row_count": report.validation.graph_node_row_count,
                "graph_edge_row_count": report.validation.graph_edge_row_count,
                "note": report.validation.note,
            }
        ]
    )


def _generate_scale_demo_dataset(
    config: ScaleDemoConfig,
    generated_input_dir: Path,
) -> _GeneratedScaleDataset:
    generated_input_dir.mkdir(parents=True, exist_ok=True)
    feature_path = generated_input_dir / "scale_demo_features.tsv"
    design_path = generated_input_dir / "scale_demo.design.tsv"
    proteins_fasta_path = generated_input_dir / "scale_demo_proteins.fasta"
    pathway_path = generated_input_dir / "scale_demo_pathways.tsv"

    samples = _build_scale_demo_samples(config.replicates_per_condition)
    proteins = tuple(f"P{index + 1:05d}" for index in range(config.protein_count))
    peptides_by_protein = {
        protein_ref: tuple(
            _build_scale_demo_peptide_sequence(protein_index, peptide_index)
            for peptide_index in range(config.peptides_per_protein)
        )
        for protein_index, protein_ref in enumerate(proteins)
    }

    atomic_write_text(feature_path, _render_feature_rows(samples, proteins, peptides_by_protein))
    atomic_write_text(design_path, _render_design_rows(samples))
    atomic_write_text(
        proteins_fasta_path,
        _render_scale_demo_fasta(proteins, peptides_by_protein),
    )
    atomic_write_text(
        pathway_path,
        _render_scale_demo_pathways(proteins, config.pathway_count),
    )

    return _GeneratedScaleDataset(
        feature_path=feature_path,
        design_path=design_path,
        proteins_fasta_path=proteins_fasta_path,
        pathway_path=pathway_path,
        sample_count=len(samples),
        protein_count=len(proteins),
        peptide_count=len(proteins) * config.peptides_per_protein,
        feature_row_count=len(samples) * len(proteins) * config.peptides_per_protein,
    )


def _parse_scale_demo_inputs(
    dataset: _GeneratedScaleDataset,
):
    feature_parse_report = parse_ms1_feature_table(dataset.feature_path)
    if feature_parse_report.rejected_rows:
        raise ValueError("generated scale demo feature table must parse without rejected rows")
    design_report = parse_experimental_design_table(dataset.design_path)
    if design_report.rejected_rows:
        raise ValueError("generated scale demo design table must parse without rejected rows")
    return feature_parse_report, tuple(design_report.accepted_entries)


def _build_scale_demo_quant_table(
    records,
    *,
    peptides_per_protein: int,
):
    return build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
        top_n=min(3, peptides_per_protein),
    )


def _build_scale_demo_report_bundle(
    quant_table,
    design_entries,
    *,
    proteins_fasta_path: Path,
    pathway_path: Path,
):
    return build_biological_result_report_bundle_from_quant_table(
        quant_table,
        design_entries,
        proteins_fasta_path=proteins_fasta_path,
        pathway_membership_tsv_path=pathway_path,
        condition_a="control",
        condition_b="treated",
        selection_policy=BiologicalResultSelectionPolicy(
            max_adjusted_p_value=0.05,
            min_absolute_log2_fold_change=0.5,
        ),
    )


def _export_and_validate_scale_demo(
    report_bundle,
    *,
    biological_output_dir: Path,
) -> tuple[BiologicalResultReportExportManifest, ScaleDemoValidation]:
    biological_manifest = write_biological_result_report_bundle(
        report_bundle,
        biological_output_dir,
    )
    atomic_write_text(
        biological_output_dir / "biological_report_manifest.json",
        biological_manifest.to_stable_json() + "\n",
    )
    layout_manifest = validate_workflow_artifact_manifest(biological_output_dir)
    lazy_graph = load_lazy_proteomics_evidence_graph(
        biological_output_dir / biological_manifest.artifacts.evidence_graph_nodes_tsv,
        biological_output_dir / biological_manifest.artifacts.evidence_graph_edges_tsv,
    )
    differential_row_count = _count_tsv_rows(
        biological_output_dir / biological_manifest.artifacts.differential_tsv
    )
    protein_card_row_count = _count_tsv_rows(
        biological_output_dir / biological_manifest.artifacts.protein_card_tsv
    )
    supported_claim_path = biological_manifest.artifacts.supported_claim_tsv
    if supported_claim_path is None:
        raise ValueError("scale demo biological report must produce supported claims")
    supported_claim_row_count = _count_tsv_rows(
        biological_output_dir / supported_claim_path
    )
    graph_node_row_count = _count_tsv_rows(
        biological_output_dir / biological_manifest.artifacts.evidence_graph_nodes_tsv
    )
    graph_edge_row_count = _count_tsv_rows(
        biological_output_dir / biological_manifest.artifacts.evidence_graph_edges_tsv
    )
    if graph_node_row_count != lazy_graph.summary.node_count:
        raise ValueError("lazy graph node summary drifted from exported node TSV rows")
    if graph_edge_row_count != lazy_graph.summary.edge_count:
        raise ValueError("lazy graph edge summary drifted from exported edge TSV rows")

    validation = ScaleDemoValidation(
        outputs_validated=True,
        manifest_artifact_count=len(layout_manifest.artifacts),
        differential_row_count=differential_row_count,
        protein_card_row_count=protein_card_row_count,
        supported_claim_row_count=supported_claim_row_count,
        graph_node_row_count=graph_node_row_count,
        graph_edge_row_count=graph_edge_row_count,
        note=(
            "validation confirmed the managed biological report manifest, loaded the "
            "exported evidence graph through the lazy graph artifact owner, and "
            "counted key review artifacts directly from written TSV outputs"
        ),
    )
    return biological_manifest, validation


def _write_scale_demo_artifacts(
    *,
    output_dir: Path,
    dataset: _GeneratedScaleDataset,
    biological_manifest: BiologicalResultReportExportManifest,
    stage_metrics: tuple[ScaleDemoStageMetric, ...],
    summary: ScaleDemoSummary,
    validation: ScaleDemoValidation,
) -> ScaleDemoArtifactPaths:
    summary_name = "scale_demo_summary.tsv"
    stage_metrics_name = "scale_demo_stage_metrics.tsv"
    validation_name = "scale_demo_validation.tsv"
    report_name = "scale_demo_report.json"
    artifacts = ScaleDemoArtifactPaths(
        feature_tsv=str(dataset.feature_path.relative_to(output_dir)),
        design_tsv=str(dataset.design_path.relative_to(output_dir)),
        proteins_fasta=str(dataset.proteins_fasta_path.relative_to(output_dir)),
        pathways_tsv=str(dataset.pathway_path.relative_to(output_dir)),
        summary_tsv=summary_name,
        stage_metrics_tsv=stage_metrics_name,
        validation_tsv=validation_name,
        report_json=report_name,
        biological_output_dir="biological_report",
        biological_report_manifest_json="biological_report/biological_report_manifest.json",
        biological_report_html=(
            "biological_report/" + biological_manifest.artifacts.report_html
        ),
        evidence_graph_nodes_tsv=(
            "biological_report/" + biological_manifest.artifacts.evidence_graph_nodes_tsv
        ),
        evidence_graph_edges_tsv=(
            "biological_report/" + biological_manifest.artifacts.evidence_graph_edges_tsv
        ),
        protein_cards_tsv=(
            "biological_report/" + biological_manifest.artifacts.protein_card_tsv
        ),
        supported_claims_tsv=(
            "biological_report/" + (biological_manifest.artifacts.supported_claim_tsv or "")
        ),
    )
    write_output_table_tsv(output_dir / summary_name, _render_scale_demo_summary(summary))
    write_output_table_tsv(
        output_dir / stage_metrics_name,
        _render_scale_demo_stage_metrics(stage_metrics),
    )
    write_output_table_tsv(
        output_dir / validation_name,
        _render_scale_demo_validation(validation),
    )
    return artifacts


def _build_scale_demo_samples(
    replicates_per_condition: int,
) -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []
    for condition, prefix in (("control", "c"), ("treated", "t")):
        for replicate_index in range(replicates_per_condition):
            sample_id = f"{prefix}{replicate_index + 1:02d}"
            rows.append(
                {
                    "sample_id": sample_id,
                    "condition": condition,
                    "replicate": str(replicate_index + 1),
                    "fraction": "1",
                    "spectra_file": f"{sample_id}.raw",
                    "identifications_file": f"{sample_id}.tsv",
                    "batch": "b1" if replicate_index < max(1, replicates_per_condition // 2) else "b2",
                    "instrument": "orbitrap",
                    "search_engine": "maxquant",
                }
            )
    return tuple(rows)


def _render_feature_rows(
    samples: tuple[dict[str, str], ...],
    proteins: tuple[str, ...],
    peptides_by_protein: dict[str, tuple[str, ...]],
) -> str:
    rows: list[dict[str, object]] = []
    feature_index = 1
    for protein_index, protein_ref in enumerate(proteins):
        for peptide_index, peptide_sequence in enumerate(peptides_by_protein[protein_ref]):
            for sample in samples:
                rows.append(
                    {
                        "sample_id": sample["sample_id"],
                        "feature_id": f"feature-{feature_index:07d}",
                        "peptide": peptide_sequence,
                        "proteins": protein_ref,
                        "intensity": round(
                            _scale_demo_intensity(
                                protein_index=protein_index,
                                peptide_index=peptide_index,
                                condition=sample["condition"],
                                replicate_index=int(sample["replicate"]) - 1,
                            ),
                            3,
                        ),
                        "charge": 2 + (peptide_index % 2),
                        "mz": round(400.0 + (protein_index * 0.11) + (peptide_index * 2.75), 4),
                        "retention_time_seconds": round(
                            600.0
                            + (protein_index * 1.2)
                            + (peptide_index * 7.5)
                            + (int(sample["replicate"]) * 1.5),
                            3,
                        ),
                        "missing_reason": "",
                    }
                )
                feature_index += 1
    return _dict_rows_to_tsv(rows)


def _render_design_rows(samples: tuple[dict[str, str], ...]) -> str:
    return _dict_rows_to_tsv([dict(row) for row in samples])


def _render_scale_demo_fasta(
    proteins: tuple[str, ...],
    peptides_by_protein: dict[str, tuple[str, ...]],
) -> str:
    lines: list[str] = []
    for protein_index, protein_ref in enumerate(proteins):
        lines.append(
            f">sp|{protein_ref}|SCALE_DEMO_{protein_index + 1:05d} "
            f"Synthetic scale demo protein {protein_index + 1} OS=Homo sapiens "
            f"GN=SD{protein_index + 1:05d}"
        )
        sequence = "M" + "GG".join(peptides_by_protein[protein_ref]) + "KK"
        lines.append(sequence)
    return "\n".join(lines) + "\n"


def _render_scale_demo_pathways(
    proteins: tuple[str, ...],
    pathway_count: int,
) -> str:
    rows: list[dict[str, object]] = []
    pathway_count = min(pathway_count, len(proteins))
    for protein_index, protein_ref in enumerate(proteins):
        regulation_family = ("up", "down", "stable")[protein_index % 3]
        pathway_index = protein_index % pathway_count
        rows.append(
            {
                "pathway_id": f"pw:{regulation_family}:{pathway_index + 1:03d}",
                "pathway_name": (
                    f"{regulation_family.capitalize()} pathway {pathway_index + 1:03d}"
                ),
                "protein_ref": protein_ref,
                "source_name": "scale_demo",
            }
        )
    return _dict_rows_to_tsv(rows)


def _build_scale_demo_peptide_sequence(
    protein_index: int,
    peptide_index: int,
) -> str:
    return _base20_peptide((protein_index * 97) + (peptide_index * 31) + 1, 8) + "K"


def _base20_peptide(seed: int, length: int) -> str:
    value = seed
    residues = ["A"] * length
    for index in range(length - 1, -1, -1):
        residues[index] = _AMINO_ACIDS[value % len(_AMINO_ACIDS)]
        value //= len(_AMINO_ACIDS)
    return "".join(residues)


def _scale_demo_intensity(
    *,
    protein_index: int,
    peptide_index: int,
    condition: str,
    replicate_index: int,
) -> float:
    base_intensity = 900.0 + (protein_index * 11.0) + (peptide_index * 55.0)
    peptide_factor = 1.0 + (peptide_index * 0.04)
    replicate_factor = 1.0 + (replicate_index * 0.02)
    if condition == "control":
        condition_factor = 1.0
    else:
        bucket = protein_index % 3
        condition_factor = {0: 4.0, 1: 0.35, 2: 1.05}[bucket]
    return base_intensity * peptide_factor * replicate_factor * condition_factor


def _measure_stage(function):
    tracemalloc.start()
    start = perf_counter()
    try:
        result = function()
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    return result, _StageMeasurement(
        elapsed_seconds=perf_counter() - start,
        peak_memory_mib=peak / (1024.0 * 1024.0),
    )


def _count_tsv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return sum(1 for _ in reader)


def _dict_rows_to_tsv(rows: list[dict[str, object]]) -> str:
    if not rows:
        return ""
    handle = StringIO()
    writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue()


def _render_scale_demo_summary(summary: ScaleDemoSummary) -> str:
    return _dict_rows_to_tsv(
        [
            {
                "elapsed_seconds": round(summary.elapsed_seconds, 6),
                "peak_memory_mib": round(summary.peak_memory_mib, 6),
                "sample_count": summary.sample_count,
                "protein_count": summary.protein_count,
                "peptide_count": summary.peptide_count,
                "generated_feature_row_count": summary.generated_feature_row_count,
                "parsed_feature_row_count": summary.parsed_feature_row_count,
                "quant_value_row_count": summary.quant_value_row_count,
                "graph_node_count": summary.graph_node_count,
                "graph_edge_count": summary.graph_edge_count,
                "differential_row_count": summary.differential_row_count,
                "protein_card_row_count": summary.protein_card_row_count,
                "exported_artifact_count": summary.exported_artifact_count,
                "outputs_validated": str(summary.outputs_validated).lower(),
            }
        ]
    )


def _render_scale_demo_stage_metrics(
    stage_metrics: tuple[ScaleDemoStageMetric, ...],
) -> str:
    return _dict_rows_to_tsv(
        [
            {
                "stage_name": metric.stage_name,
                "elapsed_seconds": round(metric.elapsed_seconds, 6),
                "peak_memory_mib": round(metric.peak_memory_mib, 6),
                "primary_row_count": metric.primary_row_count,
                "note": metric.note,
            }
            for metric in stage_metrics
        ]
    )


def _render_scale_demo_validation(validation: ScaleDemoValidation) -> str:
    return _dict_rows_to_tsv(
        [
            {
                "outputs_validated": str(validation.outputs_validated).lower(),
                "manifest_artifact_count": validation.manifest_artifact_count,
                "differential_row_count": validation.differential_row_count,
                "protein_card_row_count": validation.protein_card_row_count,
                "supported_claim_row_count": validation.supported_claim_row_count,
                "graph_node_row_count": validation.graph_node_row_count,
                "graph_edge_row_count": validation.graph_edge_row_count,
                "note": validation.note,
            }
        ]
    )


__all__ = [
    "ScaleDemoArtifactPaths",
    "ScaleDemoConfig",
    "ScaleDemoReport",
    "ScaleDemoStageMetric",
    "ScaleDemoSummary",
    "ScaleDemoValidation",
    "render_scale_demo_stage_metrics_tsv",
    "render_scale_demo_summary_tsv",
    "render_scale_demo_validation_tsv",
    "run_scale_demo",
]
