# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned PTM reporting surfaces."""

from __future__ import annotations

import csv
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.ptm.contracts import (
    PtmEvidenceRecord,
    PtmSiteEntry,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
)
from bijux_proteomics.ptm.differential_analysis import (
    PtmDifferentialAnalysisReport,
    PtmProteinCorrectionMode,
    build_ptm_differential_analysis_report,
    render_ptm_site_differential_tsv,
)
from bijux_proteomics.ptm.localization_scoring import (
    PtmLocalizationScoringReport,
    build_ptm_localization_scoring_report,
    render_ptm_localization_scoring_entry_tsv,
)
from bijux_proteomics.ptm.site_quantification import (
    PtmSiteQuantAmbiguityPolicy,
    PtmSiteQuantificationReport,
    build_ptm_site_quantification_report,
    render_ptm_site_quant_matrix_tsv,
)
from bijux_proteomics.quantification import Ms1FeatureRecord, NormalizationMethod
from bijux_proteomics_foundation import JsonModel


class PtmReportPeptideEntry(JsonModel):
    """One PTM peptide observation carried into a report bundle."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    sample_id: str | None = None
    localized_peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    sequence: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    score: float
    q_value: float | None = Field(default=None, ge=0.0)
    localization_score: float = Field(..., ge=0.0)
    localization_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    modification_names: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel


class PtmReportSummary(JsonModel):
    """Compact summary over the current PTM report bundle."""

    model_config = ConfigDict(extra="forbid")

    accepted_evidence_count: int = Field(..., ge=0)
    peptide_entry_count: int = Field(..., ge=0)
    site_row_count: int = Field(..., ge=0)
    ambiguous_site_count: int = Field(..., ge=0)
    modified_peptide_count: int = Field(..., ge=0)
    localization_entry_count: int = Field(..., ge=0)
    quantified_site_row_count: int = Field(..., ge=0)
    differential_site_count: int = Field(..., ge=0)


class PtmReportBundle(JsonModel):
    """Owned PTM report bundle over evidence-derived peptide and site surfaces."""

    model_config = ConfigDict(extra="forbid")

    peptide_entries: tuple[PtmReportPeptideEntry, ...] = Field(default_factory=tuple)
    site_table: tuple[PtmSiteEntry, ...] = Field(default_factory=tuple)
    localization_scoring: PtmLocalizationScoringReport
    site_quantification: PtmSiteQuantificationReport | None = None
    differential_analysis: PtmDifferentialAnalysisReport | None = None
    summary: PtmReportSummary
    note: str = Field(..., min_length=1)


def build_ptm_report_bundle(
    records: tuple[PtmEvidenceRecord, ...],
    *,
    protein_sequences: dict[str, str],
    fragment_ion_support_by_spectrum: dict[str, tuple[str, ...]] | None = None,
    feature_records: tuple[Ms1FeatureRecord, ...] | None = None,
    design_entries: tuple[ExperimentalDesignEntry, ...] | None = None,
    ambiguity_policy: PtmSiteQuantAmbiguityPolicy = PtmSiteQuantAmbiguityPolicy.PRESERVE,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    protein_correction_mode: PtmProteinCorrectionMode = PtmProteinCorrectionMode.NONE,
    batch_field: str = "batch",
    covariate_fields: tuple[str, ...] = (),
    pairing_field: str | None = None,
) -> PtmReportBundle:
    """Build the core PTM report bundle from evidence rows and protein context."""

    peptide_entries = tuple(
        sorted(
            (
                PtmReportPeptideEntry(
                    spectrum_id=record.spectrum_id,
                    sample_id=record.sample_id,
                    localized_peptide=record.localized_peptide,
                    canonical_peptide=record.canonical_peptide,
                    sequence=record.sequence,
                    charge=record.charge,
                    score=record.score,
                    q_value=record.q_value,
                    localization_score=record.localization_score,
                    localization_probability=record.localization_probability,
                    protein_refs=record.protein_refs,
                    modification_names=record.modification_names,
                    target_decoy_label=record.target_decoy_label,
                )
                for record in records
            ),
            key=lambda entry: (
                entry.protein_refs[0] if entry.protein_refs else "",
                entry.localized_peptide,
                entry.spectrum_id,
                entry.sample_id or "",
            ),
        )
    )
    mappings = map_ptm_evidence_to_protein_sites(
        records,
        protein_sequences=protein_sequences,
    )
    site_table = build_ptm_site_table(mappings)
    localization_scoring = build_ptm_localization_scoring_report(
        records,
        fragment_ion_support_by_spectrum=fragment_ion_support_by_spectrum,
    )
    site_quantification = None
    differential_analysis = None
    if feature_records is not None:
        site_quantification = build_ptm_site_quantification_report(
            site_table,
            feature_records=feature_records,
            ambiguity_policy=ambiguity_policy,
        )
    if design_entries is not None:
        if site_quantification is None or feature_records is None:
            raise ValueError(
                "design-aware ptm reporting requires feature_records so site quantification exists before differential analysis"
            )
        differential_analysis = build_ptm_differential_analysis_report(
            site_quantification,
            design_entries,
            normalization_method=normalization_method,
            condition_a=condition_a,
            condition_b=condition_b,
            feature_records=feature_records,
            protein_correction_mode=protein_correction_mode,
            batch_field=batch_field,
            covariate_fields=tuple(dict.fromkeys(covariate_fields)),
            pairing_field=pairing_field,
        )
    return PtmReportBundle(
        peptide_entries=peptide_entries,
        site_table=site_table,
        localization_scoring=localization_scoring,
        site_quantification=site_quantification,
        differential_analysis=differential_analysis,
        summary=PtmReportSummary(
            accepted_evidence_count=len(records),
            peptide_entry_count=len(peptide_entries),
            site_row_count=len(site_table),
            ambiguous_site_count=sum(1 for entry in site_table if entry.ambiguous),
            modified_peptide_count=len(
                {
                    entry.localized_peptide
                    for entry in peptide_entries
                }
            ),
            localization_entry_count=len(localization_scoring.entries),
            quantified_site_row_count=(
                0 if site_quantification is None else len(site_quantification.rows)
            ),
            differential_site_count=(
                0
                if differential_analysis is None
                else len(differential_analysis.differential_report.entries)
            ),
        ),
        note=(
            "ptm reporting assembles governed peptide observations, site rows, localization review, site quantification, and optional differential analysis into one owned report bundle"
        ),
    )


def render_ptm_report_summary_tsv(report: PtmReportBundle) -> str:
    """Render compact PTM report summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "accepted_evidence_count",
            "peptide_entry_count",
            "site_row_count",
            "ambiguous_site_count",
            "modified_peptide_count",
            "localization_entry_count",
            "quantified_site_row_count",
            "differential_site_count",
        ]
    )
    writer.writerow(
        [
            report.summary.accepted_evidence_count,
            report.summary.peptide_entry_count,
            report.summary.site_row_count,
            report.summary.ambiguous_site_count,
            report.summary.modified_peptide_count,
            report.summary.localization_entry_count,
            report.summary.quantified_site_row_count,
            report.summary.differential_site_count,
        ]
    )
    return buffer.getvalue()


