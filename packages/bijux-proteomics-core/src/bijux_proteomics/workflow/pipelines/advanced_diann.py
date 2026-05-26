# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Advanced DIA-NN workflow execution over governed review surfaces."""

from __future__ import annotations

from bijux_proteomics._atomic_files import atomic_write_text
from bijux_proteomics._output_tables import write_output_table_tsv

import csv
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics.domain.reason_codes import (
    ReasonCodeCategory,
    require_registered_reason_codes,
)
from bijux_proteomics.dia import (
    DiaPeptideRollupMethod,
    DiaProteinMatrixTargetKind,
    DiaProteinRollupMethod,
    DiaSharedPeptidePolicy,
)
from bijux_proteomics.io import (
    DiaFragmentCoelutionReport,
    extract_mzml_dia_fragment_trace_coelution,
    render_dia_fragment_coelution_fragments_tsv,
    render_dia_fragment_coelution_runs_tsv,
)
from bijux_proteomics.quantification import NormalizationMethod
from bijux_proteomics.review import (
    BeliefAuditReport,
    EvidenceGraphFinalResultEntry,
    EvidenceGraphFinalResultReport,
    FinalClaimEvidenceTier,
    ProteomicsEvidenceGraph,
    ProteomicsEvidenceNodeKind,
    build_belief_audit_report_from_artifacts,
    build_evidence_graph_final_result_table,
    render_belief_audit_summary_tsv,
    render_belief_audit_tsv,
    render_evidence_graph_final_results_tsv,
)
from bijux_proteomics.review.evidence_graph.evidence_graph_confidence import EvidenceGraphConfidenceTier
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.workflow.reports.biological_reporting import (
    BiologicalResultSelectionPolicy,
    VolcanoReviewPolicy,
)
from bijux_proteomics.workflow.pipelines.diann_biological_workflow import (
    DiannBiologicalWorkflowBundle,
    DiannBiologicalWorkflowExportManifest,
    build_diann_biological_workflow_bundle,
    write_diann_biological_workflow_bundle,
)
from bijux_proteomics.workflow.result_types import (
    BiologyResult,
    artifact_name_map,
    build_rejected_evidence_entries_from_table_rows,
    build_result_warning,
)
from bijux_proteomics.workflow.exports.artifact_layout import synchronize_workflow_artifact_layout
from bijux_proteomics_foundation import JsonModel


class AdvancedDiannWorkflowConfig(JsonModel):
    """Config for the advanced DIA-NN workflow owner."""

    model_config = ConfigDict(extra="forbid")

    result_tsv_path: Path
    design_tsv_path: Path
    proteins_fasta_path: Path
    output_dir: Path
    protocol_context_tsv_path: Path | None = None
    config_path: Path | None = None
    annotation_tsv_path: Path | None = None
    context_annotation_tsv_path: Path | None = None
    go_annotation_tsv_path: Path | None = None
    pathway_membership_tsv_path: Path | None = None
    complex_membership_tsv_path: Path | None = None
    include_decoys: bool = False
    max_q_value: float = Field(default=0.01, ge=0.0, le=1.0)
    peptide_rollup_method: DiaPeptideRollupMethod = DiaPeptideRollupMethod.MAX
    target_kind: DiaProteinMatrixTargetKind = DiaProteinMatrixTargetKind.PROTEIN_GROUP
    shared_peptide_policy: DiaSharedPeptidePolicy = DiaSharedPeptidePolicy.INCLUDE
    protein_rollup_method: DiaProteinRollupMethod = DiaProteinRollupMethod.SUM
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN
    condition_a: str | None = None
    condition_b: str | None = None
    selection_policy: BiologicalResultSelectionPolicy | None = None
    volcano_policy: VolcanoReviewPolicy | None = None
    fragment_mzml_paths: tuple[Path, ...] = Field(default_factory=tuple)
    fragment_target_tsv_path: Path | None = None
    fragment_tolerance_da: float | None = Field(default=None, gt=0.0)
    fragment_tolerance_ppm: float | None = Field(default=10.0, gt=0.0)
    fragment_min_peak_height: float = Field(default=1.0, gt=0.0)
    fragment_apex_tolerance_seconds: float = Field(default=5.0, gt=0.0)
    fragment_min_correlation: float = Field(default=0.8, ge=-1.0, le=1.0)
    fragment_min_passing_fragment_count: int = Field(default=2, ge=1)


