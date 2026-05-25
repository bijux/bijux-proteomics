# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Advanced FragPipe workflow execution over governed review surfaces."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import PsmRecord, SearchAdapterKind
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification import NormalizationMethod, QuantRollupMethod
from bijux_proteomics.workflow.biological_reporting import (
    BiologicalResultSelectionPolicy,
    VolcanoReviewPolicy,
)
from bijux_proteomics.workflow.dda_biological_workflow import (
    DdaBiologicalWorkflowBundle,
    DdaBiologicalWorkflowExportManifest,
    DdaPsmAcceptancePolicy,
    DdaProteinGroupDiscrepancyEntry,
    DdaProteinGroupDiscrepancyStatus,
    export_dda_biological_workflow_bundle,
    build_dda_biological_workflow_bundle,
)
from bijux_proteomics.workflow.result_types import (
    BiologyResult,
    artifact_name_map,
    build_rejected_evidence_entries_from_issue_rows,
    build_rejected_evidence_entries_from_reason_rows,
    build_result_warning,
)
from bijux_proteomics_foundation import JsonModel


class AdvancedFragpipeWorkflowConfig(JsonModel):
    """Config for the advanced FragPipe workflow owner."""

    model_config = ConfigDict(extra="forbid")

    psm_tsv_path: Path
    design_tsv_path: Path
    proteins_fasta_path: Path
    output_dir: Path
    protocol_context_tsv_path: Path | None = None
    philosopher_protein_tsv_path: Path | None = None
    acceptance_policy: DdaPsmAcceptancePolicy | None = None
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM
    top_n: int = Field(default=3, ge=1)
    minimum_shared_peptides: int = Field(default=1, ge=1)
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN
    condition_a: str | None = None
    condition_b: str | None = None
    annotation_tsv_path: Path | None = None
    go_annotation_tsv_path: Path | None = None
    pathway_membership_tsv_path: Path | None = None
    complex_membership_tsv_path: Path | None = None
    selection_policy: BiologicalResultSelectionPolicy | None = None
    volcano_policy: VolcanoReviewPolicy | None = None


class AdvancedFragpipeDiscrepancyReason(StrEnum):
    """Stable exact reasons for FragPipe protein-group discrepancy rows."""

    SHARED = "shared_between_source_and_workflow"
    SOURCE_ONLY = "present_in_source_summary_only"
    WORKFLOW_INFERRED_AND_QUANTIFIED = "missing_from_source_summary_but_inferred_and_quantified"
    WORKFLOW_INFERRED_ONLY = "missing_from_source_summary_but_inferred_only"
    WORKFLOW_QUANTIFIED_ONLY = "missing_from_source_summary_but_quantified_only"
    WORKFLOW_SIGNIFICANT_ONLY = "missing_from_source_summary_but_marked_significant_only"
    WORKFLOW_PRESENT_UNSPECIFIED = "missing_from_source_summary_but_present_in_workflow"


class AdvancedFragpipeWorkflowSummary(JsonModel):
    """Compact summary over one advanced FragPipe workflow run."""

    model_config = ConfigDict(extra="forbid")

    imported_psm_row_count: int = Field(..., ge=0)
    accepted_psm_count: int = Field(..., ge=0)
    filtered_psm_count: int = Field(..., ge=0)
    inferred_protein_count: int = Field(..., ge=0)
    quantified_protein_count: int = Field(..., ge=0)
    peptide_evidence_count: int = Field(..., ge=0)
    protein_group_discrepancy_count: int = Field(..., ge=0)
    source_only_protein_group_count: int = Field(..., ge=0)
    workflow_only_protein_group_count: int = Field(..., ge=0)
    significant_protein_count: int = Field(..., ge=0)


class AdvancedFragpipeWorkflowArtifactPaths(JsonModel):
    """Advanced FragPipe artifact paths written into the output directory."""

    model_config = ConfigDict(extra="forbid")

    summary_tsv: str = Field(..., min_length=1)
    fragpipe_workflow_manifest_json: str = Field(..., min_length=1)
    biological_report_manifest_json: str = Field(..., min_length=1)
    peptide_evidence_tsv: str = Field(..., min_length=1)
    discrepancy_reason_tsv: str | None = None
    supported_claim_tsv: str | None = None
    rejected_claim_tsv: str | None = None


