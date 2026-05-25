# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Frontend-ready comparison payloads over governed interactive result bundles."""

from __future__ import annotations

import csv
import math
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.workflow.exports.interactive_result_bundle import (
    InteractiveResultBundle,
    InteractiveResultPathway,
    InteractiveResultProtein,
    InteractiveResultPtmSite,
    InteractiveResultQcEntry,
    InteractiveResultSourceReport,
    build_interactive_result_bundle_from_artifacts,
)
from bijux_proteomics_foundation import JsonModel


class InteractiveResultComparisonStatus(StrEnum):
    """Stable change classes preserved on UI comparison entries."""

    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"


class InteractiveResultComparisonReasonCode(StrEnum):
    """Stable reasons explaining why one result object changed."""

    ENTITY_ADDED = "entity_added"
    ENTITY_REMOVED = "entity_removed"
    LOG2_FOLD_CHANGE_CHANGED = "log2_fold_change_changed"
    ADJUSTED_P_VALUE_CHANGED = "adjusted_p_value_changed"
    SIGNIFICANCE_CHANGED = "significance_changed"
    EVIDENCE_TIER_CHANGED = "evidence_tier_changed"
    WARNING_CODES_CHANGED = "warning_codes_changed"
    LINKED_PEPTIDES_CHANGED = "linked_peptides_changed"
    LINKED_SITES_CHANGED = "linked_sites_changed"
    LINKED_PATHWAYS_CHANGED = "linked_pathways_changed"
    LOCALIZATION_TIER_CHANGED = "localization_tier_changed"
    PROTEIN_CORRECTION_STATUS_CHANGED = "protein_correction_status_changed"
    MECHANISM_CLASS_CHANGED = "mechanism_class_changed"
    CLAIM_IDS_CHANGED = "claim_ids_changed"
    QC_STATUS_CHANGED = "qc_status_changed"
    QC_SEVERITY_CHANGED = "qc_severity_changed"
    QC_REASON_CODES_CHANGED = "qc_reason_codes_changed"
    QC_MESSAGE_CHANGED = "qc_message_changed"
    ACTIVITY_SCORE_CHANGED = "activity_score_changed"
    ENRICHMENT_RATIO_CHANGED = "enrichment_ratio_changed"
    PATHWAY_ADJUSTED_P_VALUE_CHANGED = "pathway_adjusted_p_value_changed"
    FOREGROUND_OVERLAP_CHANGED = "foreground_overlap_changed"
    PATHWAY_CONFIDENCE_CHANGED = "pathway_confidence_changed"
    SUPPORTING_PROTEINS_CHANGED = "supporting_proteins_changed"
    UNRESOLVED_MEMBERS_CHANGED = "unresolved_members_changed"


class InteractiveResultComparisonReason(JsonModel):
    """One stable explanation attached to a changed result object."""

    model_config = ConfigDict(extra="forbid")

    code: InteractiveResultComparisonReasonCode
    field_name: str = Field(..., min_length=1)
    left_value: str | None = None
    right_value: str | None = None
    message: str = Field(..., min_length=1)


