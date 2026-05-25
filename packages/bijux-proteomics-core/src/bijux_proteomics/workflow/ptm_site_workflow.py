# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned PTM-site workflow bundles from localized evidence to site biology."""

from __future__ import annotations

import csv
from io import StringIO
import json
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import (
    PtmEvidenceCardPolicy,
    PtmEvidenceParseReport,
    PtmLocalizationColumnMapping,
    PtmMotifComparisonPolicy,
    PtmPhosphositeSelectionPolicy,
    PtmProteinCorrectionMode,
    PtmReportBundle,
    PtmReportExportManifest,
    PtmRegulatorEnrichmentPolicy,
    PtmSiteQuantAmbiguityPolicy,
    write_ptm_report_bundle,
    parse_ptm_localization_tsv,
    parse_ptm_site_annotation_tsv,
)
from bijux_proteomics.ptm.reporting import build_ptm_report_bundle
from bijux_proteomics.quantification import (
    NormalizationMethod,
    parse_ms1_feature_table,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics.study import ExperimentDesign, build_experiment_design
from bijux_proteomics_foundation import JsonModel


class PtmSiteWorkflowSummary(JsonModel):
    """Compact summary over one PTM-site workflow bundle."""

    model_config = ConfigDict(extra="forbid")

    total_evidence_row_count: int = Field(..., ge=0)
    accepted_evidence_count: int = Field(..., ge=0)
    rejected_evidence_count: int = Field(..., ge=0)
    protein_sequence_count: int = Field(..., ge=0)
    feature_row_count: int = Field(..., ge=0)
    design_row_count: int = Field(..., ge=0)
    site_row_count: int = Field(..., ge=0)
    localization_entry_count: int = Field(..., ge=0)
    quantified_site_row_count: int = Field(..., ge=0)
    differential_site_count: int = Field(..., ge=0)
    motif_term_count: int = Field(..., ge=0)
    evidence_card_count: int = Field(..., ge=0)
    narrative_claim_count: int = Field(..., ge=0)


class PtmSiteWorkflowBundle(JsonModel):
    """Owned PTM-site workflow from localized evidence TSV to PTM report surfaces."""

    model_config = ConfigDict(extra="forbid")

    evidence_parse_report: PtmEvidenceParseReport
    feature_row_count: int = Field(..., ge=0)
    experiment_design: ExperimentDesign
    protein_sequence_count: int = Field(..., ge=0)
    report: PtmReportBundle
    summary: PtmSiteWorkflowSummary
    note: str = Field(..., min_length=1)


class PtmSiteWorkflowArtifactPaths(JsonModel):
    """Relative artifact paths written into one PTM-site workflow directory."""

    model_config = ConfigDict(extra="forbid")

    summary_tsv: str = Field(..., min_length=1)
    accepted_evidence_tsv: str = Field(..., min_length=1)
    rejected_evidence_tsv: str = Field(..., min_length=1)
    ptm_report_manifest_json: str = Field(..., min_length=1)


class PtmSiteWorkflowExportManifest(JsonModel):
    """Stable manifest over one exported PTM-site workflow directory."""

    model_config = ConfigDict(extra="forbid")

    summary: PtmSiteWorkflowSummary
    artifacts: PtmSiteWorkflowArtifactPaths
    ptm_report_manifest: PtmReportExportManifest
    note: str = Field(..., min_length=1)


def build_ptm_site_workflow_bundle(
    evidence_tsv_path: Path,
    proteins_fasta_path: Path,
    *,
    feature_tsv_path: Path,
    design_path: Path,
    mapping: PtmLocalizationColumnMapping | None = None,
    fragment_support_json_path: Path | None = None,
    ambiguity_policy: PtmSiteQuantAmbiguityPolicy = PtmSiteQuantAmbiguityPolicy.PRESERVE,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    protein_correction_mode: PtmProteinCorrectionMode = PtmProteinCorrectionMode.NONE,
    batch_field: str = "batch",
    covariate_fields: tuple[str, ...] = (),
    pairing_field: str | None = None,
    motif_flank_size: int = 7,
    motif_selection_policy: PtmPhosphositeSelectionPolicy | None = None,
    motif_comparison_policy: PtmMotifComparisonPolicy | None = None,
    annotation_tsv_path: Path | None = None,
    annotation_target_species: str | None = None,
    regulator_enrichment_policy: PtmRegulatorEnrichmentPolicy | None = None,
    evidence_card_policy: PtmEvidenceCardPolicy | None = None,
) -> PtmSiteWorkflowBundle:
    """Build one governed PTM-site workflow bundle from TSV inputs."""

    evidence_parse_report = parse_ptm_localization_tsv(
        evidence_tsv_path,
        mapping=mapping,
    )
    fasta_report = parse_fasta_document(
        proteins_fasta_path.read_text(encoding="utf-8"),
        mode=FastaParseMode.STRICT,
    )
    if fasta_report.rejected_records:
        rejected = ", ".join(
            record.source_identifier for record in fasta_report.rejected_records
        )
        raise ValueError(
            f"FASTA input contains rejected records under strict mode: {rejected}"
        )
    feature_report = parse_ms1_feature_table(feature_tsv_path)
    design_report = parse_experimental_design_table(design_path)
    if design_report.rejected_rows:
        raise ValueError("design table contains rejected rows")
    experiment_design = build_experiment_design(design_report.accepted_entries)
    fragment_ion_support_by_spectrum = _load_fragment_support_by_spectrum(
        fragment_support_json_path
    )
    annotation_records = None
    if annotation_tsv_path is not None:
        annotation_records = parse_ptm_site_annotation_tsv(
            annotation_tsv_path
        ).accepted_records
    protein_sequences = {
        record.canonical_accession: record.residues
        for record in fasta_report.accepted_records
    }
    report = build_ptm_report_bundle(
        evidence_parse_report.accepted_records,
        protein_sequences=protein_sequences,
        protein_records=fasta_report.accepted_records,
        fragment_ion_support_by_spectrum=fragment_ion_support_by_spectrum,
        feature_records=feature_report.accepted_records,
        design_entries=experiment_design.entries,
        ambiguity_policy=ambiguity_policy,
        normalization_method=normalization_method,
        condition_a=condition_a,
        condition_b=condition_b,
        protein_correction_mode=protein_correction_mode,
        batch_field=batch_field,
        covariate_fields=tuple(dict.fromkeys(covariate_fields)),
        pairing_field=pairing_field,
        motif_flank_size=motif_flank_size,
        motif_selection_policy=motif_selection_policy,
        motif_comparison_policy=motif_comparison_policy,
        annotation_records=annotation_records,
        annotation_target_species=annotation_target_species,
        regulator_enrichment_policy=regulator_enrichment_policy,
        evidence_card_policy=evidence_card_policy,
    )
    return PtmSiteWorkflowBundle(
        evidence_parse_report=evidence_parse_report,
        feature_row_count=len(feature_report.accepted_records),
        experiment_design=experiment_design,
        protein_sequence_count=len(protein_sequences),
        report=report,
        summary=PtmSiteWorkflowSummary(
            total_evidence_row_count=evidence_parse_report.total_rows,
            accepted_evidence_count=len(evidence_parse_report.accepted_records),
            rejected_evidence_count=len(evidence_parse_report.rejected_rows),
            protein_sequence_count=len(protein_sequences),
            feature_row_count=len(feature_report.accepted_records),
            design_row_count=len(experiment_design.entries),
            site_row_count=report.summary.site_row_count,
            localization_entry_count=report.summary.localization_entry_count,
            quantified_site_row_count=report.summary.quantified_site_row_count,
            differential_site_count=report.summary.differential_site_count,
            motif_term_count=report.summary.motif_term_count,
            evidence_card_count=report.summary.evidence_card_count,
            narrative_claim_count=report.summary.narrative_claim_count,
        ),
        note=(
            "PTM-site workflow parses localized evidence and experiment context from governed files, preserves rejected evidence review, and routes accepted site biology through the owned PTM report bundle"
        ),
    )


def render_ptm_site_workflow_summary_tsv(report: PtmSiteWorkflowBundle) -> str:
    """Render one compact PTM-site workflow summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field_name, value in (
        ("total_evidence_row_count", report.summary.total_evidence_row_count),
        ("accepted_evidence_count", report.summary.accepted_evidence_count),
        ("rejected_evidence_count", report.summary.rejected_evidence_count),
        ("protein_sequence_count", report.summary.protein_sequence_count),
        ("feature_row_count", report.summary.feature_row_count),
        ("design_row_count", report.summary.design_row_count),
        ("site_row_count", report.summary.site_row_count),
        ("localization_entry_count", report.summary.localization_entry_count),
        ("quantified_site_row_count", report.summary.quantified_site_row_count),
        ("differential_site_count", report.summary.differential_site_count),
        ("motif_term_count", report.summary.motif_term_count),
        ("evidence_card_count", report.summary.evidence_card_count),
        ("narrative_claim_count", report.summary.narrative_claim_count),
        ("note", report.note),
    ):
        writer.writerow((field_name, value))
    return handle.getvalue()


def render_ptm_site_workflow_accepted_evidence_tsv(
    report: PtmSiteWorkflowBundle,
) -> str:
    """Render accepted PTM evidence records carried into the workflow."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "sample_id",
            "spectrum_id",
            "localized_peptide",
            "canonical_peptide",
            "sequence",
            "charge",
            "score",
            "q_value",
            "localization_score",
            "localization_probability",
            "protein_refs",
            "candidate_site_indices",
            "target_decoy_label",
            "modification_names",
        )
    )
    for record in report.evidence_parse_report.accepted_records:
        writer.writerow(
            (
                record.sample_id or "",
                record.spectrum_id,
                record.localized_peptide,
                record.canonical_peptide,
                record.sequence,
                record.charge,
                f"{record.score:g}",
                "" if record.q_value is None else f"{record.q_value:g}",
                f"{record.localization_score:g}",
                ""
                if record.localization_probability is None
                else f"{record.localization_probability:g}",
                ";".join(record.protein_refs),
                ";".join(str(index) for index in record.candidate_site_indices),
                record.target_decoy_label.value,
                ";".join(record.modification_names),
            )
        )
    return handle.getvalue()


