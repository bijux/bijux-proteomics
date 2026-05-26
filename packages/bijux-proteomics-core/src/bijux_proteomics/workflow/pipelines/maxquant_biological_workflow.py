# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned MaxQuant-to-biology workflow bundles."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import (
    MaxquantImportReport,
    MaxquantLfqMatrixCandidateEntry,
    MaxquantPeptideReviewEntry,
    MaxquantProteinGroupReviewEntry,
    build_maxquant_lfq_matrix_candidates,
    render_maxquant_evidence_tsv,
    render_maxquant_peptide_tsv,
    render_maxquant_protein_group_tsv,
    render_maxquant_summary_tsv,
)
from bijux_proteomics.identification.maxquant_import import build_maxquant_import_report
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    LabelFreeQuantTable,
    MissingValueKind,
    NormalizationMethod,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
    QuantValue,
    render_label_free_quant_missingness_matrix_tsv,
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
    build_rejected_evidence_entry,
    render_result_rejected_evidence_tsv,
)
from bijux_proteomics_foundation import JsonModel


class MaxquantProteinGroupAcceptanceReason(StrEnum):
    """Stable reasons why one MaxQuant protein group cannot enter biology workflows."""

    CONTAMINANT = "contaminant"
    REVERSE = "reverse"
    ONLY_IDENTIFIED_BY_SITE = "only_identified_by_site"
    MISSING_PROTEIN_REFS = "missing_protein_refs"
    MISSING_LFQ_SIGNAL = "missing_lfq_signal"


class MaxquantProteinGroupAcceptancePolicy(JsonModel):
    """Explicit acceptance policy for MaxQuant protein groups entering biology."""

    model_config = ConfigDict(extra="forbid")

    exclude_contaminants: bool = True
    exclude_reverse: bool = True
    exclude_only_identified_by_site: bool = True
    require_lfq_signal: bool = True
    require_protein_refs: bool = True