class AdvancedDiannWorkflowSummary(JsonModel):
    """Compact summary over one advanced DIA-NN workflow run."""

    model_config = ConfigDict(extra="forbid")

    imported_precursor_count: int = Field(..., ge=0)
    rejected_evidence_count: int = Field(..., ge=0)
    accepted_protein_count: int = Field(..., ge=0)
    downgraded_protein_count: int = Field(..., ge=0)
    supported_claim_count: int = Field(..., ge=0)
    rejected_claim_count: int = Field(..., ge=0)
    belief_audit_entry_count: int = Field(..., ge=0)
    fragment_coelution_run_count: int = Field(..., ge=0)
    fragment_coelution_fragment_count: int = Field(..., ge=0)


class AdvancedDiannWorkflowArtifactPaths(JsonModel):
    """Advanced DIA-NN artifact paths written into the output directory."""

    model_config = ConfigDict(extra="forbid")

    summary_tsv: str = Field(..., min_length=1)
    diann_workflow_manifest_json: str = Field(..., min_length=1)
    biological_report_manifest_json: str = Field(..., min_length=1)
    rejected_evidence_tsv: str = Field(..., min_length=1)
    import_rejected_evidence_tsv: str = Field(..., min_length=1)
    supported_claim_tsv: str | None = None
    rejected_claim_tsv: str | None = None
    graph_final_results_tsv: str = Field(..., min_length=1)
    accepted_proteins_tsv: str = Field(..., min_length=1)
    downgraded_proteins_tsv: str = Field(..., min_length=1)
    belief_audit_summary_tsv: str = Field(..., min_length=1)
    belief_audit_tsv: str = Field(..., min_length=1)
    fragment_coelution_runs_tsv: str | None = None
    fragment_coelution_fragments_tsv: str | None = None


class AdvancedDiannWorkflowManifest(JsonModel):
    """Stable manifest over one advanced DIA-NN workflow output directory."""

    model_config = ConfigDict(extra="forbid")

    summary: AdvancedDiannWorkflowSummary
    artifacts: AdvancedDiannWorkflowArtifactPaths
    diann_workflow_manifest: DiannBiologicalWorkflowExportManifest
    note: str = Field(..., min_length=1)