class InteractiveResultProteinComparisonEntry(JsonModel):
    """One changed protein object across two governed result bundles."""

    model_config = ConfigDict(extra="forbid")

    object_id: str = Field(..., min_length=1)
    status: InteractiveResultComparisonStatus
    representative_protein_ref: str | None = None
    gene_symbol: str | None = None
    left_protein: InteractiveResultProtein | None = None
    right_protein: InteractiveResultProtein | None = None
    reasons: tuple[InteractiveResultComparisonReason, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class InteractiveResultPtmSiteComparisonEntry(JsonModel):
    """One changed PTM-site object across two governed result bundles."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    status: InteractiveResultComparisonStatus
    protein_ref: str | None = None
    left_site: InteractiveResultPtmSite | None = None
    right_site: InteractiveResultPtmSite | None = None
    reasons: tuple[InteractiveResultComparisonReason, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class InteractiveResultQcComparisonEntry(JsonModel):
    """One changed QC object across two governed result bundles."""

    model_config = ConfigDict(extra="forbid")

    qc_id: str = Field(..., min_length=1)
    status: InteractiveResultComparisonStatus
    scope: str | None = None
    entity_id: str | None = None
    left_qc_entry: InteractiveResultQcEntry | None = None
    right_qc_entry: InteractiveResultQcEntry | None = None
    reasons: tuple[InteractiveResultComparisonReason, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class InteractiveResultPathwayComparisonEntry(JsonModel):
    """One changed pathway object across two governed result bundles."""

    model_config = ConfigDict(extra="forbid")

    pathway_id: str = Field(..., min_length=1)
    status: InteractiveResultComparisonStatus
    pathway_name: str | None = None
    left_pathway: InteractiveResultPathway | None = None
    right_pathway: InteractiveResultPathway | None = None
    reasons: tuple[InteractiveResultComparisonReason, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class InteractiveResultComparisonSummary(JsonModel):
    """Compact summary over one governed result comparison payload."""

    model_config = ConfigDict(extra="forbid")

    left_source_count: int = Field(..., ge=0)
    right_source_count: int = Field(..., ge=0)
    changed_protein_count: int = Field(..., ge=0)
    changed_ptm_site_count: int = Field(..., ge=0)
    changed_qc_entry_count: int = Field(..., ge=0)
    changed_pathway_count: int = Field(..., ge=0)
    total_change_count: int = Field(..., ge=0)
    total_reason_count: int = Field(..., ge=0)


class InteractiveResultComparisonPayload(JsonModel):
    """Frontend-ready JSON payload for comparing two governed result bundles."""

    model_config = ConfigDict(extra="forbid")

    left_source_reports: tuple[InteractiveResultSourceReport, ...] = Field(
        default_factory=tuple
    )
    right_source_reports: tuple[InteractiveResultSourceReport, ...] = Field(
        default_factory=tuple
    )
    left_summary: dict[str, int | bool] = Field(default_factory=dict)
    right_summary: dict[str, int | bool] = Field(default_factory=dict)
    changed_proteins: tuple[InteractiveResultProteinComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    changed_ptm_sites: tuple[InteractiveResultPtmSiteComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    changed_qc_entries: tuple[InteractiveResultQcComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    changed_pathways: tuple[InteractiveResultPathwayComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    summary: InteractiveResultComparisonSummary
    note: str = Field(..., min_length=1)


def build_interactive_result_comparison_from_artifacts(
    *,
    left_biological_report_dir: Path | None = None,
    left_ptm_report_dir: Path | None = None,
    left_run_qc_assessment_tsv_paths: tuple[Path, ...] = (),
    right_biological_report_dir: Path | None = None,
    right_ptm_report_dir: Path | None = None,
    right_run_qc_assessment_tsv_paths: tuple[Path, ...] = (),
) -> InteractiveResultComparisonPayload:
    """Build one result-comparison payload from two governed artifact groups."""

    left_bundle = _build_side_bundle(
        biological_report_dir=left_biological_report_dir,
        ptm_report_dir=left_ptm_report_dir,
        run_qc_assessment_tsv_paths=left_run_qc_assessment_tsv_paths,
        side_label="left",
    )
    right_bundle = _build_side_bundle(
        biological_report_dir=right_biological_report_dir,
        ptm_report_dir=right_ptm_report_dir,
        run_qc_assessment_tsv_paths=right_run_qc_assessment_tsv_paths,
        side_label="right",
    )
    return build_interactive_result_comparison_payload(left_bundle, right_bundle)


def build_interactive_result_comparison_payload(
    left_bundle: InteractiveResultBundle,
    right_bundle: InteractiveResultBundle,
) -> InteractiveResultComparisonPayload:
    """Compare two governed interactive result bundles for frontend clients."""

    changed_proteins = _build_protein_changes(left_bundle, right_bundle)
    changed_ptm_sites = _build_ptm_site_changes(left_bundle, right_bundle)
    changed_qc_entries = _build_qc_changes(left_bundle, right_bundle)
    changed_pathways = _build_pathway_changes(left_bundle, right_bundle)
    total_reason_count = sum(
        len(entry.reasons)
        for entry in (
            *changed_proteins,
            *changed_ptm_sites,
            *changed_qc_entries,
            *changed_pathways,
        )
    )
    return InteractiveResultComparisonPayload(
        left_source_reports=left_bundle.source_reports,
        right_source_reports=right_bundle.source_reports,
        left_summary=_bundle_summary_dict(left_bundle),
        right_summary=_bundle_summary_dict(right_bundle),
        changed_proteins=changed_proteins,
        changed_ptm_sites=changed_ptm_sites,
        changed_qc_entries=changed_qc_entries,
        changed_pathways=changed_pathways,
        summary=InteractiveResultComparisonSummary(
            left_source_count=len(left_bundle.source_reports),
            right_source_count=len(right_bundle.source_reports),
            changed_protein_count=len(changed_proteins),
            changed_ptm_site_count=len(changed_ptm_sites),
            changed_qc_entry_count=len(changed_qc_entries),
            changed_pathway_count=len(changed_pathways),
            total_change_count=(
                len(changed_proteins)
                + len(changed_ptm_sites)
                + len(changed_qc_entries)
                + len(changed_pathways)
            ),
            total_reason_count=total_reason_count,
        ),
        note=(
            "interactive result comparison preserves changed proteins, PTM sites, QC "
            "entries, and pathways with stable reasons instead of comparing files only"
        ),
    )


def render_interactive_result_comparison_summary_tsv(
    payload: InteractiveResultComparisonPayload,
) -> str:
    """Render one compact comparison summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field, value in (
        ("left_source_count", payload.summary.left_source_count),
        ("right_source_count", payload.summary.right_source_count),
        ("changed_protein_count", payload.summary.changed_protein_count),
        ("changed_ptm_site_count", payload.summary.changed_ptm_site_count),
        ("changed_qc_entry_count", payload.summary.changed_qc_entry_count),
        ("changed_pathway_count", payload.summary.changed_pathway_count),
        ("total_change_count", payload.summary.total_change_count),
        ("total_reason_count", payload.summary.total_reason_count),
        ("note", payload.note),
    ):
        writer.writerow((field, value))
    return buffer.getvalue()


def render_interactive_result_comparison_protein_tsv(
    payload: InteractiveResultComparisonPayload,
) -> str:
    """Render changed proteins inside one comparison payload as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "object_id",
            "status",
            "representative_protein_ref",
            "gene_symbol",
            "left_log2_fold_change",
            "right_log2_fold_change",
            "left_adjusted_p_value",
            "right_adjusted_p_value",
            "left_evidence_tier",
            "right_evidence_tier",
            "reasons",
            "note",
        )
    )
    for entry in payload.changed_proteins:
        writer.writerow(
            (
                entry.object_id,
                entry.status.value,
                _stringify_optional(entry.representative_protein_ref),
                _stringify_optional(entry.gene_symbol),
                _stringify_optional(_maybe_protein(entry.left_protein, "log2_fold_change")),
                _stringify_optional(_maybe_protein(entry.right_protein, "log2_fold_change")),
                _stringify_optional(_maybe_protein(entry.left_protein, "adjusted_p_value")),
                _stringify_optional(_maybe_protein(entry.right_protein, "adjusted_p_value")),
                _stringify_optional(_maybe_protein(entry.left_protein, "evidence_tier")),
                _stringify_optional(_maybe_protein(entry.right_protein, "evidence_tier")),
                _join_reasons(entry.reasons),
                entry.note,
            )
        )
    return buffer.getvalue()


def render_interactive_result_comparison_ptm_site_tsv(
    payload: InteractiveResultComparisonPayload,
) -> str:
    """Render changed PTM sites inside one comparison payload as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "site_key",
            "status",
            "protein_ref",
            "left_log2_fold_change",
            "right_log2_fold_change",
            "left_localization_tier",
            "right_localization_tier",
            "left_protein_correction_status",
            "right_protein_correction_status",
            "reasons",
            "note",
        )
    )
    for entry in payload.changed_ptm_sites:
        writer.writerow(
            (
                entry.site_key,
                entry.status.value,
                _stringify_optional(entry.protein_ref),
                _stringify_optional(_maybe_site(entry.left_site, "log2_fold_change")),
                _stringify_optional(_maybe_site(entry.right_site, "log2_fold_change")),
                _stringify_optional(_maybe_site(entry.left_site, "localization_tier")),
                _stringify_optional(_maybe_site(entry.right_site, "localization_tier")),
                _stringify_optional(
                    _maybe_site(entry.left_site, "protein_correction_status")
                ),
                _stringify_optional(
                    _maybe_site(entry.right_site, "protein_correction_status")
                ),
                _join_reasons(entry.reasons),
                entry.note,
            )
        )
    return buffer.getvalue()


