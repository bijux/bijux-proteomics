# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed adapter facade ledger for identification owner modules."""

from __future__ import annotations

from bijux_proteomics.identification.facade_ledger.models import (
    IdentificationFacadeBudget,
    IdentificationFacadeModule,
    build_facade_module,
)

ADAPTERS_FACADE_BUDGET = IdentificationFacadeBudget(
    max_public_symbols=120,
    max_init_lines=40,
)


def list_identification_adapter_api_modules() -> tuple[IdentificationFacadeModule, ...]:
    """Return the supported identification adapter-facade modules."""

    return (
        build_facade_module(
            "bijux_proteomics.identification.adapters.comet_import",
            "adapter_import_owner",
            "Comet import owner surface.",
            (
                "CometImportKind",
                "CometPsmReviewEntry",
                "CometCanonicalPsmEntry",
                "CometImportSummary",
                "CometImportReport",
                "build_comet_import_report",
                "render_comet_summary_tsv",
                "render_comet_canonical_psm_tsv",
                "render_comet_psm_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.adapters.diann_import",
            "adapter_import_owner",
            "DIA-NN import owner surface.",
            (
                "DiaNnPrecursorReviewEntry",
                "DiaNnProteinGroupReviewEntry",
                "DiaNnImportSummary",
                "DiaNnRejectedRowEntry",
                "DiaNnBundleImportReport",
                "build_diann_import_report",
                "render_diann_summary_tsv",
                "render_diann_precursor_tsv",
                "render_diann_protein_group_tsv",
                "render_diann_rejected_row_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.adapters.fragpipe_benchmarks",
            "adapter_benchmark_owner",
            "FragPipe import benchmark owner surface.",
            (
                "FragpipeCountComparisonEntry",
                "FragpipeImportBenchmarkReport",
                "FragpipeImportBenchmarkSummary",
                "FragpipeProteinGroupComparison",
                "FragpipeQValueBehaviorComparison",
                "FragpipeQValueComparisonEntry",
                "build_fragpipe_import_benchmark_report",
                "render_fragpipe_benchmark_summary_tsv",
                "render_fragpipe_count_comparisons_tsv",
                "render_fragpipe_protein_group_comparison_tsv",
                "render_fragpipe_q_value_comparison_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.adapters.fragpipe_import",
            "adapter_import_owner",
            "FragPipe import owner surface.",
            (
                "FragpipePsmReviewEntry",
                "FragpipeCanonicalPsmEntry",
                "FragpipePeptideReviewEntry",
                "FragpipeProteinReviewEntry",
                "FragpipeOpenSearchEvidenceEntry",
                "FragpipeProteinQuantityEntry",
                "FragpipeImportSummary",
                "FragpipeImportReport",
                "build_fragpipe_import_report",
                "render_fragpipe_summary_tsv",
                "render_fragpipe_canonical_psm_tsv",
                "render_fragpipe_psm_tsv",
                "render_fragpipe_peptide_tsv",
                "render_fragpipe_protein_tsv",
                "render_fragpipe_open_search_evidence_tsv",
                "render_fragpipe_protein_quantity_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.adapters.maxquant_import",
            "adapter_import_owner",
            "MaxQuant import owner surface.",
            (
                "MaxquantLfqIntensityEntry",
                "MaxquantEvidenceReviewEntry",
                "MaxquantPeptideReviewEntry",
                "MaxquantProteinGroupReviewEntry",
                "MaxquantLfqMatrixCandidateEntry",
                "MaxquantImportSummary",
                "MaxquantImportReport",
                "build_maxquant_import_report",
                "render_maxquant_summary_tsv",
                "render_maxquant_evidence_tsv",
                "render_maxquant_peptide_tsv",
                "render_maxquant_protein_group_tsv",
                "render_maxquant_lfq_candidate_tsv",
                "build_maxquant_lfq_matrix_candidates",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.adapters.openms_import",
            "adapter_import_owner",
            "OpenMS import owner surface.",
            (
                "OpenMsPsmReviewEntry",
                "OpenMsProteinReviewEntry",
                "OpenMsFeatureReviewEntry",
                "OpenMsFeatureValidationIssue",
                "OpenMsRejectedFeatureRow",
                "OpenMsImportSummary",
                "OpenMsFeatureParseSummary",
                "OpenMsImportReport",
                "build_openms_import_report",
                "render_openms_summary_tsv",
                "render_openms_psm_tsv",
                "render_openms_protein_tsv",
                "render_openms_feature_tsv",
                "render_openms_rejected_feature_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.adapters.sage_import",
            "adapter_import_owner",
            "Sage import owner surface.",
            (
                "SagePsmReviewEntry",
                "SageCanonicalPsmEntry",
                "SageImportSummary",
                "SageImportReport",
                "build_sage_import_report",
                "render_sage_summary_tsv",
                "render_sage_canonical_psm_tsv",
                "render_sage_psm_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.adapters.search_adapter_loss",
            "adapter_review_owner",
            "Search-adapter loss and parity owner surface.",
            (
                "SearchAdapterInformationLossReport",
                "ProteinInferenceDisagreementEntry",
                "ProteinInferenceEngineDisagreementDossier",
                "SearchAdapterParityCheck",
                "SearchAdapterParityReport",
                "build_search_adapter_information_loss_report",
                "build_protein_inference_engine_disagreement_dossier",
                "build_search_adapter_parity_report",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.adapters.spectronaut_import",
            "adapter_import_owner",
            "Spectronaut import owner surface.",
            (
                "SpectronautPrecursorReviewEntry",
                "SpectronautProteinGroupReviewEntry",
                "SpectronautPrecursorQuantityEntry",
                "SpectronautProteinGroupQuantityEntry",
                "SpectronautImportSummary",
                "SpectronautImportReport",
                "build_spectronaut_import_report",
                "render_spectronaut_summary_tsv",
                "render_spectronaut_precursor_tsv",
                "render_spectronaut_protein_group_tsv",
                "render_spectronaut_precursor_quantity_tsv",
                "render_spectronaut_protein_group_quantity_tsv",
            ),
        ),
    )


__all__ = ["ADAPTERS_FACADE_BUDGET", "list_identification_adapter_api_modules"]
