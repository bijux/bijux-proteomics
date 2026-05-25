# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Advanced MaxQuant LFQ workflow execution over governed review surfaces."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import MaxquantPeptideReviewEntry
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification import NormalizationMethod
from bijux_proteomics.workflow.biological_reporting import (
    BiologicalResultSelectionPolicy,
    VolcanoReviewPolicy,
)
from bijux_proteomics.workflow.maxquant_biological_workflow import (
    MaxquantBiologicalWorkflowBundle,
    MaxquantBiologicalWorkflowExportManifest,
    MaxquantFilteredProteinGroupEntry,
    MaxquantProteinGroupAcceptancePolicy,
    build_maxquant_biological_workflow_bundle,
    write_maxquant_biological_workflow_bundle,
    render_filtered_maxquant_protein_groups_tsv,
)
from bijux_proteomics.workflow.result_types import (
    BiologyResult,
    artifact_name_map,
    build_rejected_evidence_entry,
    build_result_warning,
)
from bijux_proteomics_foundation import JsonModel


class AdvancedMaxquantWorkflowConfig(JsonModel):
    """Config for the advanced MaxQuant LFQ workflow owner."""

    model_config = ConfigDict(extra="forbid")

    evidence_txt_path: Path
    peptides_txt_path: Path
    protein_groups_txt_path: Path
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
    acceptance_policy: MaxquantProteinGroupAcceptancePolicy | None = None
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN
    condition_a: str | None = None
    condition_b: str | None = None
    selection_policy: BiologicalResultSelectionPolicy | None = None
    volcano_policy: VolcanoReviewPolicy | None = None


class AdvancedMaxquantWorkflowSummary(JsonModel):
    """Compact summary over one advanced MaxQuant LFQ workflow run."""

    model_config = ConfigDict(extra="forbid")

    imported_evidence_count: int = Field(..., ge=0)
    accepted_protein_group_count: int = Field(..., ge=0)
    excluded_reverse_or_contaminant_count: int = Field(..., ge=0)
    additional_filtered_protein_group_count: int = Field(..., ge=0)
    biological_foreground_protein_count: int = Field(..., ge=0)
    peptide_contribution_count: int = Field(..., ge=0)
    significant_protein_count: int = Field(..., ge=0)
    supported_claim_count: int = Field(..., ge=0)
    rejected_claim_count: int = Field(..., ge=0)


class AdvancedMaxquantWorkflowArtifactPaths(JsonModel):
    """Advanced MaxQuant artifact paths written into the output directory."""

    model_config = ConfigDict(extra="forbid")

    summary_tsv: str = Field(..., min_length=1)
    maxquant_workflow_manifest_json: str = Field(..., min_length=1)
    biological_report_manifest_json: str = Field(..., min_length=1)
    excluded_protein_groups_tsv: str = Field(..., min_length=1)
    peptide_contribution_tsv: str = Field(..., min_length=1)
    supported_claim_tsv: str | None = None
    rejected_claim_tsv: str | None = None


class AdvancedMaxquantWorkflowManifest(JsonModel):
    """Stable manifest over one advanced MaxQuant workflow output directory."""

    model_config = ConfigDict(extra="forbid")

    summary: AdvancedMaxquantWorkflowSummary
    artifacts: AdvancedMaxquantWorkflowArtifactPaths
    maxquant_workflow_manifest: MaxquantBiologicalWorkflowExportManifest
    note: str = Field(..., min_length=1)