def render_interactive_result_comparison_qc_tsv(
    payload: InteractiveResultComparisonPayload,
) -> str:
    """Render changed QC entries inside one comparison payload as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "qc_id",
            "status",
            "scope",
            "entity_id",
            "left_status",
            "right_status",
            "left_severity",
            "right_severity",
            "reasons",
            "note",
        )
    )
    for entry in payload.changed_qc_entries:
        writer.writerow(
            (
                entry.qc_id,
                entry.status.value,
                _stringify_optional(entry.scope),
                _stringify_optional(entry.entity_id),
                _stringify_optional(_maybe_qc(entry.left_qc_entry, "status")),
                _stringify_optional(_maybe_qc(entry.right_qc_entry, "status")),
                _stringify_optional(_maybe_qc(entry.left_qc_entry, "severity")),
                _stringify_optional(_maybe_qc(entry.right_qc_entry, "severity")),
                _join_reasons(entry.reasons),
                entry.note,
            )
        )
    return buffer.getvalue()


def render_interactive_result_comparison_pathway_tsv(
    payload: InteractiveResultComparisonPayload,
) -> str:
    """Render changed pathways inside one comparison payload as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "pathway_id",
            "status",
            "pathway_name",
            "left_activity_score_delta",
            "right_activity_score_delta",
            "left_enrichment_ratio",
            "right_enrichment_ratio",
            "left_adjusted_p_value",
            "right_adjusted_p_value",
            "reasons",
            "note",
        )
    )
    for entry in payload.changed_pathways:
        writer.writerow(
            (
                entry.pathway_id,
                entry.status.value,
                _stringify_optional(entry.pathway_name),
                _stringify_optional(
                    _maybe_pathway(entry.left_pathway, "activity_score_delta")
                ),
                _stringify_optional(
                    _maybe_pathway(entry.right_pathway, "activity_score_delta")
                ),
                _stringify_optional(_maybe_pathway(entry.left_pathway, "enrichment_ratio")),
                _stringify_optional(_maybe_pathway(entry.right_pathway, "enrichment_ratio")),
                _stringify_optional(_maybe_pathway(entry.left_pathway, "adjusted_p_value")),
                _stringify_optional(_maybe_pathway(entry.right_pathway, "adjusted_p_value")),
                _join_reasons(entry.reasons),
                entry.note,
            )
        )
    return buffer.getvalue()