class MaxquantFilteredProteinGroupEntry(JsonModel):
    """One MaxQuant protein group filtered before biology reporting."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    protein_ids: tuple[str, ...] = Field(default_factory=tuple)
    majority_protein_ids: tuple[str, ...] = Field(default_factory=tuple)
    contaminant_flag: bool = False
    reverse_flag: bool = False
    only_identified_by_site: bool = False
    observed_lfq_experiment_count: int = Field(..., ge=0)
    reasons: tuple[MaxquantProteinGroupAcceptanceReason, ...] = Field(
        default_factory=tuple
    )


class MaxquantBiologicalWorkflowSummary(JsonModel):
    """Compact summary over one MaxQuant-to-biology workflow bundle."""

    model_config = ConfigDict(extra="forbid")

    imported_evidence_count: int = Field(..., ge=0)
    imported_peptide_row_count: int = Field(..., ge=0)
    imported_protein_group_row_count: int = Field(..., ge=0)
    accepted_protein_group_count: int = Field(..., ge=0)
    filtered_protein_group_count: int = Field(..., ge=0)
    enrichment_foreground_protein_count: int = Field(..., ge=0)
    lfq_experiment_count: int = Field(..., ge=0)
    quantified_protein_count: int = Field(..., ge=0)
    significant_protein_count: int = Field(..., ge=0)
    annotation_entry_count: int = Field(..., ge=0)
    protein_card_count: int = Field(..., ge=0)
    context_term_count: int = Field(..., ge=0)
    go_enriched_term_count: int = Field(..., ge=0)
    pathway_enriched_entry_count: int = Field(..., ge=0)
    complex_enriched_entry_count: int = Field(..., ge=0)


class MaxquantBiologicalForegroundEntry(JsonModel):
    """One final MaxQuant protein that entered the biological enrichment foreground."""

    model_config = ConfigDict(extra="forbid")

    card_id: str = Field(..., min_length=1)
    entity_id: str = Field(..., min_length=1)
    representative_protein_ref: str = Field(..., min_length=1)
    protein_ids: tuple[str, ...] = Field(default_factory=tuple)
    majority_protein_ids: tuple[str, ...] = Field(default_factory=tuple)
    contaminant_flag: bool = False
    reverse_flag: bool = False
    only_identified_by_site: bool = False


class MaxquantBiologicalWorkflowBundle(JsonModel):
    """Owned MaxQuant bundle from imported result tables to biological reporting."""

    model_config = ConfigDict(extra="forbid")

    import_report: MaxquantImportReport
    acceptance_policy: MaxquantProteinGroupAcceptancePolicy
    accepted_protein_groups: tuple[MaxquantProteinGroupReviewEntry, ...] = Field(
        default_factory=tuple
    )
    filtered_protein_groups: tuple[MaxquantFilteredProteinGroupEntry, ...] = Field(
        default_factory=tuple
    )
    enrichment_foreground_entries: tuple[MaxquantBiologicalForegroundEntry, ...] = Field(
        default_factory=tuple
    )
    lfq_table: LabelFreeQuantTable
    biological_report: BiologicalResultReportBundle
    summary: MaxquantBiologicalWorkflowSummary
    note: str = Field(..., min_length=1)


class MaxquantBiologicalWorkflowArtifactPaths(JsonModel):
    """Relative artifact paths written into one MaxQuant biology output directory."""

    model_config = ConfigDict(extra="forbid")

    summary_tsv: str = Field(..., min_length=1)
    import_summary_tsv: str = Field(..., min_length=1)
    evidence_tsv: str = Field(..., min_length=1)
    peptides_tsv: str = Field(..., min_length=1)
    protein_groups_tsv: str = Field(..., min_length=1)
    accepted_protein_groups_tsv: str = Field(..., min_length=1)
    filtered_protein_groups_tsv: str = Field(..., min_length=1)
    rejected_evidence_tsv: str = Field(..., min_length=1)
    enrichment_foreground_tsv: str = Field(..., min_length=1)
    lfq_summary_tsv: str = Field(..., min_length=1)
    lfq_matrix_tsv: str = Field(..., min_length=1)
    lfq_missingness_tsv: str = Field(..., min_length=1)
    biological_manifest_json: str = Field(..., min_length=1)
    protein_card_summary_tsv: str = Field(..., min_length=1)
    protein_card_tsv: str = Field(..., min_length=1)
    annotation_tsv: str = Field(..., min_length=1)
    annotation_unmapped_tsv: str = Field(..., min_length=1)
    context_mapping_tsv: str | None = None
    context_term_tsv: str | None = None
    context_unmapped_tsv: str | None = None
    context_rejected_tsv: str | None = None
    report_html: str = Field(..., min_length=1)


class MaxquantBiologicalWorkflowExportManifest(JsonModel):
    """Stable manifest over one exported MaxQuant-to-biology directory."""

    model_config = ConfigDict(extra="forbid")

    summary: MaxquantBiologicalWorkflowSummary
    artifacts: MaxquantBiologicalWorkflowArtifactPaths
    biological_report_manifest: BiologicalResultReportExportManifest
    note: str = Field(..., min_length=1)


def build_maxquant_biological_workflow_bundle(
    evidence_txt_path: Path,
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    peptides_txt_path: Path,
    protein_groups_txt_path: Path,
    proteins_fasta_path: Path,
    protocol_context_tsv_path: Path | None = None,
    config_path: Path | None = None,
    acceptance_policy: MaxquantProteinGroupAcceptancePolicy | None = None,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    annotation_tsv_path: Path | None = None,
    context_annotation_tsv_path: Path | None = None,
    go_annotation_tsv_path: Path | None = None,
    pathway_membership_tsv_path: Path | None = None,
    complex_membership_tsv_path: Path | None = None,
    selection_policy: BiologicalResultSelectionPolicy | None = None,
    volcano_policy: VolcanoReviewPolicy | None = None,
) -> MaxquantBiologicalWorkflowBundle:
    """Build one governed MaxQuant-to-biology workflow bundle."""

    experiment_design = coerce_experiment_design(design_entries)
    import_report = build_maxquant_import_report(
        evidence_txt_path,
        peptides_txt_path=peptides_txt_path,
        protein_groups_txt_path=protein_groups_txt_path,
        config_path=config_path,
    )
    active_policy = acceptance_policy or MaxquantProteinGroupAcceptancePolicy()
    _validate_biological_acceptance_policy(active_policy)
    accepted_protein_groups, filtered_protein_groups = (
        _filter_protein_groups_for_biology(
            import_report.protein_group_rows,
            policy=active_policy,
        )
    )
    if not accepted_protein_groups:
        raise ValueError(
            "MaxQuant biology workflow did not retain any protein groups after acceptance filtering"
        )
    lfq_table = build_label_free_quant_table_from_maxquant_protein_groups(
        accepted_protein_groups,
        peptide_rows=import_report.peptide_rows,
    )
    biological_report = build_biological_result_report_bundle_from_quant_table(
        lfq_table,
        experiment_design,
        proteins_fasta_path=proteins_fasta_path,
        protocol_context_tsv_path=protocol_context_tsv_path,
        annotation_tsv_path=annotation_tsv_path,
        context_annotation_tsv_path=context_annotation_tsv_path,
        go_annotation_tsv_path=go_annotation_tsv_path,
        pathway_membership_tsv_path=pathway_membership_tsv_path,
        complex_membership_tsv_path=complex_membership_tsv_path,
        normalization_method=normalization_method,
        condition_a=condition_a,
        condition_b=condition_b,
        selection_policy=selection_policy,
        volcano_policy=volcano_policy,
    )
    enrichment_foreground_entries = _build_enrichment_foreground_entries(
        biological_report,
        accepted_protein_groups,
    )
    return MaxquantBiologicalWorkflowBundle(
        import_report=import_report,
        acceptance_policy=active_policy,
        accepted_protein_groups=accepted_protein_groups,
        filtered_protein_groups=filtered_protein_groups,
        enrichment_foreground_entries=enrichment_foreground_entries,
        lfq_table=lfq_table,
        biological_report=biological_report,
        summary=MaxquantBiologicalWorkflowSummary(
            imported_evidence_count=import_report.summary.accepted_evidence_count,
            imported_peptide_row_count=import_report.summary.peptide_row_count,
            imported_protein_group_row_count=import_report.summary.protein_group_row_count,
            accepted_protein_group_count=len(accepted_protein_groups),
            filtered_protein_group_count=len(filtered_protein_groups),
            enrichment_foreground_protein_count=len(enrichment_foreground_entries),
            lfq_experiment_count=import_report.summary.lfq_experiment_count,
            quantified_protein_count=len(lfq_table.entity_ids),
            significant_protein_count=biological_report.summary.significant_protein_count,
            annotation_entry_count=biological_report.summary.annotation_entry_count,
            protein_card_count=biological_report.summary.protein_card_count,
            context_term_count=biological_report.summary.context_term_count,
            go_enriched_term_count=biological_report.summary.go_enriched_term_count,
            pathway_enriched_entry_count=biological_report.summary.pathway_enriched_entry_count,
            complex_enriched_entry_count=biological_report.summary.complex_enriched_entry_count,
        ),
        note=(
            "MaxQuant biological workflow preserves imported evidence, peptides, and protein groups, excludes contaminant and reverse protein groups before biological foreground selection, bridges LFQ intensities onto the governed protein quant contract, and hands that matrix to shared biological reporting"
        ),
    )


def build_label_free_quant_table_from_maxquant_protein_groups(
    rows: tuple[MaxquantProteinGroupReviewEntry, ...],
    *,
    peptide_rows: tuple[MaxquantPeptideReviewEntry, ...],
) -> LabelFreeQuantTable:
    """Bridge accepted MaxQuant protein-group LFQ rows onto the shared quant contract."""

    candidates = build_maxquant_lfq_matrix_candidates(rows, peptide_rows=peptide_rows)
    return build_label_free_quant_table_from_maxquant_lfq_candidates(candidates)


def build_label_free_quant_table_from_maxquant_lfq_candidates(
    rows: tuple[MaxquantLfqMatrixCandidateEntry, ...],
) -> LabelFreeQuantTable:
    """Bridge accepted MaxQuant LFQ candidates onto the shared quant contract."""

    if not rows:
        raise ValueError("MaxQuant protein-group bridge requires at least one row")
    sample_ids = tuple(entry.experiment_name for entry in rows[0].lfq_intensities)
    if not sample_ids:
        raise ValueError("MaxQuant protein-group bridge requires LFQ experiments")
    values: list[QuantValue] = []
    entity_protein_refs: dict[str, tuple[str, ...]] = {}
    for row in rows:
        entity_id = row.entity_id
        entity_protein_refs[entity_id] = row.protein_ids
        source_feature_count = len(row.member_peptides)
        for intensity in row.lfq_intensities:
            abundance = intensity.intensity if intensity.intensity > 0.0 else None
            values.append(
                QuantValue(
                    sample_id=intensity.experiment_name,
                    entity_id=entity_id,
                    abundance=abundance,
                    missing_value_kind=(
                        MissingValueKind.OBSERVED
                        if abundance is not None
                        else MissingValueKind.ZERO
                    ),
                    source_feature_count=source_feature_count,
                )
            )
    return LabelFreeQuantTable(
        entity_level=QuantEntityLevel.PROTEIN,
        measure_kind=QuantMeasureKind.INTENSITY,
        aggregation_method=QuantRollupMethod.SUM,
        normalization_method=NormalizationMethod.NONE,
        sample_ids=sample_ids,
        entity_ids=tuple(row.entity_id for row in rows),
        values=tuple(values),
        entity_protein_refs=entity_protein_refs,
        entity_member_peptides={
            row.entity_id: row.member_peptides
            for row in rows
        },
    )


def render_maxquant_biological_workflow_summary_tsv(
    report: MaxquantBiologicalWorkflowBundle,
) -> str:
    """Render one compact MaxQuant biology workflow summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field_name, value in (
        ("imported_evidence_count", report.summary.imported_evidence_count),
        ("imported_peptide_row_count", report.summary.imported_peptide_row_count),
        (
            "imported_protein_group_row_count",
            report.summary.imported_protein_group_row_count,
        ),
        (
            "accepted_protein_group_count",
            report.summary.accepted_protein_group_count,
        ),
        (
            "filtered_protein_group_count",
            report.summary.filtered_protein_group_count,
        ),
        (
            "enrichment_foreground_protein_count",
            report.summary.enrichment_foreground_protein_count,
        ),
        ("lfq_experiment_count", report.summary.lfq_experiment_count),
        ("quantified_protein_count", report.summary.quantified_protein_count),
        ("significant_protein_count", report.summary.significant_protein_count),
        ("annotation_entry_count", report.summary.annotation_entry_count),
        ("protein_card_count", report.summary.protein_card_count),
        ("context_term_count", report.summary.context_term_count),
        ("go_enriched_term_count", report.summary.go_enriched_term_count),
        (
            "pathway_enriched_entry_count",
            report.summary.pathway_enriched_entry_count,
        ),
        ("complex_enriched_entry_count", report.summary.complex_enriched_entry_count),
        ("note", report.note),
    ):
        writer.writerow((field_name, value))
    return handle.getvalue()