class AdvancedMaxquantPeptideContributionEntry(JsonModel):
    """One peptide carried into the accepted MaxQuant LFQ foreground."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    representative_protein_ref: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    modified_sequence: str | None = None
    leading_razor_protein: str | None = None
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    intensity: float | None = Field(default=None, ge=0.0)
    msms_count: int | None = Field(default=None, ge=0)


class AdvancedMaxquantWorkflowReport(BiologyResult):
    """Advanced MaxQuant workflow report with exported review outputs."""

    model_config = ConfigDict(extra="forbid")

    maxquant_workflow: MaxquantBiologicalWorkflowBundle
    maxquant_workflow_manifest: MaxquantBiologicalWorkflowExportManifest
    excluded_protein_groups: tuple[MaxquantFilteredProteinGroupEntry, ...] = Field(
        default_factory=tuple
    )
    peptide_contributions: tuple[AdvancedMaxquantPeptideContributionEntry, ...] = Field(
        default_factory=tuple
    )
    summary: AdvancedMaxquantWorkflowSummary
    manifest: AdvancedMaxquantWorkflowManifest
    note: str = Field(..., min_length=1)


def run_advanced_maxquant_workflow(
    config: AdvancedMaxquantWorkflowConfig,
) -> AdvancedMaxquantWorkflowReport:
    """Run the advanced MaxQuant workflow and write one durable review directory."""

    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    design_entries = tuple(
        parse_experimental_design_table(config.design_tsv_path).accepted_entries
    )
    base_report = build_maxquant_biological_workflow_bundle(
        config.evidence_txt_path,
        design_entries,
        peptides_txt_path=config.peptides_txt_path,
        protein_groups_txt_path=config.protein_groups_txt_path,
        proteins_fasta_path=config.proteins_fasta_path,
        protocol_context_tsv_path=config.protocol_context_tsv_path,
        config_path=config.config_path,
        acceptance_policy=config.acceptance_policy,
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
    maxquant_manifest = write_maxquant_biological_workflow_bundle(base_report, output_dir)
    maxquant_manifest_path = output_dir / "maxquant_biological_report_manifest.json"
    maxquant_manifest_path.write_text(
        maxquant_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )

    excluded_groups = tuple(
        row
        for row in base_report.filtered_protein_groups
        if row.contaminant_flag or row.reverse_flag
    )
    peptide_contributions = _build_peptide_contributions(base_report)

    excluded_name = "advanced_maxquant_excluded_protein_groups.tsv"
    peptide_contribution_name = "advanced_maxquant_peptide_contributions.tsv"
    summary_name = "advanced_maxquant_summary.tsv"

    (output_dir / excluded_name).write_text(
        render_filtered_maxquant_protein_groups_tsv(excluded_groups),
        encoding="utf-8",
    )
    (output_dir / peptide_contribution_name).write_text(
        render_advanced_maxquant_peptide_contributions_tsv(peptide_contributions),
        encoding="utf-8",
    )

    claim_validation = base_report.biological_report.claim_validation_report
    summary = AdvancedMaxquantWorkflowSummary(
        imported_evidence_count=base_report.summary.imported_evidence_count,
        accepted_protein_group_count=base_report.summary.accepted_protein_group_count,
        excluded_reverse_or_contaminant_count=len(excluded_groups),
        additional_filtered_protein_group_count=(
            base_report.summary.filtered_protein_group_count - len(excluded_groups)
        ),
        biological_foreground_protein_count=(
            base_report.summary.enrichment_foreground_protein_count
        ),
        peptide_contribution_count=len(peptide_contributions),
        significant_protein_count=base_report.summary.significant_protein_count,
        supported_claim_count=(
            0 if claim_validation is None else claim_validation.summary.supported_claim_count
        ),
        rejected_claim_count=(
            0 if claim_validation is None else claim_validation.summary.rejected_claim_count
        ),
    )
    (output_dir / summary_name).write_text(
        render_advanced_maxquant_workflow_summary_tsv(summary),
        encoding="utf-8",
    )

    manifest = AdvancedMaxquantWorkflowManifest(
        summary=summary,
        artifacts=AdvancedMaxquantWorkflowArtifactPaths(
            summary_tsv=summary_name,
            maxquant_workflow_manifest_json=maxquant_manifest_path.name,
            biological_report_manifest_json=maxquant_manifest.artifacts.biological_manifest_json,
            excluded_protein_groups_tsv=excluded_name,
            peptide_contribution_tsv=peptide_contribution_name,
            supported_claim_tsv=maxquant_manifest.biological_report_manifest.artifacts.supported_claim_tsv,
            rejected_claim_tsv=maxquant_manifest.biological_report_manifest.artifacts.rejected_claim_tsv,
        ),
        maxquant_workflow_manifest=maxquant_manifest,
        note=(
            "advanced maxquant workflow preserves governed import, acceptance-filtered "
            "lfq biology, separate reverse and contaminant exclusions, peptide "
            "contribution review, and downstream biological claims in one directory"
        ),
    )
    manifest_path = output_dir / "advanced_maxquant_workflow_manifest.json"
    manifest_path.write_text(manifest.to_stable_json() + "\n", encoding="utf-8")

    return AdvancedMaxquantWorkflowReport(
        maxquant_workflow=base_report,
        maxquant_workflow_manifest=maxquant_manifest,
        excluded_protein_groups=excluded_groups,
        peptide_contributions=peptide_contributions,
        summary=summary,
        manifest=manifest,
        artifacts=artifact_name_map(manifest.artifacts),
        warnings=_build_advanced_maxquant_warnings(summary=summary, manifest=manifest),
        rejected_evidence=_build_advanced_maxquant_rejected_evidence(
            excluded_groups=excluded_groups,
            manifest=manifest,
        ),
        note=(
            "advanced maxquant workflow composes governed maxquant import, "
            "protein-group acceptance, lfq biology, peptide contribution review, "
            "and explicit reverse or contaminant exclusion reporting"
        ),
    )


def render_advanced_maxquant_workflow_summary_tsv(
    summary: AdvancedMaxquantWorkflowSummary,
) -> str:
    """Render one advanced MaxQuant workflow summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field_name, value in (
        ("imported_evidence_count", summary.imported_evidence_count),
        ("accepted_protein_group_count", summary.accepted_protein_group_count),
        ("excluded_reverse_or_contaminant_count", summary.excluded_reverse_or_contaminant_count),
        ("additional_filtered_protein_group_count", summary.additional_filtered_protein_group_count),
        ("biological_foreground_protein_count", summary.biological_foreground_protein_count),
        ("peptide_contribution_count", summary.peptide_contribution_count),
        ("significant_protein_count", summary.significant_protein_count),
        ("supported_claim_count", summary.supported_claim_count),
        ("rejected_claim_count", summary.rejected_claim_count),
    ):
        writer.writerow((field_name, value))
    return handle.getvalue()