def _build_side_bundle(
    *,
    biological_report_dir: Path | None,
    ptm_report_dir: Path | None,
    run_qc_assessment_tsv_paths: tuple[Path, ...],
    side_label: str,
) -> InteractiveResultBundle:
    if (
        biological_report_dir is None
        and ptm_report_dir is None
        and not run_qc_assessment_tsv_paths
    ):
        raise ValueError(
            f"{side_label} result comparison input requires at least one governed biological report, PTM report, or QC assessment input"
        )
    return build_interactive_result_bundle_from_artifacts(
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
    )


def _build_protein_changes(
    left_bundle: InteractiveResultBundle,
    right_bundle: InteractiveResultBundle,
) -> tuple[InteractiveResultProteinComparisonEntry, ...]:
    left_by_id = {entry.object_id: entry for entry in left_bundle.proteins}
    right_by_id = {entry.object_id: entry for entry in right_bundle.proteins}
    entries: list[InteractiveResultProteinComparisonEntry] = []
    for object_id in sorted(set(left_by_id) | set(right_by_id)):
        left_entry = left_by_id.get(object_id)
        right_entry = right_by_id.get(object_id)
        reasons = _presence_reasons(left_entry, right_entry)
        if left_entry is not None and right_entry is not None:
            _append_optional_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.LOG2_FOLD_CHANGE_CHANGED,
                field_name="log2_fold_change",
                left_value=left_entry.log2_fold_change,
                right_value=right_entry.log2_fold_change,
            )
            _append_optional_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.ADJUSTED_P_VALUE_CHANGED,
                field_name="adjusted_p_value",
                left_value=left_entry.adjusted_p_value,
                right_value=right_entry.adjusted_p_value,
            )
            _append_optional_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.SIGNIFICANCE_CHANGED,
                field_name="significant",
                left_value=left_entry.significant,
                right_value=right_entry.significant,
            )
            _append_optional_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.EVIDENCE_TIER_CHANGED,
                field_name="evidence_tier",
                left_value=left_entry.evidence_tier,
                right_value=right_entry.evidence_tier,
            )
            _append_tuple_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.WARNING_CODES_CHANGED,
                field_name="warning_codes",
                left_value=left_entry.warning_codes,
                right_value=right_entry.warning_codes,
            )
            _append_tuple_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.LINKED_PEPTIDES_CHANGED,
                field_name="peptide_ids",
                left_value=left_entry.peptide_ids,
                right_value=right_entry.peptide_ids,
            )
            _append_tuple_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.LINKED_SITES_CHANGED,
                field_name="ptm_site_keys",
                left_value=left_entry.ptm_site_keys,
                right_value=right_entry.ptm_site_keys,
            )
            _append_tuple_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.LINKED_PATHWAYS_CHANGED,
                field_name="pathway_ids",
                left_value=left_entry.pathway_ids,
                right_value=right_entry.pathway_ids,
            )
        if not reasons:
            continue
        entries.append(
            InteractiveResultProteinComparisonEntry(
                object_id=object_id,
                status=_comparison_status(left_entry, right_entry),
                representative_protein_ref=(
                    None
                    if left_entry is None and right_entry is None
                    else (
                        left_entry.representative_protein_ref
                        if left_entry is not None
                        else right_entry.representative_protein_ref
                    )
                ),
                gene_symbol=(
                    left_entry.gene_symbol
                    if left_entry is not None and left_entry.gene_symbol is not None
                    else (None if right_entry is None else right_entry.gene_symbol)
                ),
                left_protein=left_entry,
                right_protein=right_entry,
                reasons=tuple(reasons),
                note=_reason_note("protein", reasons),
            )
        )
    return tuple(entries)