def render_ptm_report_peptide_tsv(report: PtmReportBundle) -> str:
    """Render the PTM peptide-observation table as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "spectrum_id",
            "sample_id",
            "localized_peptide",
            "canonical_peptide",
            "sequence",
            "charge",
            "score",
            "q_value",
            "localization_score",
            "localization_probability",
            "protein_refs",
            "modification_names",
            "target_decoy_label",
        ]
    )
    for entry in report.peptide_entries:
        writer.writerow(
            [
                entry.spectrum_id,
                entry.sample_id or "",
                entry.localized_peptide,
                entry.canonical_peptide,
                entry.sequence,
                entry.charge,
                entry.score,
                "" if entry.q_value is None else entry.q_value,
                entry.localization_score,
                ""
                if entry.localization_probability is None
                else entry.localization_probability,
                ";".join(entry.protein_refs),
                ";".join(entry.modification_names),
                entry.target_decoy_label.value,
            ]
        )
    return buffer.getvalue()


def render_ptm_report_localization_tsv(report: PtmReportBundle) -> str:
    """Render the PTM localization review table as TSV."""

    return render_ptm_localization_scoring_entry_tsv(report.localization_scoring)


def render_ptm_report_site_quant_matrix_tsv(report: PtmReportBundle) -> str:
    """Render the PTM site-quant matrix section as TSV."""

    if report.site_quantification is None:
        raise ValueError("ptm report bundle does not include site quantification")
    return render_ptm_site_quant_matrix_tsv(report.site_quantification)


def render_ptm_report_differential_tsv(report: PtmReportBundle) -> str:
    """Render the PTM differential-results section as TSV."""

    if report.differential_analysis is None:
        raise ValueError("ptm report bundle does not include differential analysis")
    return render_ptm_site_differential_tsv(
        report.differential_analysis.differential_report
    )
