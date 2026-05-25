# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Advanced PTM workflow execution over governed review surfaces."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.ptm import (
    PtmEvidenceCardPolicy,
    PtmLocalizationColumnMapping,
    PtmMotifComparisonPolicy,
    PtmOccupancyCounterpartEvidenceReport,
    PtmPhosphositeSelectionPolicy,
    PtmProteinCorrectionMode,
    PtmRegulatorEnrichmentPolicy,
    PtmSiteGroupQuantificationReport,
    PtmSiteQuantAmbiguityPolicy,
    PtmSiteQuantificationReport,
    build_ptm_occupancy_counterpart_report,
    build_ptm_site_quantification_report,
    render_ptm_occupancy_counterpart_tsv,
    render_ptm_site_group_quant_matrix_tsv,
    render_ptm_site_group_quant_missingness_tsv,
    render_ptm_site_group_quant_summary_tsv,
    render_ptm_site_quant_excluded_tsv,
)
from bijux_proteomics.quantification import NormalizationMethod, parse_ms1_feature_table
from bijux_proteomics.workflow.ptm_site_workflow import (
    PtmSiteWorkflowBundle,
    PtmSiteWorkflowExportManifest,
    build_ptm_site_workflow_bundle,
    export_ptm_site_workflow_bundle,
)
from bijux_proteomics.workflow.result_types import (
    BiologyResult,
    artifact_name_map,
    build_rejected_evidence_entries_from_issue_rows,
    build_result_warning,
)
from bijux_proteomics_foundation import JsonModel


class AdvancedPtmWorkflowConfig(JsonModel):
    """Config for the advanced PTM workflow owner."""

    model_config = ConfigDict(extra="forbid")

    evidence_tsv_path: Path
    proteins_fasta_path: Path
    feature_tsv_path: Path
    design_tsv_path: Path
    output_dir: Path
    mapping: PtmLocalizationColumnMapping | None = None
    fragment_support_json_path: Path | None = None
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN
    condition_a: str | None = None
    condition_b: str | None = None
    protein_correction_mode: PtmProteinCorrectionMode = PtmProteinCorrectionMode.NONE
    batch_field: str = "batch"
    covariate_fields: tuple[str, ...] = Field(default_factory=tuple)
    pairing_field: str | None = None
    motif_flank_size: int = Field(default=7, ge=1)
    motif_selection_policy: PtmPhosphositeSelectionPolicy | None = None
    motif_comparison_policy: PtmMotifComparisonPolicy | None = None
    annotation_tsv_path: Path | None = None
    annotation_target_species: str | None = None
    regulator_enrichment_policy: PtmRegulatorEnrichmentPolicy | None = None
    evidence_card_policy: PtmEvidenceCardPolicy | None = None


class AdvancedPtmWorkflowSummary(JsonModel):
    """Compact summary over one advanced PTM workflow run."""

    model_config = ConfigDict(extra="forbid")

    total_evidence_row_count: int = Field(..., ge=0)
    accepted_evidence_count: int = Field(..., ge=0)
    rejected_evidence_count: int = Field(..., ge=0)
    site_mapping_row_count: int = Field(..., ge=0)
    localization_entry_count: int = Field(..., ge=0)
    exact_site_row_count: int = Field(..., ge=0)
    ambiguous_group_row_count: int = Field(..., ge=0)
    excluded_ambiguous_row_count: int = Field(..., ge=0)
    differential_site_count: int = Field(..., ge=0)
    occupancy_entry_count: int = Field(..., ge=0)
    occupancy_missing_counterpart_count: int = Field(..., ge=0)
    occupancy_ambiguous_site_count: int = Field(..., ge=0)
    motif_term_count: int = Field(..., ge=0)
    regulator_enrichment_entry_count: int = Field(..., ge=0)
    evidence_card_count: int = Field(..., ge=0)
    narrative_claim_count: int = Field(..., ge=0)
    protein_correction_mode: PtmProteinCorrectionMode