def _build_ptm_site_changes(
    left_bundle: InteractiveResultBundle,
    right_bundle: InteractiveResultBundle,
) -> tuple[InteractiveResultPtmSiteComparisonEntry, ...]:
    left_by_key = {entry.site_key: entry for entry in left_bundle.ptm_sites}
    right_by_key = {entry.site_key: entry for entry in right_bundle.ptm_sites}
    entries: list[InteractiveResultPtmSiteComparisonEntry] = []
    for site_key in sorted(set(left_by_key) | set(right_by_key)):
        left_entry = left_by_key.get(site_key)
        right_entry = right_by_key.get(site_key)
        reasons = _presence_reasons(left_entry, right_entry)
        if left_entry is not None and right_entry is not None:
            _append_optional_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.LOG2_FOLD_CHANGE_CHANGED,
                field_name="log2_fold_change",
                left_value=left_entry.log2_fold_change,
                right_value=right_entry.log2_fold_change,
            )
            _append_optional_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.ADJUSTED_P_VALUE_CHANGED,
                field_name="adjusted_p_value",
                left_value=left_entry.adjusted_p_value,
                right_value=right_entry.adjusted_p_value,
            )
            _append_optional_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.LOCALIZATION_TIER_CHANGED,
                field_name="localization_tier",
                left_value=left_entry.localization_tier,
                right_value=right_entry.localization_tier,
            )
            _append_optional_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.PROTEIN_CORRECTION_STATUS_CHANGED,
                field_name="protein_correction_status",
                left_value=left_entry.protein_correction_status,
                right_value=right_entry.protein_correction_status,
            )
            _append_optional_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.MECHANISM_CLASS_CHANGED,
                field_name="mechanism_class",
                left_value=left_entry.mechanism_class,
                right_value=right_entry.mechanism_class,
            )
            _append_tuple_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.WARNING_CODES_CHANGED,
                field_name="warning_codes",
                left_value=left_entry.warning_codes,
                right_value=right_entry.warning_codes,
            )
            _append_tuple_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.CLAIM_IDS_CHANGED,
                field_name="claim_ids",
                left_value=left_entry.claim_ids,
                right_value=right_entry.claim_ids,
            )
        if not reasons:
            continue
        entries.append(
            InteractiveResultPtmSiteComparisonEntry(
                site_key=site_key,
                status=_comparison_status(left_entry, right_entry),
                protein_ref=(
                    left_entry.protein_ref
                    if left_entry is not None
                    else (None if right_entry is None else right_entry.protein_ref)
                ),
                left_site=left_entry,
                right_site=right_entry,
                reasons=tuple(reasons),
                note=_reason_note("PTM site", reasons),
            )
        )
    return tuple(entries)