def render_filtered_maxquant_protein_groups_tsv(
    rows: tuple[MaxquantFilteredProteinGroupEntry, ...],
) -> str:
    """Render filtered MaxQuant protein groups as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_id",
            "protein_ids",
            "majority_protein_ids",
            "contaminant_flag",
            "reverse_flag",
            "only_identified_by_site",
            "observed_lfq_experiment_count",
            "filter_reasons",
        )
    )
    for row in rows:
        writer.writerow(
            (
                row.entity_id,
                ";".join(row.protein_ids),
                ";".join(row.majority_protein_ids),
                str(row.contaminant_flag).lower(),
                str(row.reverse_flag).lower(),
                str(row.only_identified_by_site).lower(),
                row.observed_lfq_experiment_count,
                ";".join(reason.value for reason in row.reasons),
            )
        )
    return handle.getvalue()


def render_maxquant_enrichment_foreground_tsv(
    rows: tuple[MaxquantBiologicalForegroundEntry, ...],
) -> str:
    """Render the final MaxQuant biological enrichment foreground as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "card_id",
            "entity_id",
            "representative_protein_ref",
            "protein_ids",
            "majority_protein_ids",
            "contaminant_flag",
            "reverse_flag",
            "only_identified_by_site",
        )
    )
    for row in rows:
        writer.writerow(
            (
                row.card_id,
                row.entity_id,
                row.representative_protein_ref,
                ";".join(row.protein_ids),
                ";".join(row.majority_protein_ids),
                str(row.contaminant_flag).lower(),
                str(row.reverse_flag).lower(),
                str(row.only_identified_by_site).lower(),
            )
        )
    return handle.getvalue()


