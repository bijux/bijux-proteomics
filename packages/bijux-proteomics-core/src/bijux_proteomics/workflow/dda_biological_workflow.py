# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned DDA search-result-to-biology workflow bundles."""

from __future__ import annotations

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
    render_protein_lfq_pairwise_ratios_tsv,
    render_protein_lfq_summary_tsv,
)
from bijux_proteomics.workflow.biological_reporting import (
    BiologicalResultReportBundle,
    BiologicalResultReportExportManifest,
    BiologicalResultSelectionPolicy,
    VolcanoReviewPolicy,
    build_biological_result_report_bundle_from_quant_table,
    export_biological_result_report_bundle,
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
    sample_count: int = Field(..., ge=0)


class DdaBiologicalWorkflowBundle(JsonModel):
    """Owned DDA bundle from normalized search results to biological reporting."""

    model_config = ConfigDict(extra="forbid")

    source_columns: tuple[str, ...] = Field(default_factory=tuple)
    acceptance_policy: DdaPsmAcceptancePolicy
    parse_rejected_rows: tuple[RejectedPsmRow, ...] = Field(default_factory=tuple)
    accepted_psms: tuple[PsmRecord, ...] = Field(default_factory=tuple)
    filtered_psms: tuple[DdaFilteredPsmEntry, ...] = Field(default_factory=tuple)
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
    parsimony_summary_tsv: str = Field(..., min_length=1)
    parsimony_proteins_tsv: str = Field(..., min_length=1)
    parsimony_ambiguities_tsv: str = Field(..., min_length=1)
    protein_lfq_summary_tsv: str = Field(..., min_length=1)
    protein_lfq_matrix_tsv: str = Field(..., min_length=1)
    protein_lfq_pairwise_tsv: str = Field(..., min_length=1)
    protein_lfq_missingness_tsv: str = Field(..., min_length=1)
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
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    proteins_fasta_path: Path,
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
    annotation_tsv_path: Path | None = None,
    go_annotation_tsv_path: Path | None = None,
    pathway_membership_tsv_path: Path | None = None,
    complex_membership_tsv_path: Path | None = None,
    selection_policy: BiologicalResultSelectionPolicy | None = None,
    volcano_policy: VolcanoReviewPolicy | None = None,
) -> DdaBiologicalWorkflowBundle:
    """Build a governed DDA search-result-to-biology workflow bundle."""

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
        design_entries,
        proteins_fasta_path=proteins_fasta_path,
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
    return DdaBiologicalWorkflowBundle(
        source_columns=normalization.source_columns,
        acceptance_policy=active_policy,
        parse_rejected_rows=normalization.parse_report.rejected_rows,
        accepted_psms=accepted_psms,
        filtered_psms=filtered_psms,
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
            sample_count=len(protein_lfq_report.sample_ids),
        ),
        note=(
            "DDA biology workflow normalizes search results, applies explicit PSM acceptance policy, runs protein parsimony review, builds protein LFQ, and hands the governed protein matrix to the shared biological reporting workflow"
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


def export_dda_biological_workflow_bundle(
    report: DdaBiologicalWorkflowBundle,
    output_dir: Path,
) -> DdaBiologicalWorkflowExportManifest:
    """Write one DDA biology workflow bundle into a stable output directory."""

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_name = "dda_biological_summary.tsv"
    accepted_name = "dda_biological_psms.tsv"
    filtered_name = "dda_biological_filtered_psms.tsv"
    rejected_name = "dda_biological_parse_rejected.tsv"
    parsimony_summary_name = "dda_parsimony_summary.tsv"
    parsimony_proteins_name = "dda_parsimony_proteins.tsv"
    parsimony_ambiguities_name = "dda_parsimony_ambiguities.tsv"
    protein_lfq_summary_name = "dda_protein_lfq_summary.tsv"
    protein_lfq_matrix_name = "dda_protein_lfq_matrix.tsv"
    protein_lfq_pairwise_name = "dda_protein_lfq_pairwise.tsv"
    protein_lfq_missingness_name = "dda_protein_lfq_missingness.tsv"
    biological_manifest_name = "biological_report_manifest.json"

    (output_dir / summary_name).write_text(
        render_dda_biological_workflow_summary_tsv(report),
        encoding="utf-8",
    )
    export_psm_tsv(report.accepted_psms, output_dir / accepted_name)
    (output_dir / filtered_name).write_text(
        render_filtered_dda_psms_tsv(report.filtered_psms),
        encoding="utf-8",
    )
    (output_dir / rejected_name).write_text(
        render_rejected_psm_rows_tsv(report.parse_rejected_rows),
        encoding="utf-8",
    )
    (output_dir / parsimony_summary_name).write_text(
        render_parsimony_review_summary_tsv(report.parsimony_review),
        encoding="utf-8",
    )
    (output_dir / parsimony_proteins_name).write_text(
        render_parsimony_review_proteins_tsv(report.parsimony_review),
        encoding="utf-8",
    )
    (output_dir / parsimony_ambiguities_name).write_text(
        render_parsimony_review_ambiguities_tsv(report.parsimony_review),
        encoding="utf-8",
    )
    (output_dir / protein_lfq_summary_name).write_text(
        render_protein_lfq_summary_tsv(report.protein_lfq_report),
        encoding="utf-8",
    )
    (output_dir / protein_lfq_matrix_name).write_text(
        render_protein_lfq_matrix_tsv(report.protein_lfq_report),
        encoding="utf-8",
    )
    (output_dir / protein_lfq_pairwise_name).write_text(
        render_protein_lfq_pairwise_ratios_tsv(report.protein_lfq_report),
        encoding="utf-8",
    )
    (output_dir / protein_lfq_missingness_name).write_text(
        render_protein_lfq_missingness_tsv(report.protein_lfq_report),
        encoding="utf-8",
    )
    biological_manifest = export_biological_result_report_bundle(
        report.biological_report,
        output_dir,
    )
    (output_dir / biological_manifest_name).write_text(
        biological_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )
    return DdaBiologicalWorkflowExportManifest(
        summary=report.summary,
        artifacts=DdaBiologicalWorkflowArtifactPaths(
            summary_tsv=summary_name,
            accepted_psm_tsv=accepted_name,
            filtered_psm_tsv=filtered_name,
            parse_rejected_tsv=rejected_name,
            parsimony_summary_tsv=parsimony_summary_name,
            parsimony_proteins_tsv=parsimony_proteins_name,
            parsimony_ambiguities_tsv=parsimony_ambiguities_name,
            protein_lfq_summary_tsv=protein_lfq_summary_name,
            protein_lfq_matrix_tsv=protein_lfq_matrix_name,
            protein_lfq_pairwise_tsv=protein_lfq_pairwise_name,
            protein_lfq_missingness_tsv=protein_lfq_missingness_name,
            biological_manifest_json=biological_manifest_name,
            report_html=biological_manifest.artifacts.report_html,
        ),
        biological_report_manifest=biological_manifest,
        note=(
            "DDA biology export preserves accepted and filtered search evidence, parsimony review, protein LFQ, and the downstream biological report bundle in one directory"
        ),
    )


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
        if policy.exclude_contaminants and row.contaminant_flag:
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