class AdvancedFragpipeWorkflowManifest(JsonModel):
    """Stable manifest over one advanced FragPipe workflow output directory."""

    model_config = ConfigDict(extra="forbid")

    summary: AdvancedFragpipeWorkflowSummary
    artifacts: AdvancedFragpipeWorkflowArtifactPaths
    fragpipe_workflow_manifest: DdaBiologicalWorkflowExportManifest
    note: str = Field(..., min_length=1)


class AdvancedFragpipePeptideEvidenceEntry(JsonModel):
    """One peptide evidence row carried through the accepted FragPipe workflow."""

    model_config = ConfigDict(extra="forbid")

    peptide_sequence: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    psm_count: int = Field(..., ge=0)
    run_count: int = Field(..., ge=0)
    best_q_value: float | None = Field(default=None, ge=0.0)
    total_intensity: float = Field(..., ge=0.0)


class AdvancedFragpipeDiscrepancyEntry(JsonModel):
    """One exact-reason FragPipe discrepancy row against a source summary."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    status: DdaProteinGroupDiscrepancyStatus
    discrepancy_reason: AdvancedFragpipeDiscrepancyReason
    source_table_present: bool
    inferred_by_workflow: bool
    quantified_by_workflow: bool
    significant_in_workflow: bool


class AdvancedFragpipeWorkflowReport(BiologyResult):
    """Advanced FragPipe workflow report with exported review outputs."""

    model_config = ConfigDict(extra="forbid")

    fragpipe_workflow: DdaBiologicalWorkflowBundle
    fragpipe_workflow_manifest: DdaBiologicalWorkflowExportManifest
    peptide_evidence: tuple[AdvancedFragpipePeptideEvidenceEntry, ...] = Field(
        default_factory=tuple
    )
    discrepancy_reasons: tuple[AdvancedFragpipeDiscrepancyEntry, ...] = Field(
        default_factory=tuple
    )
    summary: AdvancedFragpipeWorkflowSummary
    manifest: AdvancedFragpipeWorkflowManifest
    note: str = Field(..., min_length=1)


def run_advanced_fragpipe_workflow(
    config: AdvancedFragpipeWorkflowConfig,
) -> AdvancedFragpipeWorkflowReport:
    """Run the advanced FragPipe workflow and write one durable review directory."""

    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    design_entries = tuple(
        parse_experimental_design_table(config.design_tsv_path).accepted_entries
    )
    base_report = build_dda_biological_workflow_bundle(
        config.psm_tsv_path,
        design_entries,
        proteins_fasta_path=config.proteins_fasta_path,
        protocol_context_tsv_path=config.protocol_context_tsv_path,
        adapter_kind=SearchAdapterKind.MSFRAGGER,
        dialect_id="fragpipe-psm",
        acceptance_policy=config.acceptance_policy,
        aggregation_method=config.aggregation_method,
        top_n=config.top_n,
        minimum_shared_peptides=config.minimum_shared_peptides,
        normalization_method=config.normalization_method,
        condition_a=config.condition_a,
        condition_b=config.condition_b,
        source_protein_tsv_path=config.philosopher_protein_tsv_path,
        annotation_tsv_path=config.annotation_tsv_path,
        go_annotation_tsv_path=config.go_annotation_tsv_path,
        pathway_membership_tsv_path=config.pathway_membership_tsv_path,
        complex_membership_tsv_path=config.complex_membership_tsv_path,
        selection_policy=config.selection_policy,
        volcano_policy=config.volcano_policy,
    )
    fragpipe_manifest = export_dda_biological_workflow_bundle(base_report, output_dir)
    fragpipe_manifest_path = output_dir / "fragpipe_biological_report_manifest.json"
    fragpipe_manifest_path.write_text(
        fragpipe_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )

    peptide_evidence = _build_peptide_evidence(base_report.accepted_psms)
    discrepancy_reasons = _build_discrepancy_reasons(
        base_report.protein_group_discrepancies
    )

    peptide_evidence_name = "advanced_fragpipe_peptide_evidence.tsv"
    discrepancy_name = "advanced_fragpipe_protein_group_discrepancies.tsv"
    summary_name = "advanced_fragpipe_summary.tsv"

    (output_dir / peptide_evidence_name).write_text(
        render_advanced_fragpipe_peptide_evidence_tsv(peptide_evidence),
        encoding="utf-8",
    )
    if discrepancy_reasons:
        (output_dir / discrepancy_name).write_text(
            render_advanced_fragpipe_discrepancy_tsv(discrepancy_reasons),
            encoding="utf-8",
        )

    summary = AdvancedFragpipeWorkflowSummary(
        imported_psm_row_count=base_report.summary.imported_psm_row_count,
        accepted_psm_count=base_report.summary.accepted_psm_count,
        filtered_psm_count=base_report.summary.filtered_psm_count,
        inferred_protein_count=base_report.summary.inferred_protein_count,
        quantified_protein_count=base_report.summary.quantified_protein_count,
        peptide_evidence_count=len(peptide_evidence),
        protein_group_discrepancy_count=base_report.summary.protein_group_discrepancy_count,
        source_only_protein_group_count=base_report.summary.source_only_protein_group_count,
        workflow_only_protein_group_count=base_report.summary.workflow_only_protein_group_count,
        significant_protein_count=base_report.summary.significant_protein_count,
    )
    (output_dir / summary_name).write_text(
        render_advanced_fragpipe_workflow_summary_tsv(summary),
        encoding="utf-8",
    )

    manifest = AdvancedFragpipeWorkflowManifest(
        summary=summary,
        artifacts=AdvancedFragpipeWorkflowArtifactPaths(
            summary_tsv=summary_name,
            fragpipe_workflow_manifest_json=fragpipe_manifest_path.name,
            biological_report_manifest_json=fragpipe_manifest.artifacts.biological_manifest_json,
            peptide_evidence_tsv=peptide_evidence_name,
            discrepancy_reason_tsv=discrepancy_name if discrepancy_reasons else None,
            supported_claim_tsv=fragpipe_manifest.biological_report_manifest.artifacts.supported_claim_tsv,
            rejected_claim_tsv=fragpipe_manifest.biological_report_manifest.artifacts.rejected_claim_tsv,
        ),
        fragpipe_workflow_manifest=fragpipe_manifest,
        note=(
            "advanced fragpipe workflow preserves governed fragpipe psm import, "
            "psm fdr filtering, peptide evidence, protein grouping, protein lfq, "
            "and exact discrepancy reasoning against an optional philosopher summary"
        ),
    )
    manifest_path = output_dir / "advanced_fragpipe_workflow_manifest.json"
    manifest_path.write_text(manifest.to_stable_json() + "\n", encoding="utf-8")

    return AdvancedFragpipeWorkflowReport(
        fragpipe_workflow=base_report,
        fragpipe_workflow_manifest=fragpipe_manifest,
        peptide_evidence=peptide_evidence,
        discrepancy_reasons=discrepancy_reasons,
        summary=summary,
        manifest=manifest,
        artifacts=artifact_name_map(manifest.artifacts),
        warnings=_build_advanced_fragpipe_warnings(summary=summary, manifest=manifest),
        rejected_evidence=_build_advanced_fragpipe_rejected_evidence(
            report=base_report,
            discrepancy_reasons=discrepancy_reasons,
            manifest=manifest,
        ),
        note=(
            "advanced fragpipe workflow composes governed fragpipe psm import, "
            "protein grouping, protein quantification, downstream biology, and "
            "exact reason export for source-summary discrepancies"
        ),
    )


def render_advanced_fragpipe_workflow_summary_tsv(
    summary: AdvancedFragpipeWorkflowSummary,
) -> str:
    """Render one advanced FragPipe workflow summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field_name, value in (
        ("imported_psm_row_count", summary.imported_psm_row_count),
        ("accepted_psm_count", summary.accepted_psm_count),
        ("filtered_psm_count", summary.filtered_psm_count),
        ("inferred_protein_count", summary.inferred_protein_count),
        ("quantified_protein_count", summary.quantified_protein_count),
        ("peptide_evidence_count", summary.peptide_evidence_count),
        ("protein_group_discrepancy_count", summary.protein_group_discrepancy_count),
        ("source_only_protein_group_count", summary.source_only_protein_group_count),
        ("workflow_only_protein_group_count", summary.workflow_only_protein_group_count),
        ("significant_protein_count", summary.significant_protein_count),
    ):
        writer.writerow((field_name, value))
    return handle.getvalue()


