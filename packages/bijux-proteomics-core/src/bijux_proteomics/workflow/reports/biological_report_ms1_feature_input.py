# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""MS1 feature-table entrypoint for biological report bundle assembly."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.ptm import PtmEvidenceCardReport
from bijux_proteomics.quantification.contracts import (
    Ms1FeatureColumnMapping,
    NormalizationMethod,
    QuantRollupMethod,
)
from bijux_proteomics.review.explanations.volcano_plots import VolcanoReviewPolicy
from bijux_proteomics.study import (
    ExperimentDesign,
    LcmsRunQcReport,
    QcRunAssessmentReport,
    coerce_experiment_design,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
    BiologicalResultSelectionPolicy,
    _resolve_biological_result_selection_policy,
)
from bijux_proteomics.workflow.reports.biological_report_ms1_feature_quant_table import (
    _build_biological_quant_table_from_ms1_feature_input,
)


def build_biological_result_report_bundle_from_ms1_feature_input(
    input_tsv_path: Path,
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
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
    mapping: Ms1FeatureColumnMapping | None = None,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    top_n: int = 3,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    selection_policy: BiologicalResultSelectionPolicy | None = None,
    volcano_policy: VolcanoReviewPolicy | None = None,
    lab_run_qc_feedback_report: object | None = None,
    run_qc_reports: tuple[LcmsRunQcReport, ...] = (),
    run_qc_assessments: tuple[QcRunAssessmentReport, ...] = (),
    chunk_size_rows: int | None = None,
) -> BiologicalResultReportBundle:
    """Build a biological report bundle from an MS1 feature table input."""

    from bijux_proteomics.workflow.reports.biological_report_assembly import (
        build_biological_result_report_bundle_from_quant_table,
    )

    experiment_design = coerce_experiment_design(design_entries)
    active_selection_policy = _resolve_biological_result_selection_policy(
        selection_policy,
        protocol_context_tsv_path=protocol_context_tsv_path,
    )
    quant_table = _build_biological_quant_table_from_ms1_feature_input(
        input_tsv_path,
        mapping=mapping,
        aggregation_method=aggregation_method,
        top_n=top_n,
        chunk_size_rows=chunk_size_rows,
    )
    return build_biological_result_report_bundle_from_quant_table(
        quant_table,
        experiment_design,
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
        selection_policy=active_selection_policy,
        volcano_policy=volcano_policy,
        # Keep the lab-owned QC feedback contract out of this wrapper module and
        # forward it opaquely to the deeper assembly surface that owns the
        # cross-package exception.
        lab_run_qc_feedback_report=cast(Any, lab_run_qc_feedback_report),
        run_qc_reports=run_qc_reports,
        run_qc_assessments=run_qc_assessments,
    )