def render_ptm_site_workflow_rejected_evidence_tsv(
    report: PtmSiteWorkflowBundle,
) -> str:
    """Render rejected PTM evidence rows as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("row_number", "issue_codes", "issue_messages", "raw_fields"))
    for row in report.evidence_parse_report.rejected_rows:
        writer.writerow(
            (
                row.row_number,
                ";".join(issue.code for issue in row.issues),
                ";".join(issue.message for issue in row.issues),
                ";".join(
                    f"{key}={value}"
                    for key, value in sorted(
                        row.raw_fields.items(),
                        key=lambda item: item[0],
                    )
                ),
            )
        )
    return handle.getvalue()


def write_ptm_site_workflow_bundle(
    report: PtmSiteWorkflowBundle,
    output_dir: Path,
) -> PtmSiteWorkflowExportManifest:
    """Export one PTM-site workflow bundle into a stable directory."""

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_name = "ptm_site_workflow_summary.tsv"
    accepted_name = "ptm_site_workflow_accepted_evidence.tsv"
    rejected_name = "ptm_site_workflow_rejected_evidence.tsv"
    ptm_report_manifest_name = "ptm_report_manifest.json"

    (output_dir / summary_name).write_text(
        render_ptm_site_workflow_summary_tsv(report),
        encoding="utf-8",
    )
    (output_dir / accepted_name).write_text(
        render_ptm_site_workflow_accepted_evidence_tsv(report),
        encoding="utf-8",
    )
    (output_dir / rejected_name).write_text(
        render_ptm_site_workflow_rejected_evidence_tsv(report),
        encoding="utf-8",
    )
    ptm_report_manifest = write_ptm_report_bundle(report.report, output_dir)
    (output_dir / ptm_report_manifest_name).write_text(
        ptm_report_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )
    return PtmSiteWorkflowExportManifest(
        summary=report.summary,
        artifacts=PtmSiteWorkflowArtifactPaths(
            summary_tsv=summary_name,
            accepted_evidence_tsv=accepted_name,
            rejected_evidence_tsv=rejected_name,
            ptm_report_manifest_json=ptm_report_manifest_name,
        ),
        ptm_report_manifest=ptm_report_manifest,
        note=(
            "PTM-site workflow export preserves accepted and rejected evidence review plus the downstream PTM report bundle in one durable directory"
        ),
    )


def export_ptm_site_workflow_bundle(
    report: PtmSiteWorkflowBundle,
    output_dir: Path,
) -> PtmSiteWorkflowExportManifest:
    """Compatibility wrapper for the legacy PTM-site workflow bundle export name."""

    return write_ptm_site_workflow_bundle(report, output_dir)


def _load_fragment_support_by_spectrum(
    fragment_support_json_path: Path | None,
) -> dict[str, tuple[str, ...]] | None:
    if fragment_support_json_path is None:
        return None
    raw_fragment_support = json.loads(
        fragment_support_json_path.read_text(encoding="utf-8")
    )
    if not isinstance(raw_fragment_support, dict):
        raise ValueError("fragment support JSON must be an object keyed by spectrum id")
    return {
        str(spectrum_id): tuple(str(ion) for ion in ions)
        for spectrum_id, ions in raw_fragment_support.items()
    }