class AdvancedPtmWorkflowArtifactPaths(JsonModel):
    """Advanced PTM artifact paths written into the output directory."""

    model_config = ConfigDict(extra="forbid")

    summary_tsv: str = Field(..., min_length=1)
    ptm_workflow_manifest_json: str = Field(..., min_length=1)
    ptm_report_manifest_json: str = Field(..., min_length=1)
    site_mapping_tsv: str = Field(..., min_length=1)
    localization_tsv: str = Field(..., min_length=1)
    exact_site_matrix_tsv: str = Field(..., min_length=1)
    differential_tsv: str | None = None
    ambiguity_group_summary_tsv: str | None = None
    ambiguity_group_matrix_tsv: str | None = None
    ambiguity_group_missingness_tsv: str | None = None
    excluded_ambiguous_sites_tsv: str = Field(..., min_length=1)
    occupancy_counterpart_tsv: str = Field(..., min_length=1)
    motif_term_tsv: str | None = None
    regulator_enrichment_tsv: str | None = None
    evidence_card_tsv: str | None = None
    evidence_claim_tsv: str | None = None


class AdvancedPtmWorkflowManifest(JsonModel):
    """Stable manifest over one advanced PTM workflow output directory."""

    model_config = ConfigDict(extra="forbid")

    summary: AdvancedPtmWorkflowSummary
    artifacts: AdvancedPtmWorkflowArtifactPaths
    ptm_workflow_manifest: PtmSiteWorkflowExportManifest
    note: str = Field(..., min_length=1)


class AdvancedPtmWorkflowReport(BiologyResult):
    """Advanced PTM workflow report with explicit ambiguity and occupancy review."""

    model_config = ConfigDict(extra="forbid")

    ptm_workflow: PtmSiteWorkflowBundle
    ptm_workflow_manifest: PtmSiteWorkflowExportManifest
    exact_site_exclusion_audit: PtmSiteQuantificationReport
    ambiguity_group_quantification: PtmSiteGroupQuantificationReport | None = None
    occupancy_counterpart_report: PtmOccupancyCounterpartEvidenceReport
    summary: AdvancedPtmWorkflowSummary
    manifest: AdvancedPtmWorkflowManifest
    note: str = Field(..., min_length=1)


