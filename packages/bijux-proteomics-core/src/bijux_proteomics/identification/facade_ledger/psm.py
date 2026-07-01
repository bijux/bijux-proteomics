# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed PSM facade ledger for identification owner modules."""

from __future__ import annotations

from bijux_proteomics.identification.facade_ledger.models import (
    IdentificationFacadeBudget,
    IdentificationFacadeModule,
    build_facade_module,
)

PSM_FACADE_BUDGET = IdentificationFacadeBudget(
    max_public_symbols=60,
    max_init_lines=70,
)


def list_identification_psm_api_modules() -> tuple[IdentificationFacadeModule, ...]:
    """Return the supported PSM owner-facade modules."""

    return (
        build_facade_module(
            "bijux_proteomics.identification.psm.contaminant_audit",
            "psm_audit_owner",
            "PSM contaminant audit and strategy-shift owner surface.",
            (
                "ContaminantStrategyShift",
                "ContaminantAwareProteinInferenceAudit",
                "ContaminantPeptideMatchReport",
                "build_contaminant_aware_protein_inference_audit",
                "build_contaminant_peptide_match_report",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.psm.contaminant_evidence",
            "psm_evidence_owner",
            "PSM contaminant evidence and burden rendering owner surface.",
            (
                "ContaminantBurdenEntry",
                "ContaminantEvidenceReport",
                "ContaminantEvidenceSummary",
                "ContaminantSeparatedPeptideEntry",
                "ContaminantSeparatedProteinEntry",
                "ContaminantSeparatedPsmEntry",
                "build_contaminant_evidence_report",
                "render_contaminant_burden_tsv",
                "render_contaminant_proteins_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.psm.generic_psm_mapper",
            "psm_mapping_owner",
            "Generic external PSM table mapping owner surface.",
            (
                "GenericPsmTableColumnMapping",
                "GenericMappedPsmRow",
                "GenericPsmMapperSummary",
                "GenericPsmMapperReport",
                "load_generic_psm_table_mapping",
                "build_generic_psm_mapper_report",
                "render_generic_psm_mapper_tsv",
                "render_generic_psm_rejected_row_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.psm.psm_features",
            "psm_feature_owner",
            "PSM feature extraction owner surface.",
            (
                "PsmFeatureRow",
                "extract_psm_features",
                "render_psm_feature_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.psm.psm_inspection",
            "psm_inspection_owner",
            "PSM evidence inspection and distribution owner surface.",
            (
                "PsmInspectionDistributionEntry",
                "PsmEvidenceInspectionReport",
                "build_psm_evidence_inspection_report",
                "render_psm_evidence_inspection_summary_tsv",
                "render_psm_inspection_distribution_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.psm.psm_rescoring",
            "psm_rescoring_owner",
            "PSM rescoring model and explanation owner surface.",
            (
                "PsmRescoringFeatureParameter",
                "PsmRescoringModel",
                "PsmRescoringEntry",
                "PsmRescoringExplanationEntry",
                "PsmRescoringSummary",
                "PsmRescoringReport",
                "fit_target_decoy_logistic_model",
                "explain_rescored_psm",
                "render_psm_rescoring_tsv",
                "render_psm_rescoring_explanation_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.psm.rejected_evidence_table",
            "psm_refusal_owner",
            "Rejected evidence table owner surface for parsed PSM rows.",
            (
                "RejectedEvidenceTableEntry",
                "build_rejected_evidence_rows_from_psm_rows",
                "build_rejected_evidence_rows_from_scientific_rows",
                "render_rejected_evidence_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.psm.score_separation_diagnostic",
            "psm_diagnostic_owner",
            "Score separation diagnostic owner surface for PSM evidence.",
            (
                "ScoreSeparationBin",
                "ScoreSeparationDiagnosticPolicy",
                "ScoreSeparationDiagnosticReport",
                "ScoreSeparationDiagnosticSummary",
                "ScoreSeparationWarningTier",
                "build_score_separation_diagnostic_report",
                "render_score_separation_bins_tsv",
                "render_score_separation_summary_tsv",
            ),
        ),
    )


__all__ = ["PSM_FACADE_BUDGET", "list_identification_psm_api_modules"]
