# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable registry over machine-readable scientific reason codes."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class ReasonCodeCategory(StrEnum):
    """Durable categories for scientific reason-code consumers."""

    VALIDATION_ISSUE = "validation_issue"
    RESULT_WARNING = "result_warning"
    REJECTED_EVIDENCE = "rejected_evidence"
    QC_REASON = "qc_reason"
    WORKFLOW_BLOCK = "workflow_block"
    WORKFLOW_ADVISORY = "workflow_advisory"
    CLAIM_DOWNGRADE = "claim_downgrade"


class ReasonCodeEntry(JsonModel):
    """One stable reason-code registry entry."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    categories: tuple[ReasonCodeCategory, ...] = Field(default_factory=tuple)


_VALIDATION_ISSUE_CODES = frozenset(
    {
        "absolute_archive_path",
        "absolute_artifact_path",
        "ambiguous_mass_delta",
        "ambiguous_ortholog_unresolved",
        "ambiguous_residue",
        "ambiguous_shared_run",
        "ambiguous_site_localization",
        "assay-ids-duplicate",
        "assay-panel-missing",
        "assay-panel-needs-assay-evidence",
        "background_not_broader_than_foreground",
        "batch_condition_confounding",
        "blocked_targets_present",
        "blocking-assay-missing",
        "blocking-gate-needs-blocking-assays",
        "blocking-gate-roles-missing",
        "blocking-review-gate-missing",
        "bound-criterion-invalid-threshold",
        "bound-criterion-upper-threshold-missing",
        "broken_encoding",
        "broken_pair",
        "candidate_position_out_of_range",
        "capacity_exceeded",
        "carryover_suspected",
        "confidence_normalization",
        "conflicting_controlled_id",
        "conflicting_effects_present",
        "conflicting_sample_identity",
        "confounded_batch_condition",
        "constraint-mitigation-missing",
        "contamination_burden",
        "contradicted_validation_present",
        "corrupt_table",
        "criterion-assay-unmapped",
        "criterion-ids-duplicate",
        "criterion-metrics-duplicate",
        "criterion-without-assay",
        "critical-failure-modes-missing",
        "dda_missing_target_decoy",
        "decision-owners-missing",
        "decoy_policy_mismatch",
        "decoy_ptm_evidence",
        "degenerate_contrast",
        "depletion_inefficiency",
        "dia_vs_dda_mixture",
        "digestion_consistency_not_assessed",
        "digestion_inefficiency",
        "digestion_specificity_drift",
        "digestion_specificity_mismatch",
        "downgraded_protein_present",
        "duplicate_accession",
        "duplicate_adapter_kind",
        "duplicate_contrast_id",
        "duplicate_id",
        "duplicate_identifier",
        "duplicate_run_channel_assignment",
        "duplicate_run_id",
        "duplicate_sample_id",
        "duplicate_spectrum_id",
        "duplicate_well_position",
        "elevated_contaminant_fraction",
        "elevated_contamination",
        "empty_background",
        "empty_covariate",
        "empty_file",
        "empty_foreground",
        "empty_required_field",
        "empty_search_table",
        "empty_sequence",
        "empty_table",
        "enrichment_evidence_not_assessed",
        "enrichment_inefficiency",
        "evidence-needs-empty",
        "evidence_code",
        "excluded_ambiguous_site_present",
        "excluded_protein_due_to_interference",
        "excluded_reverse_or_contaminant_present",
        "expected_native_fields_present",
        "explicit_decoy_contract",
        "failed_run_qc",
        "failure_disclosure",
        "filtered_protein_group",
        "filtered_psm_present",
        "flagged_run_qc",
        "foreground_outside_background",
        "high_interference_peptide_present",
        "hostile_filename",
        "human-review-unmodeled",
        "imported_semantics",
        "impossible_contrast",
        "incomplete_linked_fields",
        "incomplete_multiplex_assignment",
        "inconclusive_validation_present",
        "inconsistent_delimiter",
        "inconsistent_spectra_file",
        "insufficient_replicates",
        "invalid_block_labels",
        "invalid_character",
        "invalid_charge",
        "invalid_contrast_incomplete_pair",
        "invalid_contrast_insufficient_conditions",
        "invalid_contrast_kind",
        "invalid_contrast_row",
        "invalid_contrast_same_condition",
        "invalid_contrast_specification",
        "invalid_contrast_unknown_condition",
        "invalid_fraction_id",
        "invalid_fragment_tolerance",
        "invalid_intensity",
        "invalid_isolation_interference",
        "invalid_label",
        "invalid_modification_site",
        "invalid_modification_token",
        "invalid_modified_peptide",
        "invalid_multi_condition_specification",
        "invalid_multiplex_channel",
        "invalid_numeric_value",
        "invalid_peptide",
        "invalid_peptide_notation",
        "invalid_precursor_tolerance",
        "invalid_q_value",
        "invalid_reporter_intensity",
        "invalid_retention_window",
        "invalid_sample_metadata_row",
        "invalid_score",
        "invalid_well_position",
        "key-unknowns-missing",
        "lab-feedback-unmodeled",
        "learning-stage-assays-missing",
        "liability-evidence-missing",
        "liability-mitigation-assay-unmapped",
        "liability-owner-missing",
        "library_missing_library_scores",
        "limited_retention_coverage",
        "loss_accounting",
        "lowercase_residues",
        "malformed_archive_member",
        "malformed_header",
        "malformed_row",
        "malformed_search_table",
        "metadata_run_mismatch",
        "missing_batch_metadata",
        "missing_blocking_values",
        "missing_column_mapping",
        "missing_contrast_column",
        "missing_controls",
        "missing_database_path",
        "missing_decoy_entries",
        "missing_decoy_rules",
        "missing_decoy_strategy",
        "missing_expected_enrichment_sites",
        "missing_file",
        "missing_fragments",
        "missing_hash_ledger",
        "missing_header",
        "missing_mass_delta",
        "missing_metadata_sample",
        "missing_multiplex_channels",
        "missing_multiplex_group",
        "missing_occupancy_counterpart",
        "missing_pair_id",
        "missing_paired_comparison",
        "missing_pairing_metadata",
        "missing_peptide",
        "missing_protein_ref",
        "missing_protein_references",
        "missing_protein_sequence",
        "missing_randomization",
        "missing_replicate_layout",
        "missing_replicates",
        "missing_reporter_channel_signal",
        "missing_reporter_intensities",
        "missing_required_column",
        "missing_required_columns",
        "missing_required_output",
        "missing_sample_id",
        "missing_sample_metadata_column",
        "missing_sample_metadata_value",
        "missing_samples",
        "missing_schema_refs",
        "missing_site_evidence",
        "missing_site_index",
        "missing_site_level_decoy_support",
        "missing_source_species",
        "missing_species",
        "missing_spectrum_id",
        "missing_target_decoy_evidence",
        "missing_target_species",
        "missing_targets",
        "missing_technical_replicate_id",
        "missing_timepoint",
        "missing_timepoint_metadata",
        "missing_timepoint_order",
        "modality-context-missing",
        "multiple_c_terminal_modifications",
        "multiple_n_terminal_modifications",
        "negative_intensity",
        "negative_reporter_intensity",
        "non_dia_context",
        "non_site_confidence_family",
        "open_vs_library_mixture",
        "overlapping_explicit_values",
        "overlapping_modification_definition",
        "oversized_record",
        "partial_assay_coverage",
        "path_traversal",
        "peptide_definition_mismatch",
        "peptide_site_out_of_range",
        "protein_assignment_mismatch",
        "protein_c_term_context_required",
        "protein_group_discrepancy_present",
        "protein_n_term_context_required",
        "protein_position_out_of_range",
        "protein_reference_contract",
        "ptm_evidence_input_invalid",
        "ptm_protein_correction_not_requested",
        "q_value_above_threshold",
        "q_value_contract",
        "rejected_claim_present",
        "rejected_design_rows",
        "rejected_evidence_present",
        "rejected_input_row_present",
        "rejected_invalid_q_value_rows",
        "rejected_invalid_score_rows",
        "rejected_psm_row",
        "rejected_row",
        "rejected_scientific_row",
        "reporter_channel_evidence_not_assessed",
        "reporter_channel_input_invalid",
        "residue_incompatible",
        "residue_mismatch",
        "result_family_mismatch",
        "review-gate-ids-duplicate",
        "review-gates-missing",
        "review-input-unmapped",
        "review-inputs-duplicate",
        "review-needs-assay-evidence",
        "run_qc_failure",
        "sample_missing_decoy_matches",
        "sample_swap_suspected",
        "score_family_mismatch",
        "sex_marker_mismatch",
        "shared_base_accession_pairs",
        "singleton_condition_typo",
        "source_rejected_rows_present",
        "sparse_expected_enrichment_sites",
        "sparse_quant_signal",
        "sparse_reporter_channel_signal",
        "species_marker_mismatch",
        "stable_normalized_order",
        "stop_codon",
        "success-criteria-missing",
        "target-class-missing",
        "target-localization-missing",
        "target_missing_expected_evidence",
        "terminal_label_collision",
        "terminal_stop_codon_removed",
        "translational-assumptions-missing",
        "unexpected_reporter_channel_signal",
        "unknown_adapter_dialect",
        "unknown_blocking_field",
        "unknown_condition",
        "unknown_contrast_condition",
        "unknown_controlled_id",
        "unknown_covariate",
        "unknown_enzyme",
        "unknown_mass_delta",
        "unknown_modification",
        "unmapped_explicit_labels",
        "unreliable_target_present",
        "unsupported_method",
        "unsupported_multiple_testing_scope",
        "unsupported_residue",
        "weak_identification_signal",
        "weak_localization_score",
        "whitespace_removed",
        "wrong_type",
        "xml_entity_abuse",
    }
)

_RESULT_WARNING_CODES = frozenset(
    {
        "ambiguous_ortholog_unresolved",
        "blocked_targets_present",
        "conflicting_effects_present",
        "contradicted_validation_present",
        "downgraded_protein_present",
        "excluded_ambiguous_site_present",
        "excluded_protein_due_to_interference",
        "excluded_reverse_or_contaminant_present",
        "filtered_psm_present",
        "flagged_run_qc",
        "high_interference_peptide_present",
        "inconclusive_validation_present",
        "missing_occupancy_counterpart",
        "missing_required_output",
        "partial_assay_coverage",
        "protein_group_discrepancy_present",
        "rejected_claim_present",
        "rejected_evidence_present",
        "rejected_input_row_present",
        "run_qc_failure",
        "section_confidence_invalid",
        "section_confidence_weak",
        "source_rejected_rows_present",
        "unreliable_target_present",
    }
)

_REJECTED_EVIDENCE_CODES = frozenset(
    {
        "contaminant",
        "contradicted",
        "excluded_due_to_interference",
        "filtered_protein_group",
        "inconclusive",
        "missing_pair_id",
        "missing_from_source_summary_but_inferred_and_quantified",
        "missing_from_source_summary_but_inferred_only",
        "missing_from_source_summary_but_marked_significant_only",
        "missing_from_source_summary_but_present_in_workflow",
        "missing_from_source_summary_but_quantified_only",
        "missing_lfq_signal",
        "missing_protein_refs",
        "only_identified_by_site",
        "present_in_source_summary_only",
        "protein_assignment_mismatch",
        "rejected_psm_row",
        "rejected_row",
        "rejected_scientific_row",
        "reverse",
        "shared_between_source_and_workflow",
    }
)

_QC_REASON_CODES = frozenset(
    {
        "carryover_suspected",
        "contaminant_psm_fraction",
        "contamination_burden",
        "depletion_inefficiency",
        "digestion_inefficiency",
        "elevated_contaminant_fraction",
        "enrichment_inefficiency",
        "identification_rate",
        "internal_standard_drift",
        "internal_standard_missing",
        "limited_retention_coverage",
        "median_abs_mass_error_ppm",
        "median_spectrum_count",
        "missed_cleavage_rate",
        "non_specific_fraction",
        "outlier_run_count",
        "sample_swap_suspected",
        "sex_marker_mismatch",
        "sparse_quant_signal",
        "species_marker_mismatch",
        "spectrum_count",
        "weak_identification_signal",
    }
)

_WORKFLOW_BLOCK_CODES = frozenset(
    {
        "ambiguous_ptm_localization",
        "confounded_batch_condition",
        "decision_grade_with_ambiguous_ptm",
        "decision_grade_with_high_missingness",
        "decision_grade_with_qc_blockers",
        "decision_grade_with_quant_blockers",
        "empty_digestion_space",
        "external_engine_disagreement",
        "failed_qc_blocks_biological_promotion",
        "identification_rate",
        "insufficient_replicates",
        "carryover",
        "digestion_issues_present",
        "missing_channel_pressure",
        "multi_batch_shift",
        "ptm_support_outside_identification",
        "qc_clean_decision_allowed",
        "quant_support_outside_identification",
        "review_projection_without_candidates",
        "shared_peptide_pressure",
        "target_decoy_collision",
    }
)

_WORKFLOW_ADVISORY_CODES = frozenset(
    {
        "batch_shift_warning",
        "within_condition_replicate_instability",
    }
)

_CLAIM_DOWNGRADE_CODES = frozenset(
    {
        "background_peptide_overlap",
        "contaminant_overlap",
        "contaminant_support",
        "contradiction_caution",
        "decoy_support",
        "group_q_value_above_high_confidence",
        "group_q_value_above_moderate",
        "imputation_dependence",
        "insufficient_exported_transitions",
        "intrinsic_transition_risk",
        "library_coelution_competitor",
        "library_fragment_overlap",
        "low_localization",
        "moderate_unique_peptide_support",
        "panel_fragment_overlap",
        "poor_reproducibility",
        "poor_run_qc",
        "severe_contradiction",
        "shared_peptide",
        "shared_peptide_only",
        "single_run_only",
        "weak_or_ambiguous_unique_peptide_support",
    }
)

_CODES_BY_CATEGORY = {
    ReasonCodeCategory.VALIDATION_ISSUE: _VALIDATION_ISSUE_CODES,
    ReasonCodeCategory.RESULT_WARNING: _RESULT_WARNING_CODES,
    ReasonCodeCategory.REJECTED_EVIDENCE: _REJECTED_EVIDENCE_CODES,
    ReasonCodeCategory.QC_REASON: _QC_REASON_CODES,
    ReasonCodeCategory.WORKFLOW_BLOCK: _WORKFLOW_BLOCK_CODES,
    ReasonCodeCategory.WORKFLOW_ADVISORY: _WORKFLOW_ADVISORY_CODES,
    ReasonCodeCategory.CLAIM_DOWNGRADE: _CLAIM_DOWNGRADE_CODES,
}

_CATEGORY_LOOKUP: dict[str, tuple[ReasonCodeCategory, ...]] = {}
for category, codes in _CODES_BY_CATEGORY.items():
    for code in sorted(codes):
        _CATEGORY_LOOKUP.setdefault(code, tuple())
        if category not in _CATEGORY_LOOKUP[code]:
            _CATEGORY_LOOKUP[code] = (*_CATEGORY_LOOKUP[code], category)


def reason_code_registry() -> tuple[ReasonCodeEntry, ...]:
    """Return the full stable reason-code registry."""

    return tuple(
        ReasonCodeEntry(code=code, categories=tuple(sorted(categories, key=lambda value: value.value)))
        for code, categories in sorted(_CATEGORY_LOOKUP.items())
    )


def reason_code_categories(code: str) -> tuple[ReasonCodeCategory, ...]:
    """Return all registered categories for one reason code."""

    return _CATEGORY_LOOKUP.get(code, ())


def is_registered_reason_code(
    code: str,
    *categories: ReasonCodeCategory,
) -> bool:
    """Return whether one code is registered in any requested category."""

    registered_categories = set(reason_code_categories(code))
    if not registered_categories:
        return False
    if not categories:
        return True
    return any(category in registered_categories for category in categories)


def require_registered_reason_code(
    code: str,
    *categories: ReasonCodeCategory,
) -> str:
    """Validate and return one registered reason code."""

    normalized = code.strip()
    if is_registered_reason_code(normalized, *categories):
        return normalized
    expected = ", ".join(category.value for category in categories) or "any registered category"
    raise ValueError(
        f"reason code {normalized!r} is not registered for {expected}"
    )


def require_registered_reason_codes(
    codes: tuple[str, ...],
    *categories: ReasonCodeCategory,
) -> tuple[str, ...]:
    """Validate and return a tuple of registered reason codes."""

    return tuple(
        require_registered_reason_code(code, *categories) for code in codes
    )


__all__ = [
    "ReasonCodeCategory",
    "ReasonCodeEntry",
    "is_registered_reason_code",
    "reason_code_categories",
    "reason_code_registry",
    "require_registered_reason_code",
    "require_registered_reason_codes",
]
