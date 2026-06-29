# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed peptide facade ledger for identification owner modules."""

from __future__ import annotations

from bijux_proteomics.identification.facade_ledger.models import (
    IdentificationFacadeBudget,
    IdentificationFacadeModule,
    build_facade_module,
)

PEPTIDE_FACADE_BUDGET = IdentificationFacadeBudget(
    max_public_symbols=35,
    max_init_lines=60,
)


def list_identification_peptide_api_modules() -> tuple[IdentificationFacadeModule, ...]:
    """Return the supported peptide owner-facade modules."""

    return (
        build_facade_module(
            "bijux_proteomics.identification.peptide.cross_run_reproducibility",
            "peptide_reproducibility_owner",
            "Cross-run reproducibility owner for peptide and protein evidence.",
            (
                "CrossRunEntityType",
                "CrossRunReproducibilityClass",
                "CrossRunReproducibilityEntry",
                "CrossRunReproducibilityReport",
                "CrossRunReproducibilitySummary",
                "RunDetectionContext",
                "build_peptide_cross_run_reproducibility_report",
                "build_protein_cross_run_reproducibility_report",
                "render_cross_run_reproducibility_entries_tsv",
                "render_cross_run_reproducibility_summary_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.peptide.error_rate_annotation",
            "peptide_annotation_owner",
            "Error-rate annotation owner for PSM-derived peptide evidence.",
            (
                "ErrorRateProvenanceFlag",
                "PsmErrorRateAnnotationEntry",
                "PsmErrorRateAnnotationPolicy",
                "PsmErrorRateAnnotationReport",
                "PsmErrorRateAnnotationSummary",
                "annotate_psm_error_rates",
                "build_psm_error_rate_annotation_report",
                "render_psm_error_rate_annotation_summary_tsv",
                "render_psm_error_rate_annotation_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.peptide.peptide_evidence",
            "peptide_evidence_owner",
            "Peptide evidence owner surface.",
            (
                "PeptideEvidenceClass",
                "PeptideEvidenceEntry",
                "PeptideEvidenceReport",
                "PeptideEvidenceSummary",
                "PeptideEvidenceTag",
                "build_peptide_evidence_report",
                "render_peptide_evidence_entries_tsv",
                "render_peptide_evidence_summary_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.peptide.peptide_evidence_review",
            "peptide_review_owner",
            "Peptide evidence review owner surface.",
            (
                "PeptideEvidencePrimaryClass",
                "PeptideEvidenceReviewEntry",
                "PeptideEvidenceReviewReport",
                "PeptideEvidenceReviewSummary",
                "build_peptide_evidence_review_report",
            ),
        ),
    )


__all__ = ["PEPTIDE_FACADE_BUDGET", "list_identification_peptide_api_modules"]