class AdvancedDiannProteinDecisionEntry(JsonModel):
    """One protein-level advanced DIA-NN decision row."""

    model_config = ConfigDict(extra="forbid")

    protein_group_id: str = Field(..., min_length=1)
    representative_protein_ref: str = Field(..., min_length=1)
    claim_node_ref: str = Field(..., min_length=1)
    claim_state: str | None = None
    evidence_tier: FinalClaimEvidenceTier
    confidence_tier: EvidenceGraphConfidenceTier
    downgrade_reasons: tuple[str, ...] = Field(default_factory=tuple)
    source_row_refs: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("downgrade_reasons")
    @classmethod
    def _validate_downgrade_reasons(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return require_registered_reason_codes(
            value,
            ReasonCodeCategory.CLAIM_DOWNGRADE,
        )


class AdvancedDiannWorkflowReport(BiologyResult):
    """Advanced DIA-NN workflow report with exported scientific review outputs."""

    model_config = ConfigDict(extra="forbid")

    diann_workflow: DiannBiologicalWorkflowBundle
    diann_workflow_manifest: DiannBiologicalWorkflowExportManifest
    graph_final_results: EvidenceGraphFinalResultReport
    accepted_protein_decisions: tuple[AdvancedDiannProteinDecisionEntry, ...] = Field(
        default_factory=tuple
    )
    downgraded_protein_decisions: tuple[AdvancedDiannProteinDecisionEntry, ...] = Field(
        default_factory=tuple
    )
    belief_audit: BeliefAuditReport
    fragment_coelution_report: DiaFragmentCoelutionReport | None = None
    summary: AdvancedDiannWorkflowSummary
    manifest: AdvancedDiannWorkflowManifest
    note: str = Field(..., min_length=1)


def run_advanced_diann_workflow(
    config: AdvancedDiannWorkflowConfig,
) -> AdvancedDiannWorkflowReport:
    """Run the advanced DIA-NN workflow and write one durable review directory."""

    _validate_fragment_inputs(config)
    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    design_entries = tuple(
        parse_experimental_design_table(config.design_tsv_path).accepted_entries
    )

    base_report = build_diann_biological_workflow_bundle(
        config.result_tsv_path,
        design_entries,
        proteins_fasta_path=config.proteins_fasta_path,
        protocol_context_tsv_path=config.protocol_context_tsv_path,
        config_path=config.config_path,
        include_decoys=config.include_decoys,
        max_q_value=config.max_q_value,
        peptide_rollup_method=config.peptide_rollup_method,
        target_kind=config.target_kind,
        shared_peptide_policy=config.shared_peptide_policy,
        protein_rollup_method=config.protein_rollup_method,
        normalization_method=config.normalization_method,
        condition_a=config.condition_a,
        condition_b=config.condition_b,
        annotation_tsv_path=config.annotation_tsv_path,
        context_annotation_tsv_path=config.context_annotation_tsv_path,
        go_annotation_tsv_path=config.go_annotation_tsv_path,
        pathway_membership_tsv_path=config.pathway_membership_tsv_path,
        complex_membership_tsv_path=config.complex_membership_tsv_path,
        selection_policy=config.selection_policy,
        volcano_policy=config.volcano_policy,
    )
    diann_manifest = write_diann_biological_workflow_bundle(base_report, output_dir)
    diann_manifest_path = output_dir / "diann_biological_report_manifest.json"
    atomic_write_text(diann_manifest_path, diann_manifest.to_stable_json() + "\n")

    graph_final_results = build_evidence_graph_final_result_table(
        base_report.biological_report.graph_report.graph
    )
    accepted_protein_entries = _accepted_protein_entries(
        graph=base_report.biological_report.graph_report.graph,
        report=graph_final_results,
    )
    downgraded_protein_entries = _downgraded_protein_entries(
        graph=base_report.biological_report.graph_report.graph,
        report=graph_final_results,
    )

    final_results_name = "advanced_diann_graph_final_results.tsv"
    accepted_name = "advanced_diann_accepted_proteins.tsv"
    downgraded_name = "advanced_diann_downgraded_proteins.tsv"
    belief_audit_summary_name = "advanced_diann_belief_audit_summary.tsv"
    belief_audit_name = "advanced_diann_belief_audit.tsv"
    summary_name = "advanced_diann_summary.tsv"

    write_output_table_tsv((output_dir / final_results_name), render_evidence_graph_final_results_tsv(graph_final_results))
    write_output_table_tsv(
        output_dir / accepted_name,
        render_advanced_diann_protein_decisions_tsv(
            _build_protein_decisions(
                graph=base_report.biological_report.graph_report.graph,
                entries=accepted_protein_entries,
            )
        ),
    )
    write_output_table_tsv(
        output_dir / downgraded_name,
        render_advanced_diann_protein_decisions_tsv(
            _build_protein_decisions(
                graph=base_report.biological_report.graph_report.graph,
                entries=downgraded_protein_entries,
            )
        ),
    )

    belief_audit = build_belief_audit_report_from_artifacts(
        biological_report_dir=output_dir,
    )
    write_output_table_tsv((output_dir / belief_audit_summary_name), render_belief_audit_summary_tsv(belief_audit))
    write_output_table_tsv((output_dir / belief_audit_name), render_belief_audit_tsv(belief_audit))

    fragment_coelution_report = _build_fragment_coelution_report(config)
    fragment_runs_name = None
    fragment_fragments_name = None
    if fragment_coelution_report is not None:
        fragment_runs_name = "advanced_diann_fragment_coelution_runs.tsv"
        fragment_fragments_name = "advanced_diann_fragment_coelution_fragments.tsv"
        write_output_table_tsv((output_dir / fragment_runs_name), render_dia_fragment_coelution_runs_tsv(fragment_coelution_report))
        write_output_table_tsv((output_dir / fragment_fragments_name), render_dia_fragment_coelution_fragments_tsv(fragment_coelution_report))

    summary = AdvancedDiannWorkflowSummary(
        imported_precursor_count=base_report.summary.imported_precursor_count,
        rejected_evidence_count=base_report.summary.rejected_evidence_count,
        accepted_protein_count=len(accepted_protein_entries),
        downgraded_protein_count=len(downgraded_protein_entries),
        supported_claim_count=(
            0
            if base_report.biological_report.claim_validation_report is None
            else base_report.biological_report.claim_validation_report.summary.supported_claim_count
        ),
        rejected_claim_count=(
            0
            if base_report.biological_report.claim_validation_report is None
            else base_report.biological_report.claim_validation_report.summary.rejected_claim_count
        ),
        belief_audit_entry_count=belief_audit.summary.entry_count,
        fragment_coelution_run_count=(
            0 if fragment_coelution_report is None else len(fragment_coelution_report.run_entries)
        ),
        fragment_coelution_fragment_count=(
            0
            if fragment_coelution_report is None
            else len(fragment_coelution_report.fragment_entries)
        ),
    )
    write_output_table_tsv((output_dir / summary_name), render_advanced_diann_workflow_summary_tsv(summary))

    manifest = AdvancedDiannWorkflowManifest(
        summary=summary,
        artifacts=AdvancedDiannWorkflowArtifactPaths(
            summary_tsv=summary_name,
            diann_workflow_manifest_json=diann_manifest_path.name,
            biological_report_manifest_json=diann_manifest.artifacts.biological_manifest_json,
            rejected_evidence_tsv=diann_manifest.artifacts.rejected_evidence_tsv,
            import_rejected_evidence_tsv=diann_manifest.artifacts.import_rejected_evidence_tsv,
            supported_claim_tsv=diann_manifest.biological_report_manifest.artifacts.supported_claim_tsv,
            rejected_claim_tsv=diann_manifest.biological_report_manifest.artifacts.rejected_claim_tsv,
            graph_final_results_tsv=final_results_name,
            accepted_proteins_tsv=accepted_name,
            downgraded_proteins_tsv=downgraded_name,
            belief_audit_summary_tsv=belief_audit_summary_name,
            belief_audit_tsv=belief_audit_name,
            fragment_coelution_runs_tsv=fragment_runs_name,
            fragment_coelution_fragments_tsv=fragment_fragments_name,
        ),
        diann_workflow_manifest=diann_manifest,
        note=(
            "advanced dia-nn workflow output preserves governed import, matrices, qc, "
            "claims, graph-backed protein decisions, optional fragment coelution, "
            "and belief audit surfaces in one directory"
        ),
    )
    manifest_path = output_dir / "advanced_diann_workflow_manifest.json"
    atomic_write_text(manifest_path, manifest.to_stable_json() + "\n")
    synchronize_workflow_artifact_layout(
        output_dir,
        producer_function="run_advanced_diann_workflow",
    )

    return AdvancedDiannWorkflowReport(
        diann_workflow=base_report,
        diann_workflow_manifest=diann_manifest,
        graph_final_results=graph_final_results,
        accepted_protein_decisions=_build_protein_decisions(
            graph=base_report.biological_report.graph_report.graph,
            entries=accepted_protein_entries,
        ),
        downgraded_protein_decisions=_build_protein_decisions(
            graph=base_report.biological_report.graph_report.graph,
            entries=downgraded_protein_entries,
        ),
        belief_audit=belief_audit,
        fragment_coelution_report=fragment_coelution_report,
        summary=summary,
        manifest=manifest,
        artifacts=artifact_name_map(manifest.artifacts),
        warnings=_build_advanced_diann_warnings(
            report=base_report,
            summary=summary,
            manifest=manifest,
        ),
        rejected_evidence=_build_advanced_diann_rejected_evidence(
            report=base_report,
            manifest=manifest,
        ),
        note=(
            "advanced dia-nn workflow composes the governed dia import, protein-level "
            "biology, graph-backed downgrade review, optional fragment coelution, "
            "and belief audit on one owned workflow surface"
        ),
    )


def render_advanced_diann_workflow_summary_tsv(
    summary: AdvancedDiannWorkflowSummary,
) -> str:
    """Render one advanced DIA-NN workflow summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field_name, value in (
        ("imported_precursor_count", summary.imported_precursor_count),
        ("rejected_evidence_count", summary.rejected_evidence_count),
        ("accepted_protein_count", summary.accepted_protein_count),
        ("downgraded_protein_count", summary.downgraded_protein_count),
        ("supported_claim_count", summary.supported_claim_count),
        ("rejected_claim_count", summary.rejected_claim_count),
        ("belief_audit_entry_count", summary.belief_audit_entry_count),
        ("fragment_coelution_run_count", summary.fragment_coelution_run_count),
        ("fragment_coelution_fragment_count", summary.fragment_coelution_fragment_count),
    ):
        writer.writerow((field_name, value))
    return handle.getvalue()


def _build_advanced_diann_warnings(
    *,
    report: DiannBiologicalWorkflowBundle,
    summary: AdvancedDiannWorkflowSummary,
    manifest: AdvancedDiannWorkflowManifest,
) -> tuple:
    warnings = []
    if summary.rejected_evidence_count > 0:
        warnings.append(
            build_result_warning(
                warning_id="advanced_diann:rejected_evidence",
                warning_code="rejected_evidence_present",
                source_surface="advanced_diann_workflow",
                message=(
                    f"DIA-NN import rejected {summary.rejected_evidence_count} evidence rows "
                    "before downstream review"
                ),
                related_artifact=manifest.artifacts.rejected_evidence_tsv,
            )
        )
    if report.summary.flagged_run_count > 0:
        warnings.append(
            build_result_warning(
                warning_id="advanced_diann:flagged_runs",
                warning_code="flagged_run_qc",
                source_surface="advanced_diann_workflow",
                message=(
                    f"DIA-NN workflow flagged {report.summary.flagged_run_count} runs during run QC"
                ),
            )
        )
    if summary.downgraded_protein_count > 0:
        warnings.append(
            build_result_warning(
                warning_id="advanced_diann:downgraded_proteins",
                warning_code="downgraded_protein_present",
                source_surface="advanced_diann_workflow",
                message=(
                    f"advanced DIA-NN downgraded {summary.downgraded_protein_count} proteins "
                    "after evidence-graph review"
                ),
                related_artifact=manifest.artifacts.downgraded_proteins_tsv,
            )
        )
    return tuple(warnings)


def _build_advanced_diann_rejected_evidence(
    *,
    report: DiannBiologicalWorkflowBundle,
    manifest: AdvancedDiannWorkflowManifest,
) -> tuple:
    return build_rejected_evidence_entries_from_table_rows(
        report.import_report.rejected_evidence_rows,
        source_surface="diann_import",
        related_artifact=manifest.artifacts.rejected_evidence_tsv,
    )


def render_advanced_diann_protein_decisions_tsv(
    entries: tuple[AdvancedDiannProteinDecisionEntry, ...],
) -> str:
    """Render accepted or downgraded protein decisions as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "protein_group_id",
            "representative_protein_ref",
            "claim_node_ref",
            "claim_state",
            "evidence_tier",
            "confidence_tier",
            "downgrade_reasons",
            "source_row_refs",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.protein_group_id,
                entry.representative_protein_ref,
                entry.claim_node_ref,
                "" if entry.claim_state is None else entry.claim_state,
                entry.evidence_tier.value,
                entry.confidence_tier.value,
                ";".join(entry.downgrade_reasons),
                ";".join(entry.source_row_refs),
            )
        )
    return handle.getvalue()