def render_advanced_fragpipe_peptide_evidence_tsv(
    entries: tuple[AdvancedFragpipePeptideEvidenceEntry, ...],
) -> str:
    """Render peptide evidence preserved from accepted FragPipe PSMs as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "peptide_sequence",
            "protein_refs",
            "psm_count",
            "run_count",
            "best_q_value",
            "total_intensity",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.peptide_sequence,
                ";".join(entry.protein_refs),
                entry.psm_count,
                entry.run_count,
                "" if entry.best_q_value is None else f"{entry.best_q_value:g}",
                f"{entry.total_intensity:g}",
            )
        )
    return handle.getvalue()


def render_advanced_fragpipe_discrepancy_tsv(
    entries: tuple[AdvancedFragpipeDiscrepancyEntry, ...],
) -> str:
    """Render exact-reason FragPipe protein-group discrepancies as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "protein_ref",
            "status",
            "discrepancy_reason",
            "source_table_present",
            "inferred_by_workflow",
            "quantified_by_workflow",
            "significant_in_workflow",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.protein_ref,
                entry.status.value,
                entry.discrepancy_reason.value,
                str(entry.source_table_present).lower(),
                str(entry.inferred_by_workflow).lower(),
                str(entry.quantified_by_workflow).lower(),
                str(entry.significant_in_workflow).lower(),
            )
        )
    return handle.getvalue()


