# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned DDA search-result-to-biology workflow bundles."""

from __future__ import annotations

from bijux_proteomics._atomic_files import atomic_write_text
from bijux_proteomics._output_tables import write_output_table_tsv

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import (
    ParsimonyReviewReport,
    ParsimonyVariant,
    PsmRecord,
    RejectedPsmRow,
    SearchAdapterKind,
    TargetDecoyContaminantClass,
    TargetDecoyLabel,
    build_parsimony_review_report,
    export_psm_tsv,
    load_generic_psm_table_mapping,
    normalize_search_results_with_adapter,
    render_parsimony_review_ambiguities_tsv,
    render_parsimony_review_proteins_tsv,
    render_parsimony_review_summary_tsv,
    select_best_psm_per_spectrum,
)
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    LabelFreeQuantTable,
    NormalizationMethod,
    ProteinLfqReport,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
    QuantValue,
    build_protein_lfq_report_from_psms,
    render_protein_lfq_matrix_tsv,
    render_protein_lfq_missingness_tsv,
    render_protein_lfq_missingness_mask_tsv,
    render_protein_lfq_pairwise_ratios_tsv,
    render_protein_lfq_summary_tsv,
)
from bijux_proteomics.study import ExperimentDesign, coerce_experiment_design
from bijux_proteomics.workflow.reports.biological_reporting import (
    BiologicalResultReportBundle,
    BiologicalResultReportExportManifest,
    BiologicalResultSelectionPolicy,
    VolcanoReviewPolicy,
    build_biological_result_report_bundle_from_quant_table,
    write_biological_result_report_bundle,
)
from bijux_proteomics.workflow.exports.artifact_layout import synchronize_workflow_artifact_layout
from bijux_proteomics.workflow.result_types import (
    build_rejected_evidence_entries_from_issue_rows,
    build_rejected_evidence_entry,
    render_result_rejected_evidence_tsv,
)
from bijux_proteomics_foundation import JsonModel


class DdaPsmAcceptanceReason(StrEnum):
    """Stable reasons why one normalized DDA PSM cannot enter biology workflows."""

    MISSING_Q_VALUE = "missing_q_value"
    Q_VALUE_ABOVE_THRESHOLD = "q_value_above_threshold"
    DECOY = "decoy"
    CONTAMINANT = "contaminant"
    MISSING_RUN_ID = "missing_run_id"
    MISSING_INTENSITY = "missing_intensity"
    MISSING_PROTEIN_REFS = "missing_protein_refs"


class DdaPsmAcceptancePolicy(JsonModel):
    """Explicit acceptance policy for DDA search results entering quantification."""

    model_config = ConfigDict(extra="forbid")

    max_q_value: float = Field(default=0.01, ge=0.0, le=1.0)
    exclude_decoys: bool = True
    exclude_contaminants: bool = True
    require_run_id: bool = True
    require_intensity: bool = True
    require_protein_refs: bool = True


class DdaFilteredPsmEntry(JsonModel):
    """One normalized DDA PSM filtered before protein-level biology reporting."""

    model_config = ConfigDict(extra="forbid")

    run_id: str | None = None
    spectrum_id: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    score: float
    intensity: float | None = Field(default=None, ge=0.0)
    q_value: float | None = Field(default=None, ge=0.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel
    contaminant_flag: bool
    target_decoy_contaminant_class: TargetDecoyContaminantClass
    reasons: tuple[DdaPsmAcceptanceReason, ...] = Field(default_factory=tuple)


class DdaBiologicalWorkflowSummary(JsonModel):
    """Compact summary over one DDA search-result-to-biology workflow bundle."""

    model_config = ConfigDict(extra="forbid")

    adapter_kind: SearchAdapterKind
    imported_psm_row_count: int = Field(..., ge=0)
    parse_rejected_row_count: int = Field(..., ge=0)
    normalized_psm_count: int = Field(..., ge=0)
    best_spectrum_psm_count: int = Field(..., ge=0)
    accepted_psm_count: int = Field(..., ge=0)
    filtered_psm_count: int = Field(..., ge=0)
    inferred_protein_count: int = Field(..., ge=0)
    quantified_protein_count: int = Field(..., ge=0)
    significant_protein_count: int = Field(..., ge=0)
    source_protein_group_count: int = Field(..., ge=0)
    protein_group_discrepancy_count: int = Field(..., ge=0)
    source_only_protein_group_count: int = Field(..., ge=0)
    workflow_only_protein_group_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)