def render_maxquant_lfq_summary_tsv(report: MaxquantBiologicalWorkflowBundle) -> str:
    """Render one compact LFQ matrix summary as TSV."""

    observed_cell_count = sum(
        1 for value in report.lfq_table.values if value.abundance is not None
    )
    missing_cell_count = len(report.lfq_table.values) - observed_cell_count
    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field_name, value in (
        ("entity_count", len(report.lfq_table.entity_ids)),
        ("sample_count", len(report.lfq_table.sample_ids)),
        ("observed_cell_count", observed_cell_count),
        ("missing_cell_count", missing_cell_count),
        ("normalization_method", report.lfq_table.normalization_method.value),
        ("measure_kind", report.lfq_table.measure_kind.value),
    ):
        writer.writerow((field_name, value))
    return handle.getvalue()


def render_maxquant_lfq_matrix_tsv(table: LabelFreeQuantTable) -> str:
    """Render one accepted MaxQuant LFQ matrix as TSV."""

    value_lookup = {
        (value.entity_id, value.sample_id): value for value in table.values
    }
    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_id",
            "protein_refs",
            "member_peptides",
            *table.sample_ids,
        )
    )
    for entity_id in table.entity_ids:
        writer.writerow(
            (
                entity_id,
                ";".join(table.entity_protein_refs.get(entity_id, ())),
                ";".join(table.entity_member_peptides.get(entity_id, ())),
                *(
                    ""
                    if value_lookup[(entity_id, sample_id)].abundance is None
                    else f"{value_lookup[(entity_id, sample_id)].abundance:g}"
                    for sample_id in table.sample_ids
                ),
            )
        )
    return handle.getvalue()