def _build_advanced_maxquant_warnings(
    *,
    summary: AdvancedMaxquantWorkflowSummary,
    manifest: AdvancedMaxquantWorkflowManifest,
) -> tuple:
    warnings = []
    if summary.excluded_reverse_or_contaminant_count > 0:
        warnings.append(
            build_result_warning(
                warning_id="advanced_maxquant:excluded_reverse_or_contaminant",
                warning_code="excluded_reverse_or_contaminant_present",
                source_surface="advanced_maxquant_workflow",
                message=(
                    "advanced MaxQuant excluded "
                    f"{summary.excluded_reverse_or_contaminant_count} reverse or contaminant groups"
                ),
                related_artifact=manifest.artifacts.excluded_protein_groups_tsv,
            )
        )
    if summary.rejected_claim_count > 0:
        warnings.append(
            build_result_warning(
                warning_id="advanced_maxquant:rejected_claims",
                warning_code="rejected_claim_present",
                source_surface="advanced_maxquant_workflow",
                message=(
                    f"advanced MaxQuant carried {summary.rejected_claim_count} rejected biological claims"
                ),
                related_artifact=manifest.artifacts.rejected_claim_tsv,
            )
        )
    return tuple(warnings)


def _build_advanced_maxquant_rejected_evidence(
    *,
    excluded_groups: tuple[MaxquantFilteredProteinGroupEntry, ...],
    manifest: AdvancedMaxquantWorkflowManifest,
) -> tuple:
    entries = []
    for group in excluded_groups:
        if group.reasons:
            for reason in group.reasons:
                entries.append(
                    build_rejected_evidence_entry(
                        evidence_id=(
                            f"advanced_maxquant:{group.entity_id}:{reason.value}"
                        ),
                        source_surface="advanced_maxquant_workflow",
                        reason_code=reason.value,
                        message=(
                            "maxquant protein group was filtered before biological "
                            "reporting"
                        ),
                        related_artifact=manifest.artifacts.excluded_protein_groups_tsv,
                        entity_id=group.entity_id,
                    )
                )
            continue
        entries.append(
            build_rejected_evidence_entry(
                evidence_id=f"advanced_maxquant:{group.entity_id}",
                source_surface="advanced_maxquant_workflow",
                reason_code="filtered_protein_group",
                message="maxquant protein group was filtered before biological reporting",
                related_artifact=manifest.artifacts.excluded_protein_groups_tsv,
                entity_id=group.entity_id,
            )
        )
    return tuple(entries)