class DdaProteinGroupDiscrepancyStatus(StrEnum):
    """Stable relationship between a source protein table and the workflow output."""

    SHARED = "shared"
    SOURCE_ONLY = "source_only"
    WORKFLOW_ONLY = "workflow_only"


class DdaProteinGroupDiscrepancyEntry(JsonModel):
    """One protein-group discrepancy row against an optional source protein table."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    status: DdaProteinGroupDiscrepancyStatus
    source_table_present: bool
    inferred_by_workflow: bool
    quantified_by_workflow: bool
    significant_in_workflow: bool


class DdaBiologicalWorkflowBundle(JsonModel):
    """Owned DDA bundle from normalized search results to biological reporting."""

    model_config = ConfigDict(extra="forbid")

    source_columns: tuple[str, ...] = Field(default_factory=tuple)
    acceptance_policy: DdaPsmAcceptancePolicy
    parse_rejected_rows: tuple[RejectedPsmRow, ...] = Field(default_factory=tuple)
    accepted_psms: tuple[PsmRecord, ...] = Field(default_factory=tuple)
    filtered_psms: tuple[DdaFilteredPsmEntry, ...] = Field(default_factory=tuple)
    protein_group_discrepancies: tuple[DdaProteinGroupDiscrepancyEntry, ...] = Field(
        default_factory=tuple
    )
    parsimony_review: ParsimonyReviewReport
    protein_lfq_report: ProteinLfqReport
    biological_report: BiologicalResultReportBundle
    summary: DdaBiologicalWorkflowSummary
    note: str = Field(..., min_length=1)


class DdaBiologicalWorkflowArtifactPaths(JsonModel):
    """Relative artifact paths written into one DDA biology output directory."""

    model_config = ConfigDict(extra="forbid")

    summary_tsv: str = Field(..., min_length=1)
    accepted_psm_tsv: str = Field(..., min_length=1)
    filtered_psm_tsv: str = Field(..., min_length=1)
    parse_rejected_tsv: str = Field(..., min_length=1)
    rejected_evidence_tsv: str = Field(..., min_length=1)
    parsimony_summary_tsv: str = Field(..., min_length=1)
    parsimony_proteins_tsv: str = Field(..., min_length=1)
    parsimony_ambiguities_tsv: str = Field(..., min_length=1)
    protein_lfq_summary_tsv: str = Field(..., min_length=1)
    protein_lfq_matrix_tsv: str = Field(..., min_length=1)
    protein_lfq_pairwise_tsv: str = Field(..., min_length=1)
    protein_lfq_missingness_tsv: str = Field(..., min_length=1)
    protein_lfq_missingness_mask_tsv: str = Field(..., min_length=1)
    protein_group_discrepancy_tsv: str | None = None
    biological_manifest_json: str = Field(..., min_length=1)
    report_html: str = Field(..., min_length=1)


class DdaBiologicalWorkflowExportManifest(JsonModel):
    """Stable manifest over one exported DDA search-result-to-biology directory."""

    model_config = ConfigDict(extra="forbid")

    summary: DdaBiologicalWorkflowSummary
    artifacts: DdaBiologicalWorkflowArtifactPaths
    biological_report_manifest: BiologicalResultReportExportManifest
    note: str = Field(..., min_length=1)


def build_dda_biological_workflow_bundle(
    search_result_tsv_path: Path,
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    proteins_fasta_path: Path,
    protocol_context_tsv_path: Path | None = None,
    adapter_kind: SearchAdapterKind = SearchAdapterKind.GENERIC,
    generic_mapping_path: Path | None = None,
    dialect_id: str = "default",
    acceptance_policy: DdaPsmAcceptancePolicy | None = None,
    parsimony_variant: ParsimonyVariant = ParsimonyVariant.GREEDY_COVERAGE,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    top_n: int = 3,
    minimum_shared_peptides: int = 1,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    source_protein_tsv_path: Path | None = None,
    annotation_tsv_path: Path | None = None,
    go_annotation_tsv_path: Path | None = None,
    pathway_membership_tsv_path: Path | None = None,
    complex_membership_tsv_path: Path | None = None,
    selection_policy: BiologicalResultSelectionPolicy | None = None,
    volcano_policy: VolcanoReviewPolicy | None = None,
) -> DdaBiologicalWorkflowBundle:
    """Build a governed DDA search-result-to-biology workflow bundle."""

    experiment_design = coerce_experiment_design(design_entries)
    active_policy = acceptance_policy or DdaPsmAcceptancePolicy()
    normalization = _normalize_search_results(
        source_path=search_result_tsv_path,
        adapter_kind=adapter_kind,
        dialect_id=dialect_id,
        generic_mapping_path=generic_mapping_path,
    )
    best_spectrum_psms = tuple(
        select_best_psm_per_spectrum(normalization.normalized_records)
    )
    accepted_psms, filtered_psms = _filter_psms_for_biological_workflow(
        best_spectrum_psms,
        policy=active_policy,
    )
    if not accepted_psms:
        raise ValueError(
            "DDA biology workflow did not retain any PSMs after acceptance filtering"
        )
    parsimony_review = build_parsimony_review_report(
        accepted_psms,
        variant=parsimony_variant,
    )
    protein_lfq_report = build_protein_lfq_report_from_psms(
        accepted_psms,
        aggregation_method=aggregation_method,
        minimum_shared_peptides=minimum_shared_peptides,
        top_n=top_n,
    )
    if not protein_lfq_report.rows:
        raise ValueError("DDA biology workflow did not quantify any proteins")
    quant_table = build_label_free_quant_table_from_protein_lfq_report(
        protein_lfq_report
    )
    biological_report = build_biological_result_report_bundle_from_quant_table(
        quant_table,
        experiment_design,
        proteins_fasta_path=proteins_fasta_path,
        protocol_context_tsv_path=protocol_context_tsv_path,
        annotation_tsv_path=annotation_tsv_path,
        go_annotation_tsv_path=go_annotation_tsv_path,
        pathway_membership_tsv_path=pathway_membership_tsv_path,
        complex_membership_tsv_path=complex_membership_tsv_path,
        normalization_method=normalization_method,
        condition_a=condition_a,
        condition_b=condition_b,
        selection_policy=selection_policy,
        volcano_policy=volcano_policy,
    )
    protein_group_discrepancies = _build_protein_group_discrepancies(
        source_protein_tsv_path=source_protein_tsv_path,
        parsimony_review=parsimony_review,
        protein_lfq_report=protein_lfq_report,
        biological_report=biological_report,
    )
    return DdaBiologicalWorkflowBundle(
        source_columns=normalization.source_columns,
        acceptance_policy=active_policy,
        parse_rejected_rows=normalization.parse_report.rejected_rows,
        accepted_psms=accepted_psms,
        filtered_psms=filtered_psms,
        protein_group_discrepancies=protein_group_discrepancies,
        parsimony_review=parsimony_review,
        protein_lfq_report=protein_lfq_report,
        biological_report=biological_report,
        summary=DdaBiologicalWorkflowSummary(
            adapter_kind=adapter_kind,
            imported_psm_row_count=normalization.parse_report.total_rows,
            parse_rejected_row_count=len(normalization.parse_report.rejected_rows),
            normalized_psm_count=len(normalization.normalized_records),
            best_spectrum_psm_count=len(best_spectrum_psms),
            accepted_psm_count=len(accepted_psms),
            filtered_psm_count=len(filtered_psms),
            inferred_protein_count=parsimony_review.summary.selected_protein_count,
            quantified_protein_count=len(protein_lfq_report.rows),
            significant_protein_count=(
                biological_report.summary.significant_protein_count
            ),
            source_protein_group_count=sum(
                1 for entry in protein_group_discrepancies if entry.source_table_present
            ),
            protein_group_discrepancy_count=sum(
                1
                for entry in protein_group_discrepancies
                if entry.status is not DdaProteinGroupDiscrepancyStatus.SHARED
            ),
            source_only_protein_group_count=sum(
                1
                for entry in protein_group_discrepancies
                if entry.status is DdaProteinGroupDiscrepancyStatus.SOURCE_ONLY
            ),
            workflow_only_protein_group_count=sum(
                1
                for entry in protein_group_discrepancies
                if entry.status is DdaProteinGroupDiscrepancyStatus.WORKFLOW_ONLY
            ),
            sample_count=len(protein_lfq_report.sample_ids),
        ),
        note=(
            "DDA biology workflow normalizes search results, applies explicit PSM acceptance policy, runs protein parsimony review, builds protein LFQ, compares optional source protein tables against the workflow protein set, and hands the governed protein matrix to the shared biological reporting workflow"
        ),
    )


def build_label_free_quant_table_from_protein_lfq_report(
    report: ProteinLfqReport,
) -> LabelFreeQuantTable:
    """Bridge one protein LFQ report onto the shared label-free quant contract."""

    values: list[QuantValue] = []
    entity_protein_refs: dict[str, tuple[str, ...]] = {}
    entity_member_peptides: dict[str, tuple[str, ...]] = {}
    for row in report.rows:
        entity_protein_refs[row.entity_id] = row.protein_refs
        entity_member_peptides[row.entity_id] = row.contributing_peptides
        for sample_value in row.values:
            values.append(
                QuantValue(
                    sample_id=sample_value.sample_id,
                    entity_id=row.entity_id,
                    abundance=sample_value.abundance,
                    missing_value_kind=sample_value.missing_value_kind,
                    source_feature_count=sample_value.contributing_peptide_count,
                )
            )
    return LabelFreeQuantTable(
        entity_level=QuantEntityLevel.PROTEIN,
        measure_kind=QuantMeasureKind.INTENSITY,
        aggregation_method=report.aggregation_method,
        normalization_method=NormalizationMethod.NONE,
        sample_ids=report.sample_ids,
        entity_ids=tuple(row.entity_id for row in report.rows),
        values=tuple(values),
        entity_protein_refs=entity_protein_refs,
        entity_member_peptides=entity_member_peptides,
    )


def render_dda_biological_workflow_summary_tsv(
    report: DdaBiologicalWorkflowBundle,
) -> str:
    """Render one compact DDA biology workflow summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field_name, value in (
        ("adapter_kind", report.summary.adapter_kind.value),
        ("imported_psm_row_count", report.summary.imported_psm_row_count),
        ("parse_rejected_row_count", report.summary.parse_rejected_row_count),
        ("normalized_psm_count", report.summary.normalized_psm_count),
        ("best_spectrum_psm_count", report.summary.best_spectrum_psm_count),
        ("accepted_psm_count", report.summary.accepted_psm_count),
        ("filtered_psm_count", report.summary.filtered_psm_count),
        ("inferred_protein_count", report.summary.inferred_protein_count),
        ("quantified_protein_count", report.summary.quantified_protein_count),
        ("significant_protein_count", report.summary.significant_protein_count),
        ("source_protein_group_count", report.summary.source_protein_group_count),
        (
            "protein_group_discrepancy_count",
            report.summary.protein_group_discrepancy_count,
        ),
        (
            "source_only_protein_group_count",
            report.summary.source_only_protein_group_count,
        ),
        (
            "workflow_only_protein_group_count",
            report.summary.workflow_only_protein_group_count,
        ),
        ("sample_count", report.summary.sample_count),
        ("note", report.note),
    ):
        writer.writerow((field_name, value))
    return handle.getvalue()