def _validate_fragment_inputs(config: AdvancedDiannWorkflowConfig) -> None:
    if config.fragment_mzml_paths and config.fragment_target_tsv_path is None:
        raise ValueError("fragment_target_tsv_path is required when fragment_mzml_paths are provided")
    if not config.fragment_mzml_paths and config.fragment_target_tsv_path is not None:
        raise ValueError("fragment_mzml_paths are required when fragment_target_tsv_path is provided")


def _build_fragment_coelution_report(
    config: AdvancedDiannWorkflowConfig,
) -> DiaFragmentCoelutionReport | None:
    if not config.fragment_mzml_paths:
        return None
    return extract_mzml_dia_fragment_trace_coelution(
        config.fragment_mzml_paths,
        config.fragment_target_tsv_path,
        tolerance_da=config.fragment_tolerance_da,
        tolerance_ppm=config.fragment_tolerance_ppm,
        min_peak_height=config.fragment_min_peak_height,
        apex_tolerance_seconds=config.fragment_apex_tolerance_seconds,
        min_correlation=config.fragment_min_correlation,
        min_passing_fragment_count=config.fragment_min_passing_fragment_count,
    )


def _accepted_protein_entries(
    *,
    graph: ProteomicsEvidenceGraph,
    report: EvidenceGraphFinalResultReport,
) -> tuple[EvidenceGraphFinalResultEntry, ...]:
    return tuple(
        entry
        for entry in report.entries
        if entry.subject_node_kind is ProteomicsEvidenceNodeKind.PROTEIN
        and _is_changed_protein_entry(graph, entry)
        and not _is_downgraded_entry(entry)
    )