def _build_qc_changes(
    left_bundle: InteractiveResultBundle,
    right_bundle: InteractiveResultBundle,
) -> tuple[InteractiveResultQcComparisonEntry, ...]:
    left_by_id = {entry.qc_id: entry for entry in left_bundle.qc_entries}
    right_by_id = {entry.qc_id: entry for entry in right_bundle.qc_entries}
    entries: list[InteractiveResultQcComparisonEntry] = []
    for qc_id in sorted(set(left_by_id) | set(right_by_id)):
        left_entry = left_by_id.get(qc_id)
        right_entry = right_by_id.get(qc_id)
        reasons = _presence_reasons(left_entry, right_entry)
        if left_entry is not None and right_entry is not None:
            _append_optional_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.QC_STATUS_CHANGED,
                field_name="status",
                left_value=left_entry.status,
                right_value=right_entry.status,
            )
            _append_optional_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.QC_SEVERITY_CHANGED,
                field_name="severity",
                left_value=left_entry.severity,
                right_value=right_entry.severity,
            )
            _append_tuple_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.QC_REASON_CODES_CHANGED,
                field_name="reason_codes",
                left_value=left_entry.reason_codes,
                right_value=right_entry.reason_codes,
            )
            _append_optional_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.QC_MESSAGE_CHANGED,
                field_name="message",
                left_value=left_entry.message,
                right_value=right_entry.message,
            )
        if not reasons:
            continue
        entries.append(
            InteractiveResultQcComparisonEntry(
                qc_id=qc_id,
                status=_comparison_status(left_entry, right_entry),
                scope=(
                    left_entry.scope
                    if left_entry is not None
                    else (None if right_entry is None else right_entry.scope)
                ),
                entity_id=(
                    left_entry.entity_id
                    if left_entry is not None
                    else (None if right_entry is None else right_entry.entity_id)
                ),
                left_qc_entry=left_entry,
                right_qc_entry=right_entry,
                reasons=tuple(reasons),
                note=_reason_note("QC entry", reasons),
            )
        )
    return tuple(entries)