def render_filtered_dda_psms_tsv(
    rows: tuple[DdaFilteredPsmEntry, ...],
) -> str:
    """Render filtered normalized DDA PSMs as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "run_id",
            "spectrum_id",
            "canonical_peptide",
            "charge",
            "score",
            "intensity",
            "q_value",
            "protein_refs",
            "target_decoy_label",
            "target_decoy_contaminant_class",
            "contaminant_flag",
            "filter_reasons",
        )
    )
    for row in rows:
        writer.writerow(
            (
                row.run_id or "",
                row.spectrum_id,
                row.canonical_peptide,
                row.charge,
                f"{row.score:g}",
                "" if row.intensity is None else f"{row.intensity:g}",
                "" if row.q_value is None else f"{row.q_value:g}",
                ";".join(row.protein_refs),
                row.target_decoy_label.value,
                row.target_decoy_contaminant_class.value,
                "true" if row.contaminant_flag else "false",
                ";".join(reason.value for reason in row.reasons),
            )
        )
    return handle.getvalue()


def render_rejected_psm_rows_tsv(rows: tuple[RejectedPsmRow, ...]) -> str:
    """Render parse-rejected raw PSM rows as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("row_number", "issue_codes", "issue_messages", "raw_fields"))
    for row in rows:
        writer.writerow(
            (
                row.row_number,
                ";".join(issue.code for issue in row.issues),
                ";".join(issue.message for issue in row.issues),
                _render_raw_field_dict(row.raw_fields),
            )
        )
    return handle.getvalue()