def write_maxquant_biological_workflow_bundle(
    report: MaxquantBiologicalWorkflowBundle,
    output_dir: Path,
) -> MaxquantBiologicalWorkflowExportManifest:
    """Export one MaxQuant biology workflow bundle into a stable directory."""

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_name = "maxquant_biological_summary.tsv"
    import_summary_name = "maxquant_import_summary.tsv"
    evidence_name = "maxquant_evidence.tsv"
    peptides_name = "maxquant_peptides.tsv"
    protein_groups_name = "maxquant_protein_groups.tsv"
    accepted_groups_name = "maxquant_accepted_protein_groups.tsv"
    filtered_groups_name = "maxquant_filtered_protein_groups.tsv"
    rejected_evidence_name = "rejected_evidence.tsv"
    foreground_name = "maxquant_biological_foreground.tsv"
    lfq_summary_name = "maxquant_lfq_summary.tsv"
    lfq_matrix_name = "maxquant_lfq_matrix.tsv"
    lfq_missingness_name = "maxquant_lfq_missingness.tsv"
    biological_manifest_name = "biological_report_manifest.json"
    rejected_evidence_entries = tuple(
        build_rejected_evidence_entry(
            evidence_id=f"maxquant_biology:{row.entity_id}:{reason.value}",
            source_surface="maxquant_biology",
            reason_code=reason.value,
            message=(
                f"filtered maxquant protein group due to {reason.value.replace('_', ' ')}"
            ),
            related_artifact=rejected_evidence_name,
            entity_type="protein_group",
            entity_id=row.entity_id,
        )
        for row in report.filtered_protein_groups
        for reason in row.reasons
    )

    write_output_table_tsv((output_dir / summary_name), render_maxquant_biological_workflow_summary_tsv(report))
    write_output_table_tsv((output_dir / import_summary_name), render_maxquant_summary_tsv(report.import_report.summary))
    write_output_table_tsv((output_dir / evidence_name), render_maxquant_evidence_tsv(report.import_report.evidence_rows))
    write_output_table_tsv((output_dir / peptides_name), render_maxquant_peptide_tsv(report.import_report.peptide_rows))
    write_output_table_tsv((output_dir / protein_groups_name), render_maxquant_protein_group_tsv(report.import_report.protein_group_rows))
    write_output_table_tsv((output_dir / accepted_groups_name), render_maxquant_protein_group_tsv(report.accepted_protein_groups))
    write_output_table_tsv((output_dir / filtered_groups_name), render_filtered_maxquant_protein_groups_tsv(report.filtered_protein_groups))
    write_output_table_tsv(
        (output_dir / rejected_evidence_name),
        render_result_rejected_evidence_tsv(rejected_evidence_entries),
    )
    write_output_table_tsv((output_dir / foreground_name), render_maxquant_enrichment_foreground_tsv(report.enrichment_foreground_entries))
    write_output_table_tsv((output_dir / lfq_summary_name), render_maxquant_lfq_summary_tsv(report))
    write_output_table_tsv((output_dir / lfq_matrix_name), render_maxquant_lfq_matrix_tsv(report.lfq_table))
    write_output_table_tsv((output_dir / lfq_missingness_name), render_label_free_quant_missingness_matrix_tsv(report.lfq_table))
    biological_manifest = write_biological_result_report_bundle(
        report.biological_report,
        output_dir,
    )
    (output_dir / biological_manifest_name).write_text(
        biological_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )
    synchronize_workflow_artifact_layout(
        output_dir,
        producer_function="write_maxquant_biological_workflow_bundle",
    )
    return MaxquantBiologicalWorkflowExportManifest(
        summary=report.summary,
        artifacts=MaxquantBiologicalWorkflowArtifactPaths(
            summary_tsv=summary_name,
            import_summary_tsv=import_summary_name,
            evidence_tsv=evidence_name,
            peptides_tsv=peptides_name,
            protein_groups_tsv=protein_groups_name,
            accepted_protein_groups_tsv=accepted_groups_name,
            filtered_protein_groups_tsv=filtered_groups_name,
            rejected_evidence_tsv=rejected_evidence_name,
            enrichment_foreground_tsv=foreground_name,
            lfq_summary_tsv=lfq_summary_name,
            lfq_matrix_tsv=lfq_matrix_name,
            lfq_missingness_tsv=lfq_missingness_name,
            biological_manifest_json=biological_manifest_name,
            protein_card_summary_tsv=biological_manifest.artifacts.protein_card_summary_tsv,
            protein_card_tsv=biological_manifest.artifacts.protein_card_tsv,
            annotation_tsv=biological_manifest.artifacts.annotation_tsv,
            annotation_unmapped_tsv=biological_manifest.artifacts.annotation_unmapped_tsv,
            context_mapping_tsv=biological_manifest.artifacts.context_mapping_tsv,
            context_term_tsv=biological_manifest.artifacts.context_term_tsv,
            context_unmapped_tsv=biological_manifest.artifacts.context_unmapped_tsv,
            context_rejected_tsv=biological_manifest.artifacts.context_rejected_tsv,
            report_html=biological_manifest.artifacts.report_html,
        ),
        biological_report_manifest=biological_manifest,
        note=(
            "MaxQuant biology export preserves imported tables, explicit protein-group acceptance review, final biological foreground review, raw LFQ matrix review, and the downstream biological report bundle in one directory"
        ),
    )