def _downgraded_protein_entries(
    *,
    graph: ProteomicsEvidenceGraph,
    report: EvidenceGraphFinalResultReport,
) -> tuple[EvidenceGraphFinalResultEntry, ...]:
    return tuple(
        entry
        for entry in report.entries
        if entry.subject_node_kind is ProteomicsEvidenceNodeKind.PROTEIN
        and _is_downgraded_entry(entry)
    )


def _is_changed_protein_entry(
    graph: ProteomicsEvidenceGraph,
    entry: EvidenceGraphFinalResultEntry,
) -> bool:
    if entry.subject_node_kind is not ProteomicsEvidenceNodeKind.PROTEIN:
        return False
    claim_state = _claim_state_by_node_id(graph, entry.claim_node_id)
    return claim_state not in {None, "", "unchanged"}


def _is_downgraded_entry(entry: EvidenceGraphFinalResultEntry) -> bool:
    return bool(entry.downgrade_reasons) or entry.evidence_tier in {
        FinalClaimEvidenceTier.WEAK,
        FinalClaimEvidenceTier.AMBIGUOUS,
    } or entry.confidence_tier not in {
        EvidenceGraphConfidenceTier.HIGH,
        EvidenceGraphConfidenceTier.MODERATE,
    }


def _claim_state_by_node_id(graph: ProteomicsEvidenceGraph, node_id: str) -> str | None:
    for node in graph.nodes:
        if node.node_id == node_id:
            return node.claim_state
    return None