def _build_advanced_fragpipe_warnings(
    *,
    summary: AdvancedFragpipeWorkflowSummary,
    manifest: AdvancedFragpipeWorkflowManifest,
) -> tuple:
    warnings = []
    if summary.filtered_psm_count > 0:
        warnings.append(
            build_result_warning(
                warning_id="advanced_fragpipe:filtered_psms",
                warning_code="filtered_psm_present",
                source_surface="advanced_fragpipe_workflow",
                message=(
                    f"advanced FragPipe filtered {summary.filtered_psm_count} accepted PSMs "
                    "during downstream review"
                ),
            )
        )
    if summary.protein_group_discrepancy_count > 0:
        warnings.append(
            build_result_warning(
                warning_id="advanced_fragpipe:protein_group_discrepancies",
                warning_code="protein_group_discrepancy_present",
                source_surface="advanced_fragpipe_workflow",
                message=(
                    "advanced FragPipe detected "
                    f"{summary.protein_group_discrepancy_count} source-summary discrepancies"
                ),
                related_artifact=manifest.artifacts.discrepancy_reason_tsv,
            )
        )
    return tuple(warnings)


def _build_advanced_fragpipe_rejected_evidence(
    *,
    report: DdaBiologicalWorkflowBundle,
    discrepancy_reasons: tuple[AdvancedFragpipeDiscrepancyEntry, ...],
    manifest: AdvancedFragpipeWorkflowManifest,
) -> tuple:
    return (
        build_rejected_evidence_entries_from_issue_rows(
            report.parse_rejected_rows,
            source_surface="advanced_fragpipe_workflow",
            related_artifact=manifest.fragpipe_workflow_manifest.artifacts.parse_rejected_tsv,
            entity_prefix="psm_row",
        )
        + build_rejected_evidence_entries_from_reason_rows(
            discrepancy_reasons,
            source_surface="advanced_fragpipe_workflow",
            reason_field="discrepancy_reason",
            message_field="status",
            entity_field="protein_ref",
            related_artifact=manifest.artifacts.discrepancy_reason_tsv,
        )
    )