def export_maxquant_biological_workflow_bundle(
    report: MaxquantBiologicalWorkflowBundle,
    output_dir: Path,
) -> MaxquantBiologicalWorkflowExportManifest:
    """Compatibility wrapper for the legacy MaxQuant workflow bundle export name."""

    return write_maxquant_biological_workflow_bundle(report, output_dir)


def _validate_biological_acceptance_policy(
    policy: MaxquantProteinGroupAcceptancePolicy,
) -> None:
    if not policy.exclude_contaminants:
        raise ValueError(
            "MaxQuant biological workflows require contaminant protein groups to stay excluded from biological foreground"
        )
    if not policy.exclude_reverse:
        raise ValueError(
            "MaxQuant biological workflows require reverse protein groups to stay excluded from biological foreground"
        )


def _filter_protein_groups_for_biology(
    rows: tuple[MaxquantProteinGroupReviewEntry, ...],
    *,
    policy: MaxquantProteinGroupAcceptancePolicy,
) -> tuple[
    tuple[MaxquantProteinGroupReviewEntry, ...],
    tuple[MaxquantFilteredProteinGroupEntry, ...],
]:
    accepted: list[MaxquantProteinGroupReviewEntry] = []
    filtered: list[MaxquantFilteredProteinGroupEntry] = []
    for row in rows:
        reasons = _protein_group_filter_reasons(row, policy=policy)
        if reasons:
            filtered.append(
                MaxquantFilteredProteinGroupEntry(
                    entity_id=_protein_group_entity_id(row),
                    protein_ids=row.protein_ids,
                    majority_protein_ids=row.majority_protein_ids,
                    contaminant_flag=row.contaminant_flag,
                    reverse_flag=row.reverse_flag,
                    only_identified_by_site=row.only_identified_by_site,
                    observed_lfq_experiment_count=sum(
                        1 for entry in row.lfq_intensities if entry.intensity > 0.0
                    ),
                    reasons=reasons,
                )
            )
            continue
        accepted.append(row)
    return tuple(accepted), tuple(filtered)