def run_advanced_ptm_workflow(
    config: AdvancedPtmWorkflowConfig,
) -> AdvancedPtmWorkflowReport:
    """Run the advanced PTM workflow and write one durable review directory."""

    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    base_report = build_ptm_site_workflow_bundle(
        config.evidence_tsv_path,
        config.proteins_fasta_path,
        feature_tsv_path=config.feature_tsv_path,
        design_path=config.design_tsv_path,
        mapping=config.mapping,
        fragment_support_json_path=config.fragment_support_json_path,
        ambiguity_policy=PtmSiteQuantAmbiguityPolicy.PRESERVE,
        normalization_method=config.normalization_method,
        condition_a=config.condition_a,
        condition_b=config.condition_b,
        protein_correction_mode=config.protein_correction_mode,
        batch_field=config.batch_field,
        covariate_fields=tuple(dict.fromkeys(config.covariate_fields)),
        pairing_field=config.pairing_field,
        motif_flank_size=config.motif_flank_size,
        motif_selection_policy=config.motif_selection_policy,
        motif_comparison_policy=config.motif_comparison_policy,
        annotation_tsv_path=config.annotation_tsv_path,
        annotation_target_species=config.annotation_target_species,
        regulator_enrichment_policy=config.regulator_enrichment_policy,
        evidence_card_policy=config.evidence_card_policy,
    )
    workflow_manifest = export_ptm_site_workflow_bundle(base_report, output_dir)
    workflow_manifest_path = output_dir / "ptm_site_workflow_manifest.json"
    workflow_manifest_path.write_text(
        workflow_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )

    feature_records = tuple(
        parse_ms1_feature_table(config.feature_tsv_path).accepted_records
    )
    exact_site_quantification = _require_site_quantification(base_report)
    exact_site_exclusion_audit = build_ptm_site_quantification_report(
        base_report.report.site_table,
        feature_records=feature_records,
        ambiguity_policy=PtmSiteQuantAmbiguityPolicy.EXCLUDE,
    )
    ambiguity_group_quantification = exact_site_quantification.ambiguous_group_quantification
    occupancy_counterpart_report = build_ptm_occupancy_counterpart_report(
        base_report.report.site_table,
        feature_records=feature_records,
    )

    ambiguity_group_summary_name = None
    ambiguity_group_matrix_name = None
    ambiguity_group_missingness_name = None
    if ambiguity_group_quantification is not None:
        ambiguity_group_summary_name = "advanced_ptm_site_group_summary.tsv"
        ambiguity_group_matrix_name = "advanced_ptm_site_group_matrix.tsv"
        ambiguity_group_missingness_name = "advanced_ptm_site_group_missingness.tsv"
        (output_dir / ambiguity_group_summary_name).write_text(
            render_ptm_site_group_quant_summary_tsv(ambiguity_group_quantification),
            encoding="utf-8",
        )
        (output_dir / ambiguity_group_matrix_name).write_text(
            render_ptm_site_group_quant_matrix_tsv(ambiguity_group_quantification),
            encoding="utf-8",
        )
        (output_dir / ambiguity_group_missingness_name).write_text(
            render_ptm_site_group_quant_missingness_tsv(ambiguity_group_quantification),
            encoding="utf-8",
        )

    excluded_name = "advanced_ptm_excluded_ambiguous_sites.tsv"
    occupancy_name = "advanced_ptm_occupancy_counterparts.tsv"
    summary_name = "advanced_ptm_summary.tsv"

    (output_dir / excluded_name).write_text(
        render_advanced_ptm_excluded_ambiguity_tsv(exact_site_exclusion_audit),
        encoding="utf-8",
    )
    (output_dir / occupancy_name).write_text(
        render_ptm_occupancy_counterpart_tsv(occupancy_counterpart_report),
        encoding="utf-8",
    )

    report_manifest = workflow_manifest.ptm_report_manifest
    summary = AdvancedPtmWorkflowSummary(
        total_evidence_row_count=base_report.summary.total_evidence_row_count,
        accepted_evidence_count=base_report.summary.accepted_evidence_count,
        rejected_evidence_count=base_report.summary.rejected_evidence_count,
        site_mapping_row_count=base_report.report.summary.site_row_count,
        localization_entry_count=base_report.report.summary.localization_entry_count,
        exact_site_row_count=exact_site_quantification.summary.site_row_count,
        ambiguous_group_row_count=(
            0
            if ambiguity_group_quantification is None
            else ambiguity_group_quantification.summary.group_row_count
        ),
        excluded_ambiguous_row_count=exact_site_exclusion_audit.summary.excluded_ambiguous_row_count,
        differential_site_count=base_report.report.summary.differential_site_count,
        occupancy_entry_count=len(occupancy_counterpart_report.entries),
        occupancy_missing_counterpart_count=occupancy_counterpart_report.missing_counterpart_count,
        occupancy_ambiguous_site_count=occupancy_counterpart_report.ambiguous_site_count,
        motif_term_count=base_report.report.summary.motif_term_count,
        regulator_enrichment_entry_count=(
            0
            if base_report.report.regulator_enrichment is None
            else len(base_report.report.regulator_enrichment.entries)
        ),
        evidence_card_count=base_report.report.summary.evidence_card_count,
        narrative_claim_count=base_report.report.summary.narrative_claim_count,
        protein_correction_mode=config.protein_correction_mode,
    )
    (output_dir / summary_name).write_text(
        render_advanced_ptm_workflow_summary_tsv(summary),
        encoding="utf-8",
    )

    manifest = AdvancedPtmWorkflowManifest(
        summary=summary,
        artifacts=AdvancedPtmWorkflowArtifactPaths(
            summary_tsv=summary_name,
            ptm_workflow_manifest_json=workflow_manifest_path.name,
            ptm_report_manifest_json=workflow_manifest.artifacts.ptm_report_manifest_json,
            site_mapping_tsv=report_manifest.artifacts.site_tsv,
            localization_tsv=report_manifest.artifacts.localization_tsv,
            exact_site_matrix_tsv=_required_artifact_name(
                report_manifest.artifacts.site_quant_matrix_tsv,
                artifact_name="site_quant_matrix_tsv",
            ),
            differential_tsv=report_manifest.artifacts.differential_tsv,
            ambiguity_group_summary_tsv=ambiguity_group_summary_name,
            ambiguity_group_matrix_tsv=ambiguity_group_matrix_name,
            ambiguity_group_missingness_tsv=ambiguity_group_missingness_name,
            excluded_ambiguous_sites_tsv=excluded_name,
            occupancy_counterpart_tsv=occupancy_name,
            motif_term_tsv=report_manifest.artifacts.motif_term_tsv,
            regulator_enrichment_tsv=report_manifest.artifacts.regulator_enrichment_tsv,
            evidence_card_tsv=report_manifest.artifacts.evidence_card_tsv,
            evidence_claim_tsv=report_manifest.artifacts.evidence_claim_tsv,
        ),
        ptm_workflow_manifest=workflow_manifest,
        note=(
            "advanced ptm workflow preserves one exact-site matrix for resolved "
            "sites, one ambiguity-group matrix for unresolved localization, one "
            "explicit exclusion audit, and one occupancy review alongside the "
            "governed ptm report bundle"
        ),
    )
    manifest_path = output_dir / "advanced_ptm_workflow_manifest.json"
    manifest_path.write_text(manifest.to_stable_json() + "\n", encoding="utf-8")

    return AdvancedPtmWorkflowReport(
        ptm_workflow=base_report,
        ptm_workflow_manifest=workflow_manifest,
        exact_site_exclusion_audit=exact_site_exclusion_audit,
        ambiguity_group_quantification=ambiguity_group_quantification,
        occupancy_counterpart_report=occupancy_counterpart_report,
        summary=summary,
        manifest=manifest,
        artifacts=artifact_name_map(manifest.artifacts),
        warnings=_build_advanced_ptm_warnings(summary=summary, manifest=manifest),
        rejected_evidence=_build_advanced_ptm_rejected_evidence(
            report=base_report,
            manifest=manifest,
        ),
        note=(
            "advanced ptm workflow composes governed site mapping, localization, "
            "site quantification, protein correction, occupancy review, motif and "
            "regulator interpretation, and evidence cards without duplicating "
            "ambiguous signal into the exact-site matrix"
        ),
    )