def _build_pathway_changes(
    left_bundle: InteractiveResultBundle,
    right_bundle: InteractiveResultBundle,
) -> tuple[InteractiveResultPathwayComparisonEntry, ...]:
    left_by_id = {entry.pathway_id: entry for entry in left_bundle.pathways}
    right_by_id = {entry.pathway_id: entry for entry in right_bundle.pathways}
    entries: list[InteractiveResultPathwayComparisonEntry] = []
    for pathway_id in sorted(set(left_by_id) | set(right_by_id)):
        left_entry = left_by_id.get(pathway_id)
        right_entry = right_by_id.get(pathway_id)
        reasons = _presence_reasons(left_entry, right_entry)
        if left_entry is not None and right_entry is not None:
            _append_optional_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.ACTIVITY_SCORE_CHANGED,
                field_name="activity_score_delta",
                left_value=left_entry.activity_score_delta,
                right_value=right_entry.activity_score_delta,
            )
            _append_optional_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.ENRICHMENT_RATIO_CHANGED,
                field_name="enrichment_ratio",
                left_value=left_entry.enrichment_ratio,
                right_value=right_entry.enrichment_ratio,
            )
            _append_optional_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.PATHWAY_ADJUSTED_P_VALUE_CHANGED,
                field_name="adjusted_p_value",
                left_value=left_entry.adjusted_p_value,
                right_value=right_entry.adjusted_p_value,
            )
            _append_optional_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.FOREGROUND_OVERLAP_CHANGED,
                field_name="foreground_overlap_count",
                left_value=left_entry.foreground_overlap_count,
                right_value=right_entry.foreground_overlap_count,
            )
            _append_optional_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.PATHWAY_CONFIDENCE_CHANGED,
                field_name="comparison_confidence_status",
                left_value=left_entry.comparison_confidence_status,
                right_value=right_entry.comparison_confidence_status,
            )
            _append_tuple_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.SUPPORTING_PROTEINS_CHANGED,
                field_name="supporting_protein_refs",
                left_value=left_entry.supporting_protein_refs,
                right_value=right_entry.supporting_protein_refs,
            )
            _append_tuple_change_reason(
                reasons,
                code=InteractiveResultComparisonReasonCode.UNRESOLVED_MEMBERS_CHANGED,
                field_name="unresolved_member_ids",
                left_value=left_entry.unresolved_member_ids,
                right_value=right_entry.unresolved_member_ids,
            )
        if not reasons:
            continue
        entries.append(
            InteractiveResultPathwayComparisonEntry(
                pathway_id=pathway_id,
                status=_comparison_status(left_entry, right_entry),
                pathway_name=(
                    left_entry.pathway_name
                    if left_entry is not None and left_entry.pathway_name is not None
                    else (None if right_entry is None else right_entry.pathway_name)
                ),
                left_pathway=left_entry,
                right_pathway=right_entry,
                reasons=tuple(reasons),
                note=_reason_note("pathway", reasons),
            )
        )
    return tuple(entries)


def _presence_reasons(
    left_entry: object | None,
    right_entry: object | None,
) -> list[InteractiveResultComparisonReason]:
    if left_entry is None and right_entry is not None:
        return [
            InteractiveResultComparisonReason(
                code=InteractiveResultComparisonReasonCode.ENTITY_ADDED,
                field_name="presence",
                left_value=None,
                right_value="present",
                message="entity is absent on the left and present on the right",
            )
        ]
    if left_entry is not None and right_entry is None:
        return [
            InteractiveResultComparisonReason(
                code=InteractiveResultComparisonReasonCode.ENTITY_REMOVED,
                field_name="presence",
                left_value="present",
                right_value=None,
                message="entity is present on the left and absent on the right",
            )
        ]
    return []


def _comparison_status(
    left_entry: object | None,
    right_entry: object | None,
) -> InteractiveResultComparisonStatus:
    if left_entry is None:
        return InteractiveResultComparisonStatus.ADDED
    if right_entry is None:
        return InteractiveResultComparisonStatus.REMOVED
    return InteractiveResultComparisonStatus.CHANGED


def _append_optional_change_reason(
    reasons: list[InteractiveResultComparisonReason],
    *,
    code: InteractiveResultComparisonReasonCode,
    field_name: str,
    left_value: object | None,
    right_value: object | None,
) -> None:
    if not _values_differ(left_value, right_value):
        return
    reasons.append(
        InteractiveResultComparisonReason(
            code=code,
            field_name=field_name,
            left_value=_stringify_optional(left_value),
            right_value=_stringify_optional(right_value),
            message=f"{field_name.replace('_', ' ')} changed between the two result bundles",
        )
    )