def render_protein_group_discrepancies_tsv(
    rows: tuple[DdaProteinGroupDiscrepancyEntry, ...],
) -> str:
    """Render one optional source-protein discrepancy table as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "protein_ref",
            "status",
            "source_table_present",
            "inferred_by_workflow",
            "quantified_by_workflow",
            "significant_in_workflow",
        )
    )
    for row in rows:
        writer.writerow(
            (
                row.protein_ref,
                row.status.value,
                str(row.source_table_present).lower(),
                str(row.inferred_by_workflow).lower(),
                str(row.quantified_by_workflow).lower(),
                str(row.significant_in_workflow).lower(),
            )
        )
    return handle.getvalue()


def write_dda_biological_workflow_bundle(
    report: DdaBiologicalWorkflowBundle,
    output_dir: Path,
) -> DdaBiologicalWorkflowExportManifest:
    """Write one DDA biology workflow bundle into a stable output directory."""

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_name = "dda_biological_summary.tsv"
    accepted_name = "dda_biological_psms.tsv"
    filtered_name = "dda_biological_filtered_psms.tsv"
    rejected_name = "dda_biological_parse_rejected.tsv"
    rejected_evidence_name = "rejected_evidence.tsv"
    parsimony_summary_name = "dda_parsimony_summary.tsv"
    parsimony_proteins_name = "dda_parsimony_proteins.tsv"
    parsimony_ambiguities_name = "dda_parsimony_ambiguities.tsv"
    protein_lfq_summary_name = "dda_protein_lfq_summary.tsv"
    protein_lfq_matrix_name = "dda_protein_lfq_matrix.tsv"
    protein_lfq_pairwise_name = "dda_protein_lfq_pairwise.tsv"
    protein_lfq_missingness_name = "dda_protein_lfq_missingness.tsv"
    protein_lfq_missingness_mask_name = "dda_protein_lfq_missingness_mask.tsv"
    protein_discrepancy_name = "dda_source_protein_discrepancies.tsv"
    biological_manifest_name = "biological_report_manifest.json"
    rejected_evidence_entries = build_dda_workflow_rejected_evidence_entries(report)

    write_output_table_tsv((output_dir / summary_name), render_dda_biological_workflow_summary_tsv(report))
    export_psm_tsv(report.accepted_psms, output_dir / accepted_name)
    write_output_table_tsv((output_dir / filtered_name), render_filtered_dda_psms_tsv(report.filtered_psms))
    write_output_table_tsv((output_dir / rejected_name), render_rejected_psm_rows_tsv(report.parse_rejected_rows))
    write_output_table_tsv(
        (output_dir / rejected_evidence_name),
        render_result_rejected_evidence_tsv(rejected_evidence_entries),
    )
    write_output_table_tsv((output_dir / parsimony_summary_name), render_parsimony_review_summary_tsv(report.parsimony_review))
    write_output_table_tsv((output_dir / parsimony_proteins_name), render_parsimony_review_proteins_tsv(report.parsimony_review))
    write_output_table_tsv((output_dir / parsimony_ambiguities_name), render_parsimony_review_ambiguities_tsv(report.parsimony_review))
    write_output_table_tsv((output_dir / protein_lfq_summary_name), render_protein_lfq_summary_tsv(report.protein_lfq_report))
    write_output_table_tsv((output_dir / protein_lfq_matrix_name), render_protein_lfq_matrix_tsv(report.protein_lfq_report))
    write_output_table_tsv((output_dir / protein_lfq_pairwise_name), render_protein_lfq_pairwise_ratios_tsv(report.protein_lfq_report))
    write_output_table_tsv((output_dir / protein_lfq_missingness_name), render_protein_lfq_missingness_tsv(report.protein_lfq_report))
    write_output_table_tsv((output_dir / protein_lfq_missingness_mask_name), render_protein_lfq_missingness_mask_tsv(report.protein_lfq_report))
    if report.protein_group_discrepancies:
        write_output_table_tsv((output_dir / protein_discrepancy_name), render_protein_group_discrepancies_tsv(report.protein_group_discrepancies))
    biological_manifest = write_biological_result_report_bundle(
        report.biological_report,
        output_dir,
    )
    atomic_write_text(
        output_dir / biological_manifest_name,
        biological_manifest.to_stable_json() + "\n",
    )
    synchronize_workflow_artifact_layout(
        output_dir,
        producer_function="write_dda_biological_workflow_bundle",
    )
    return DdaBiologicalWorkflowExportManifest(
        summary=report.summary,
        artifacts=DdaBiologicalWorkflowArtifactPaths(
            summary_tsv=summary_name,
            accepted_psm_tsv=accepted_name,
            filtered_psm_tsv=filtered_name,
            parse_rejected_tsv=rejected_name,
            rejected_evidence_tsv=rejected_evidence_name,
            parsimony_summary_tsv=parsimony_summary_name,
            parsimony_proteins_tsv=parsimony_proteins_name,
            parsimony_ambiguities_tsv=parsimony_ambiguities_name,
            protein_lfq_summary_tsv=protein_lfq_summary_name,
            protein_lfq_matrix_tsv=protein_lfq_matrix_name,
            protein_lfq_pairwise_tsv=protein_lfq_pairwise_name,
            protein_lfq_missingness_tsv=protein_lfq_missingness_name,
            protein_lfq_missingness_mask_tsv=protein_lfq_missingness_mask_name,
            protein_group_discrepancy_tsv=(
                protein_discrepancy_name
                if report.protein_group_discrepancies
                else None
            ),
            biological_manifest_json=biological_manifest_name,
            report_html=biological_manifest.artifacts.report_html,
        ),
        biological_report_manifest=biological_manifest,
        note=(
            "DDA biology export preserves accepted and filtered search evidence, optional source-protein discrepancy review, parsimony review, protein LFQ, and the downstream biological report bundle in one directory"
        ),
    )


def export_dda_biological_workflow_bundle(
    report: DdaBiologicalWorkflowBundle,
    output_dir: Path,
) -> DdaBiologicalWorkflowExportManifest:
    """Compatibility wrapper for the legacy DDA workflow bundle export name."""

    return write_dda_biological_workflow_bundle(report, output_dir)


def build_dda_workflow_rejected_evidence_entries(
    report: DdaBiologicalWorkflowBundle,
) -> tuple:
    parse_rejections = build_rejected_evidence_entries_from_issue_rows(
        report.parse_rejected_rows,
        source_surface="dda_import",
        related_artifact="rejected_evidence.tsv",
        entity_prefix="psm",
        entity_type="psm",
    )
    filtered_rejections = tuple(
        build_rejected_evidence_entry(
            evidence_id=(
                f"dda_biology:{row.spectrum_id}:{row.canonical_peptide}:{row.charge}:{reason.value}"
            ),
            source_surface="dda_biology",
            reason_code=_rejected_reason_code_for_dda_filter(reason),
            message=f"filtered dda psm due to {reason.value.replace('_', ' ')}",
            related_artifact="rejected_evidence.tsv",
            entity_type="psm",
            entity_id=row.spectrum_id,
        )
        for row in report.filtered_psms
        for reason in row.reasons
    )
    return parse_rejections + filtered_rejections


def _rejected_reason_code_for_dda_filter(reason: DdaPsmAcceptanceReason) -> str:
    if reason is DdaPsmAcceptanceReason.Q_VALUE_ABOVE_THRESHOLD:
        return "q_value_above_threshold"
    if reason is DdaPsmAcceptanceReason.CONTAMINANT:
        return "contaminant"
    if reason is DdaPsmAcceptanceReason.MISSING_PROTEIN_REFS:
        return "missing_protein_refs"
    return "rejected_psm_row"


def _normalize_search_results(
    *,
    source_path: Path,
    adapter_kind: SearchAdapterKind,
    dialect_id: str,
    generic_mapping_path: Path | None,
):
    if adapter_kind is SearchAdapterKind.GENERIC:
        if generic_mapping_path is None:
            raise ValueError(
                "generic DDA biology workflows require an explicit generic_mapping_path"
            )
        mapping = load_generic_psm_table_mapping(
            generic_mapping_path
        ).to_search_result_mapping()
    else:
        if generic_mapping_path is not None:
            raise ValueError(
                "generic_mapping_path is only supported with the generic search adapter"
            )
        mapping = None
    return normalize_search_results_with_adapter(
        source_path=source_path,
        adapter_kind=adapter_kind,
        dialect_id=dialect_id,
        mapping=mapping,
    )


def _build_protein_group_discrepancies(
    *,
    source_protein_tsv_path: Path | None,
    parsimony_review: ParsimonyReviewReport,
    protein_lfq_report: ProteinLfqReport,
    biological_report: BiologicalResultReportBundle,
) -> tuple[DdaProteinGroupDiscrepancyEntry, ...]:
    if source_protein_tsv_path is None:
        return ()
    source_refs = set(_parse_source_protein_refs(source_protein_tsv_path))
    inferred_refs = {
        entry.protein_ref for entry in parsimony_review.selected_proteins
    }
    quantified_refs = {
        row.entity_id for row in protein_lfq_report.rows
    }
    significant_refs = {
        card.protein_group_id
        for card in biological_report.protein_cards.cards
        if card.significant
    }
    all_refs = sorted(source_refs | inferred_refs | quantified_refs | significant_refs)
    discrepancies: list[DdaProteinGroupDiscrepancyEntry] = []
    for protein_ref in all_refs:
        source_present = protein_ref in source_refs
        workflow_present = protein_ref in inferred_refs or protein_ref in quantified_refs
        if source_present and workflow_present:
            status = DdaProteinGroupDiscrepancyStatus.SHARED
        elif source_present:
            status = DdaProteinGroupDiscrepancyStatus.SOURCE_ONLY
        else:
            status = DdaProteinGroupDiscrepancyStatus.WORKFLOW_ONLY
        discrepancies.append(
            DdaProteinGroupDiscrepancyEntry(
                protein_ref=protein_ref,
                status=status,
                source_table_present=source_present,
                inferred_by_workflow=protein_ref in inferred_refs,
                quantified_by_workflow=protein_ref in quantified_refs,
                significant_in_workflow=protein_ref in significant_refs,
            )
        )
    return tuple(discrepancies)


def _parse_source_protein_refs(path: Path) -> tuple[str, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("source protein table must include a header row")
        if "Protein" not in reader.fieldnames:
            raise ValueError("source protein table must include a 'Protein' column")
        refs = {
            str(row.get("Protein", "")).strip()
            for row in reader
            if str(row.get("Protein", "")).strip()
        }
    return tuple(sorted(refs))


def _filter_psms_for_biological_workflow(
    rows: tuple[PsmRecord, ...],
    *,
    policy: DdaPsmAcceptancePolicy,
) -> tuple[tuple[PsmRecord, ...], tuple[DdaFilteredPsmEntry, ...]]:
    accepted: list[PsmRecord] = []
    filtered: list[DdaFilteredPsmEntry] = []
    for row in rows:
        reasons: list[DdaPsmAcceptanceReason] = []
        if row.q_value is None:
            reasons.append(DdaPsmAcceptanceReason.MISSING_Q_VALUE)
        elif row.q_value > policy.max_q_value:
            reasons.append(DdaPsmAcceptanceReason.Q_VALUE_ABOVE_THRESHOLD)
        if policy.exclude_decoys and row.target_decoy_label is TargetDecoyLabel.DECOY:
            reasons.append(DdaPsmAcceptanceReason.DECOY)
        if (
            policy.exclude_contaminants
            and row.target_decoy_contaminant_class
            in {
                TargetDecoyContaminantClass.CONTAMINANT,
                TargetDecoyContaminantClass.MIXED,
            }
        ):
            reasons.append(DdaPsmAcceptanceReason.CONTAMINANT)
        if policy.require_run_id and not row.run_id:
            reasons.append(DdaPsmAcceptanceReason.MISSING_RUN_ID)
        if policy.require_intensity and row.intensity is None:
            reasons.append(DdaPsmAcceptanceReason.MISSING_INTENSITY)
        if policy.require_protein_refs and not row.protein_refs:
            reasons.append(DdaPsmAcceptanceReason.MISSING_PROTEIN_REFS)
        if reasons:
            filtered.append(
                DdaFilteredPsmEntry(
                    run_id=row.run_id,
                    spectrum_id=row.spectrum_id,
                    canonical_peptide=row.canonical_peptide,
                    charge=row.charge,
                    score=row.score,
                    intensity=row.intensity,
                    q_value=row.q_value,
                    protein_refs=row.protein_refs,
                    target_decoy_label=row.target_decoy_label,
                    contaminant_flag=row.contaminant_flag,
                    target_decoy_contaminant_class=row.target_decoy_contaminant_class,
                    reasons=tuple(dict.fromkeys(reasons)),
                )
            )
            continue
        accepted.append(row)
    return tuple(accepted), tuple(filtered)


def _render_raw_field_dict(raw_fields: dict[str, str]) -> str:
    return ";".join(
        f"{key}={value}" for key, value in sorted(raw_fields.items(), key=lambda item: item[0])
    )