def render_advanced_ptm_workflow_summary_tsv(
    summary: AdvancedPtmWorkflowSummary,
) -> str:
    """Render one advanced PTM workflow summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field_name, value in (
        ("total_evidence_row_count", summary.total_evidence_row_count),
        ("accepted_evidence_count", summary.accepted_evidence_count),
        ("rejected_evidence_count", summary.rejected_evidence_count),
        ("site_mapping_row_count", summary.site_mapping_row_count),
        ("localization_entry_count", summary.localization_entry_count),
        ("exact_site_row_count", summary.exact_site_row_count),
        ("ambiguous_group_row_count", summary.ambiguous_group_row_count),
        ("excluded_ambiguous_row_count", summary.excluded_ambiguous_row_count),
        ("differential_site_count", summary.differential_site_count),
        ("occupancy_entry_count", summary.occupancy_entry_count),
        ("occupancy_missing_counterpart_count", summary.occupancy_missing_counterpart_count),
        ("occupancy_ambiguous_site_count", summary.occupancy_ambiguous_site_count),
        ("motif_term_count", summary.motif_term_count),
        ("regulator_enrichment_entry_count", summary.regulator_enrichment_entry_count),
        ("evidence_card_count", summary.evidence_card_count),
        ("narrative_claim_count", summary.narrative_claim_count),
        ("protein_correction_mode", summary.protein_correction_mode.value),
    ):
        writer.writerow((field_name, value))
    return handle.getvalue()


def _build_advanced_ptm_warnings(
    *,
    summary: AdvancedPtmWorkflowSummary,
    manifest: AdvancedPtmWorkflowManifest,
) -> tuple:
    warnings = []
    if summary.rejected_evidence_count > 0:
        warnings.append(
            build_result_warning(
                warning_id="advanced_ptm:rejected_evidence",
                warning_code="rejected_evidence_present",
                source_surface="advanced_ptm_workflow",
                message=(
                    f"advanced PTM rejected {summary.rejected_evidence_count} evidence rows "
                    "during localization parsing"
                ),
                related_artifact=manifest.ptm_workflow_manifest.artifacts.rejected_evidence_tsv,
            )
        )
    if summary.excluded_ambiguous_row_count > 0:
        warnings.append(
            build_result_warning(
                warning_id="advanced_ptm:excluded_ambiguous_sites",
                warning_code="excluded_ambiguous_site_present",
                source_surface="advanced_ptm_workflow",
                message=(
                    f"advanced PTM excluded {summary.excluded_ambiguous_row_count} ambiguous rows "
                    "from the exact-site matrix"
                ),
                related_artifact=manifest.artifacts.excluded_ambiguous_sites_tsv,
            )
        )
    if summary.occupancy_missing_counterpart_count > 0:
        warnings.append(
            build_result_warning(
                warning_id="advanced_ptm:missing_occupancy_counterpart",
                warning_code="missing_occupancy_counterpart",
                source_surface="advanced_ptm_workflow",
                message=(
                    "advanced PTM found "
                    f"{summary.occupancy_missing_counterpart_count} occupancy rows without counterparts"
                ),
                related_artifact=manifest.artifacts.occupancy_counterpart_tsv,
            )
        )
    return tuple(warnings)


def _build_advanced_ptm_rejected_evidence(
    *,
    report: PtmSiteWorkflowBundle,
    manifest: AdvancedPtmWorkflowManifest,
) -> tuple:
    return build_rejected_evidence_entries_from_issue_rows(
        report.evidence_parse_report.rejected_rows,
        source_surface="advanced_ptm_workflow",
        related_artifact=manifest.ptm_workflow_manifest.artifacts.rejected_evidence_tsv,
        entity_prefix="ptm_evidence_row",
    )


def render_advanced_ptm_excluded_ambiguity_tsv(
    report: PtmSiteQuantificationReport,
) -> str:
    """Render the exact-site exclusion audit ledger as TSV."""

    return render_ptm_site_quant_excluded_tsv(report)


def _require_site_quantification(
    report: PtmSiteWorkflowBundle,
) -> PtmSiteQuantificationReport:
    site_quantification = report.report.site_quantification
    if site_quantification is None:
        raise ValueError(
            "advanced ptm workflow requires feature-backed site quantification"
        )
    return site_quantification


def _required_artifact_name(name: str | None, *, artifact_name: str) -> str:
    if name is None:
        raise ValueError(f"advanced ptm workflow requires {artifact_name}")
    return name


__all__ = [
    "AdvancedPtmWorkflowArtifactPaths",
    "AdvancedPtmWorkflowConfig",
    "AdvancedPtmWorkflowManifest",
    "AdvancedPtmWorkflowReport",
    "AdvancedPtmWorkflowSummary",
    "render_advanced_ptm_excluded_ambiguity_tsv",
    "render_advanced_ptm_workflow_summary_tsv",
    "run_advanced_ptm_workflow",
]