def _build_enrichment_foreground_entries(
    biological_report: BiologicalResultReportBundle,
    accepted_groups: tuple[MaxquantProteinGroupReviewEntry, ...],
) -> tuple[MaxquantBiologicalForegroundEntry, ...]:
    accepted_by_entity = {
        _protein_group_entity_id(row): row for row in accepted_groups
    }
    foreground_entries: list[MaxquantBiologicalForegroundEntry] = []
    for card in biological_report.protein_cards.cards:
        if not card.significant:
            continue
        source_group = accepted_by_entity.get(card.protein_group_id)
        foreground_entries.append(
            MaxquantBiologicalForegroundEntry(
                card_id=card.card_id,
                entity_id=card.protein_group_id,
                representative_protein_ref=card.representative_protein_ref,
                protein_ids=(
                    source_group.protein_ids
                    if source_group is not None
                    else card.protein_refs
                ),
                majority_protein_ids=(
                    source_group.majority_protein_ids if source_group is not None else ()
                ),
                contaminant_flag=(
                    source_group.contaminant_flag if source_group is not None else False
                ),
                reverse_flag=(
                    source_group.reverse_flag if source_group is not None else False
                ),
                only_identified_by_site=(
                    source_group.only_identified_by_site
                    if source_group is not None
                    else False
                ),
            )
        )
    return tuple(sorted(foreground_entries, key=lambda entry: entry.entity_id))


def _protein_group_filter_reasons(
    row: MaxquantProteinGroupReviewEntry,
    *,
    policy: MaxquantProteinGroupAcceptancePolicy,
) -> tuple[MaxquantProteinGroupAcceptanceReason, ...]:
    reasons: list[MaxquantProteinGroupAcceptanceReason] = []
    if policy.exclude_contaminants and row.contaminant_flag:
        reasons.append(MaxquantProteinGroupAcceptanceReason.CONTAMINANT)
    if policy.exclude_reverse and row.reverse_flag:
        reasons.append(MaxquantProteinGroupAcceptanceReason.REVERSE)
    if policy.exclude_only_identified_by_site and row.only_identified_by_site:
        reasons.append(MaxquantProteinGroupAcceptanceReason.ONLY_IDENTIFIED_BY_SITE)
    if policy.require_protein_refs and not row.protein_ids:
        reasons.append(MaxquantProteinGroupAcceptanceReason.MISSING_PROTEIN_REFS)
    if policy.require_lfq_signal and not any(
        entry.intensity > 0.0 for entry in row.lfq_intensities
    ):
        reasons.append(MaxquantProteinGroupAcceptanceReason.MISSING_LFQ_SIGNAL)
    return tuple(reasons)


def _protein_group_entity_id(row: MaxquantProteinGroupReviewEntry) -> str:
    protein_ids = row.majority_protein_ids or row.protein_ids
    if protein_ids:
        return ";".join(protein_ids)
    return "unassigned_protein_group"