def render_advanced_maxquant_peptide_contributions_tsv(
    entries: tuple[AdvancedMaxquantPeptideContributionEntry, ...],
) -> str:
    """Render peptide contributions to accepted MaxQuant LFQ entities as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_id",
            "representative_protein_ref",
            "peptide_sequence",
            "modified_sequence",
            "leading_razor_protein",
            "protein_refs",
            "intensity",
            "msms_count",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.entity_id,
                entry.representative_protein_ref,
                entry.peptide_sequence,
                "" if entry.modified_sequence is None else entry.modified_sequence,
                "" if entry.leading_razor_protein is None else entry.leading_razor_protein,
                ";".join(entry.protein_refs),
                "" if entry.intensity is None else f"{entry.intensity:g}",
                "" if entry.msms_count is None else entry.msms_count,
            )
        )
    return handle.getvalue()


def _build_peptide_contributions(
    report: MaxquantBiologicalWorkflowBundle,
) -> tuple[AdvancedMaxquantPeptideContributionEntry, ...]:
    peptide_rows_by_sequence: dict[str, tuple[MaxquantPeptideReviewEntry, ...]] = {}
    for row in report.import_report.peptide_rows:
        peptide_rows_by_sequence.setdefault(row.residue_sequence, tuple())
        peptide_rows_by_sequence[row.residue_sequence] = (
            peptide_rows_by_sequence[row.residue_sequence] + (row,)
        )

    entries: list[AdvancedMaxquantPeptideContributionEntry] = []
    for entity_id in report.lfq_table.entity_ids:
        representative_protein_ref = next(
            (
                row.representative_protein_ref
                for row in report.enrichment_foreground_entries
                if row.entity_id == entity_id
            ),
            report.lfq_table.entity_protein_refs.get(entity_id, (entity_id,))[0],
        )
        protein_refs = set(report.lfq_table.entity_protein_refs.get(entity_id, ()))
        for peptide_sequence in report.lfq_table.entity_member_peptides.get(entity_id, ()):
            matching_rows = _matching_peptide_rows(
                peptide_rows_by_sequence.get(peptide_sequence, ()),
                protein_refs=protein_refs,
            )
            if not matching_rows:
                entries.append(
                    AdvancedMaxquantPeptideContributionEntry(
                        entity_id=entity_id,
                        representative_protein_ref=representative_protein_ref,
                        peptide_sequence=peptide_sequence,
                    )
                )
                continue
            for peptide_row in matching_rows:
                entries.append(
                    AdvancedMaxquantPeptideContributionEntry(
                        entity_id=entity_id,
                        representative_protein_ref=representative_protein_ref,
                        peptide_sequence=peptide_row.residue_sequence,
                        modified_sequence=peptide_row.modified_sequence,
                        leading_razor_protein=peptide_row.leading_razor_protein,
                        protein_refs=peptide_row.protein_refs,
                        intensity=peptide_row.intensity,
                        msms_count=peptide_row.msms_count,
                    )
                )
    return tuple(
        sorted(
            entries,
            key=lambda entry: (
                entry.entity_id,
                entry.peptide_sequence,
                entry.modified_sequence or "",
            ),
        )
    )


def _matching_peptide_rows(
    rows: tuple[MaxquantPeptideReviewEntry, ...],
    *,
    protein_refs: set[str],
) -> tuple[MaxquantPeptideReviewEntry, ...]:
    matching = []
    for row in rows:
        row_protein_refs = set(row.protein_refs)
        if row.leading_razor_protein is not None:
            row_protein_refs.add(row.leading_razor_protein)
        if protein_refs.intersection(row_protein_refs):
            matching.append(row)
    if matching:
        return tuple(matching)
    return rows


__all__ = [
    "AdvancedMaxquantPeptideContributionEntry",
    "AdvancedMaxquantWorkflowArtifactPaths",
    "AdvancedMaxquantWorkflowConfig",
    "AdvancedMaxquantWorkflowManifest",
    "AdvancedMaxquantWorkflowReport",
    "AdvancedMaxquantWorkflowSummary",
    "render_advanced_maxquant_peptide_contributions_tsv",
    "render_advanced_maxquant_workflow_summary_tsv",
    "run_advanced_maxquant_workflow",
]
