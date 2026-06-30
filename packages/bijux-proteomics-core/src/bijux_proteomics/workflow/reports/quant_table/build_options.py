# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Build-option contracts for biological quant-table report assembly."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics.ptm import PtmEvidenceCardReport
from bijux_proteomics.quantification.contracts import NormalizationMethod
from bijux_proteomics.review.explanations.volcano_plots import VolcanoReviewPolicy
from bijux_proteomics.study import LcmsRunQcReport, QcRunAssessmentReport
from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
    BiologicalResultSelectionPolicy,
)


@dataclass(frozen=True)
class BiologicalReportQuantTableBuildOptions:
    """Governed options and supporting sources for quant-table report building."""

    proteins_fasta_path: Path
    variant_proteins_fasta_path: Path | None = None
    variant_peptide_tsv_path: Path | None = None
    protocol_context_tsv_path: Path | None = None
    annotation_tsv_path: Path | None = None
    context_annotation_tsv_path: Path | None = None
    protein_region_context_tsv_path: Path | None = None
    go_annotation_tsv_path: Path | None = None
    pathway_membership_tsv_path: Path | None = None
    complex_membership_tsv_path: Path | None = None
    regulator_evidence_tsv_path: Path | None = None
    regulator_site_signal_tsv_path: Path | None = None
    ptm_evidence_card_report: PtmEvidenceCardReport | None = None
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN
    condition_a: str | None = None
    condition_b: str | None = None
    selection_policy: BiologicalResultSelectionPolicy | None = None
    volcano_policy: VolcanoReviewPolicy | None = None
    lab_run_qc_feedback_report: object | None = None
    run_qc_reports: tuple[LcmsRunQcReport, ...] = ()
    run_qc_assessments: tuple[QcRunAssessmentReport, ...] = ()


def _build_biological_report_quant_table_build_options(
    *,
    proteins_fasta_path: Path,
    variant_proteins_fasta_path: Path | None = None,
    variant_peptide_tsv_path: Path | None = None,
    protocol_context_tsv_path: Path | None = None,
    annotation_tsv_path: Path | None = None,
    context_annotation_tsv_path: Path | None = None,
    protein_region_context_tsv_path: Path | None = None,
    go_annotation_tsv_path: Path | None = None,
    pathway_membership_tsv_path: Path | None = None,
    complex_membership_tsv_path: Path | None = None,
    regulator_evidence_tsv_path: Path | None = None,
    regulator_site_signal_tsv_path: Path | None = None,
    ptm_evidence_card_report: PtmEvidenceCardReport | None = None,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    selection_policy: BiologicalResultSelectionPolicy | None = None,
    volcano_policy: VolcanoReviewPolicy | None = None,
    lab_run_qc_feedback_report: object | None = None,
    run_qc_reports: tuple[LcmsRunQcReport, ...] = (),
    run_qc_assessments: tuple[QcRunAssessmentReport, ...] = (),
) -> BiologicalReportQuantTableBuildOptions:
    return BiologicalReportQuantTableBuildOptions(
        proteins_fasta_path=proteins_fasta_path,
        variant_proteins_fasta_path=variant_proteins_fasta_path,
        variant_peptide_tsv_path=variant_peptide_tsv_path,
        protocol_context_tsv_path=protocol_context_tsv_path,
        annotation_tsv_path=annotation_tsv_path,
        context_annotation_tsv_path=context_annotation_tsv_path,
        protein_region_context_tsv_path=protein_region_context_tsv_path,
        go_annotation_tsv_path=go_annotation_tsv_path,
        pathway_membership_tsv_path=pathway_membership_tsv_path,
        complex_membership_tsv_path=complex_membership_tsv_path,
        regulator_evidence_tsv_path=regulator_evidence_tsv_path,
        regulator_site_signal_tsv_path=regulator_site_signal_tsv_path,
        ptm_evidence_card_report=ptm_evidence_card_report,
        normalization_method=normalization_method,
        condition_a=condition_a,
        condition_b=condition_b,
        selection_policy=selection_policy,
        volcano_policy=volcano_policy,
        lab_run_qc_feedback_report=lab_run_qc_feedback_report,
        run_qc_reports=run_qc_reports,
        run_qc_assessments=run_qc_assessments,
    )


__all__ = [
    "BiologicalReportQuantTableBuildOptions",
    "_build_biological_report_quant_table_build_options",
]