def _append_tuple_change_reason(
    reasons: list[InteractiveResultComparisonReason],
    *,
    code: InteractiveResultComparisonReasonCode,
    field_name: str,
    left_value: tuple[str, ...],
    right_value: tuple[str, ...],
) -> None:
    if left_value == right_value:
        return
    reasons.append(
        InteractiveResultComparisonReason(
            code=code,
            field_name=field_name,
            left_value=_stringify_optional(left_value),
            right_value=_stringify_optional(right_value),
            message=f"{field_name.replace('_', ' ')} changed between the two result bundles",
        )
    )


def _values_differ(left_value: object | None, right_value: object | None) -> bool:
    if isinstance(left_value, float) or isinstance(right_value, float):
        if left_value is None or right_value is None:
            return left_value != right_value
        if not isinstance(left_value, (int, float)) or not isinstance(
            right_value,
            (int, float),
        ):
            return left_value != right_value
        return not math.isclose(float(left_value), float(right_value), abs_tol=1e-9)
    return left_value != right_value


def _bundle_summary_dict(
    bundle: InteractiveResultBundle,
) -> dict[str, int | bool]:
    return {
        "biological_report_available": bundle.summary.biological_report_available,
        "ptm_report_available": bundle.summary.ptm_report_available,
        "run_qc_input_count": bundle.summary.run_qc_input_count,
        "sample_count": bundle.summary.sample_count,
        "protein_count": bundle.summary.protein_count,
        "peptide_count": bundle.summary.peptide_count,
        "ptm_site_count": bundle.summary.ptm_site_count,
        "pathway_count": bundle.summary.pathway_count,
        "qc_entry_count": bundle.summary.qc_entry_count,
        "card_count": bundle.summary.card_count,
        "graph_node_count": bundle.summary.graph_node_count,
        "graph_edge_count": bundle.summary.graph_edge_count,
        "plot_count": bundle.summary.plot_count,
    }


def _stringify_optional(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, tuple):
        return ";".join(str(entry) for entry in value)
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _join_reasons(reasons: tuple[InteractiveResultComparisonReason, ...]) -> str:
    return "; ".join(f"{reason.code.value}: {reason.message}" for reason in reasons)


def _reason_note(
    entity_label: str,
    reasons: list[InteractiveResultComparisonReason],
) -> str:
    joined_codes = ", ".join(reason.code.value for reason in reasons)
    return f"{entity_label} changed because {joined_codes}"


def _maybe_protein(
    protein: InteractiveResultProtein | None,
    field_name: str,
) -> object | None:
    return None if protein is None else getattr(protein, field_name)


def _maybe_site(
    site: InteractiveResultPtmSite | None,
    field_name: str,
) -> object | None:
    return None if site is None else getattr(site, field_name)


def _maybe_qc(
    qc_entry: InteractiveResultQcEntry | None,
    field_name: str,
) -> object | None:
    return None if qc_entry is None else getattr(qc_entry, field_name)


def _maybe_pathway(
    pathway: InteractiveResultPathway | None,
    field_name: str,
) -> object | None:
    return None if pathway is None else getattr(pathway, field_name)


__all__ = [
    "InteractiveResultComparisonPayload",
    "InteractiveResultComparisonReason",
    "InteractiveResultComparisonReasonCode",
    "InteractiveResultComparisonStatus",
    "InteractiveResultPathwayComparisonEntry",
    "InteractiveResultProteinComparisonEntry",
    "InteractiveResultPtmSiteComparisonEntry",
    "InteractiveResultQcComparisonEntry",
    "InteractiveResultComparisonSummary",
    "build_interactive_result_comparison_from_artifacts",
    "build_interactive_result_comparison_payload",
    "render_interactive_result_comparison_pathway_tsv",
    "render_interactive_result_comparison_protein_tsv",
    "render_interactive_result_comparison_ptm_site_tsv",
    "render_interactive_result_comparison_qc_tsv",
    "render_interactive_result_comparison_summary_tsv",
]