def _build_protein_decisions(
    *,
    graph: ProteomicsEvidenceGraph,
    entries: tuple[EvidenceGraphFinalResultEntry, ...],
) -> tuple[AdvancedDiannProteinDecisionEntry, ...]:
    nodes_by_id = {node.node_id: node for node in graph.nodes}
    decisions = []
    for entry in entries:
        protein_node = nodes_by_id[entry.subject_node_id]
        decisions.append(
            AdvancedDiannProteinDecisionEntry(
                protein_group_id=entry.subject_node_ref,
                representative_protein_ref=protein_node.label or entry.subject_node_ref,
                claim_node_ref=entry.claim_node_ref,
                claim_state=_claim_state_by_node_id(graph, entry.claim_node_id),
                evidence_tier=entry.evidence_tier,
                confidence_tier=entry.confidence_tier,
                downgrade_reasons=tuple(reason.value for reason in entry.downgrade_reasons),
                source_row_refs=entry.source_row_refs,
            )
        )
    return tuple(
        sorted(
            decisions,
            key=lambda entry: (entry.protein_group_id, entry.representative_protein_ref),
        )
    )


__all__ = [
    "AdvancedDiannWorkflowArtifactPaths",
    "AdvancedDiannWorkflowConfig",
    "AdvancedDiannWorkflowManifest",
    "AdvancedDiannProteinDecisionEntry",
    "AdvancedDiannWorkflowReport",
    "AdvancedDiannWorkflowSummary",
    "render_advanced_diann_protein_decisions_tsv",
    "render_advanced_diann_workflow_summary_tsv",
    "run_advanced_diann_workflow",
]