def _build_peptide_evidence(
    psms: tuple[PsmRecord, ...],
) -> tuple[AdvancedFragpipePeptideEvidenceEntry, ...]:
    by_key: dict[tuple[str, tuple[str, ...]], list[PsmRecord]] = {}
    for psm in psms:
        key = (psm.canonical_peptide, tuple(sorted(psm.protein_refs)))
        by_key.setdefault(key, []).append(psm)
    entries: list[AdvancedFragpipePeptideEvidenceEntry] = []
    for (peptide_sequence, protein_refs), rows in by_key.items():
        q_values = [row.q_value for row in rows if row.q_value is not None]
        entries.append(
            AdvancedFragpipePeptideEvidenceEntry(
                peptide_sequence=peptide_sequence,
                protein_refs=protein_refs,
                psm_count=len(rows),
                run_count=len({row.run_id for row in rows if row.run_id}),
                best_q_value=None if not q_values else min(q_values),
                total_intensity=sum(row.intensity or 0.0 for row in rows),
            )
        )
    return tuple(
        sorted(
            entries,
            key=lambda entry: (entry.peptide_sequence, entry.protein_refs),
        )
    )


def _build_discrepancy_reasons(
    entries: tuple[DdaProteinGroupDiscrepancyEntry, ...],
) -> tuple[AdvancedFragpipeDiscrepancyEntry, ...]:
    return tuple(
        sorted(
            (
                AdvancedFragpipeDiscrepancyEntry(
                    protein_ref=entry.protein_ref,
                    status=entry.status,
                    discrepancy_reason=_discrepancy_reason(entry),
                    source_table_present=entry.source_table_present,
                    inferred_by_workflow=entry.inferred_by_workflow,
                    quantified_by_workflow=entry.quantified_by_workflow,
                    significant_in_workflow=entry.significant_in_workflow,
                )
                for entry in entries
            ),
            key=lambda entry: (entry.status.value, entry.protein_ref),
        )
    )


def _discrepancy_reason(
    entry: DdaProteinGroupDiscrepancyEntry,
) -> AdvancedFragpipeDiscrepancyReason:
    if entry.status is DdaProteinGroupDiscrepancyStatus.SHARED:
        return AdvancedFragpipeDiscrepancyReason.SHARED
    if entry.status is DdaProteinGroupDiscrepancyStatus.SOURCE_ONLY:
        return AdvancedFragpipeDiscrepancyReason.SOURCE_ONLY
    if entry.inferred_by_workflow and entry.quantified_by_workflow:
        return AdvancedFragpipeDiscrepancyReason.WORKFLOW_INFERRED_AND_QUANTIFIED
    if entry.inferred_by_workflow:
        return AdvancedFragpipeDiscrepancyReason.WORKFLOW_INFERRED_ONLY
    if entry.quantified_by_workflow:
        return AdvancedFragpipeDiscrepancyReason.WORKFLOW_QUANTIFIED_ONLY
    if entry.significant_in_workflow:
        return AdvancedFragpipeDiscrepancyReason.WORKFLOW_SIGNIFICANT_ONLY
    return AdvancedFragpipeDiscrepancyReason.WORKFLOW_PRESENT_UNSPECIFIED


__all__ = [
    "AdvancedFragpipeDiscrepancyEntry",
    "AdvancedFragpipeDiscrepancyReason",
    "AdvancedFragpipePeptideEvidenceEntry",
    "AdvancedFragpipeWorkflowArtifactPaths",
    "AdvancedFragpipeWorkflowConfig",
    "AdvancedFragpipeWorkflowManifest",
    "AdvancedFragpipeWorkflowReport",
    "AdvancedFragpipeWorkflowSummary",
    "render_advanced_fragpipe_discrepancy_tsv",
    "render_advanced_fragpipe_peptide_evidence_tsv",
    "render_advanced_fragpipe_workflow_summary_tsv",
    "run_advanced_fragpipe_workflow",
]
