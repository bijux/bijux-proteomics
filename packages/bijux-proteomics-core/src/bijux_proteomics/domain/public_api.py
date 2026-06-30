# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Machine-readable public facade contract for the domain package."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DomainFacadeBudget:
    """Public export and initializer budget for the domain facade."""

    max_public_symbols: int
    max_init_lines: int


DOMAIN_FACADE_BUDGET = DomainFacadeBudget(
    max_public_symbols=150,
    max_init_lines=40,
)

_DOMAIN_FACADE_EXPORTS: tuple[tuple[str, str], ...] = (
    ("AssayRequirement", "bijux_proteomics.domain.assays"),
    ("STANDARD_CARD_TSV_COLUMNS", "bijux_proteomics.domain.card_schema"),
    ("ComplexMembership", "bijux_proteomics.domain.targets"),
    ("coerce_confidence_tier", "bijux_proteomics.domain.confidence"),
    ("ConfidenceTier", "bijux_proteomics.domain.confidence"),
    ("ConstraintCategory", "bijux_proteomics.domain.constraints"),
    ("ConstraintRiskReport", "bijux_proteomics.domain.constraints"),
    ("DecisionOwnerRole", "bijux_proteomics.domain.operating_model"),
    ("DecisionQuery", "bijux_proteomics.domain.repositories"),
    ("DesignError", "bijux_proteomics.domain.errors"),
    ("DuplicateReviewDecisionError", "bijux_proteomics.domain.repositories"),
    ("EvidenceNeed", "bijux_proteomics.domain.program_spec"),
    ("ImportedEvidenceProvenance", "bijux_proteomics.domain.records"),
    ("HYDROPATHY", "bijux_proteomics.domain.sequence"),
    ("LifecycleTransition", "bijux_proteomics.domain.lifecycle"),
    ("LiabilityCategory", "bijux_proteomics.domain.liabilities"),
    ("MeasurementDirection", "bijux_proteomics.domain.criteria"),
    ("MechanismLiability", "bijux_proteomics.domain.targets"),
    ("MetricFamily", "bijux_proteomics.domain.criteria"),
    ("OperatingModel", "bijux_proteomics.domain.operating_model"),
    ("OutcomeSeverity", "bijux_proteomics.domain.targets"),
    ("PKA_C_TERM", "bijux_proteomics.domain.sequence"),
    ("PKA_N_TERM", "bijux_proteomics.domain.sequence"),
    ("PKA_SIDE", "bijux_proteomics.domain.sequence"),
    ("PrimarySummary", "bijux_proteomics.domain.summary"),
    ("ProgramContext", "bijux_proteomics.domain.context"),
    ("ProgramDeliveryContext", "bijux_proteomics.domain.context"),
    ("ProgramLifecycle", "bijux_proteomics.domain.lifecycle"),
    ("ProgramLiability", "bijux_proteomics.domain.liabilities"),
    ("ProgramNotFoundError", "bijux_proteomics.domain.repositories"),
    ("ProgramPortfolioContext", "bijux_proteomics.domain.context"),
    ("ProgramRepository", "bijux_proteomics.domain.repositories"),
    ("ProgramRevisionConflictError", "bijux_proteomics.domain.repositories"),
    ("ProgramSpec", "bijux_proteomics.domain.program_spec"),
    ("ProgramStage", "bijux_proteomics.domain.program_spec"),
    ("ProteinGroup", "bijux_proteomics.domain.records"),
    ("ProteinRecord", "bijux_proteomics.domain.records"),
    ("ProteinDomain", "bijux_proteomics.domain.targets"),
    ("ProteinMotif", "bijux_proteomics.domain.targets"),
    ("ProteinTarget", "bijux_proteomics.domain.targets"),
    ("PSMRecord", "bijux_proteomics.domain.records"),
    ("PTMSite", "bijux_proteomics.domain.records"),
    ("PtmHotspot", "bijux_proteomics.domain.targets"),
    ("PeptideRecord", "bijux_proteomics.domain.records"),
    ("QuantEntityKind", "bijux_proteomics.domain.records"),
    ("QuantMatrix", "bijux_proteomics.domain.records"),
    ("QuantMeasureKind", "bijux_proteomics.domain.records"),
    ("RejectedEvidence", "bijux_proteomics.domain.records"),
    ("ReasonCodeCategory", "bijux_proteomics.domain.reason_codes"),
    ("ReasonCodeEntry", "bijux_proteomics.domain.reason_codes"),
    ("ReviewCadence", "bijux_proteomics.domain.operating_model"),
    ("ReviewDecision", "bijux_proteomics.domain.repositories"),
    ("ReviewDecisionRepository", "bijux_proteomics.domain.repositories"),
    ("ReviewGate", "bijux_proteomics.domain.reviews"),
    ("ReviewGateEvaluation", "bijux_proteomics.domain.repositories"),
    ("ReviewGateState", "bijux_proteomics.domain.repositories"),
    ("ReviewOutcome", "bijux_proteomics.domain.repositories"),
    ("ScientificConstraint", "bijux_proteomics.domain.constraints"),
    ("ScientificEvidenceError", "bijux_proteomics.domain.errors"),
    ("SecondarySummary", "bijux_proteomics.domain.summary"),
    ("SampleMetadata", "bijux_proteomics.domain.records"),
    ("SpectrumRecord", "bijux_proteomics.domain.records"),
    ("SchemaError", "bijux_proteomics.domain.errors"),
    ("StageEligibility", "bijux_proteomics.domain.program_spec"),
    ("StandardCardEntry", "bijux_proteomics.domain.card_schema"),
    ("StandardCardKind", "bijux_proteomics.domain.card_schema"),
    ("StandardCardSubjectKind", "bijux_proteomics.domain.card_schema"),
    ("SuccessCriterion", "bijux_proteomics.domain.criteria"),
    ("SemanticIdNamespace", "bijux_proteomics.domain.semantic_ids"),
    ("SourceRowLineage", "bijux_proteomics.domain.source_row_lineage"),
    ("TargetAnnotation", "bijux_proteomics.domain.targets"),
    ("TargetDecoyState", "bijux_proteomics.domain.records"),
    ("TargetOutcome", "bijux_proteomics.domain.targets"),
    ("TertiarySummary", "bijux_proteomics.domain.summary"),
    ("TransitionRecord", "bijux_proteomics.domain.records"),
    ("TractabilityFlag", "bijux_proteomics.domain.targets"),
    ("Contrast", "bijux_proteomics.domain.records"),
    ("ContrastKind", "bijux_proteomics.domain.records"),
    ("InvalidWorkflowError", "bijux_proteomics.domain.errors"),
    ("MissingValueState", "bijux_proteomics.domain.records"),
    ("ModifiedPeptide", "bijux_proteomics.domain.records"),
    ("UnsupportedFormatError", "bijux_proteomics.domain.errors"),
    ("advance_stage", "bijux_proteomics.domain.lifecycle"),
    ("allowed_next_stages", "bijux_proteomics.domain.lifecycle"),
    ("assess_constraint_risk", "bijux_proteomics.domain.constraints"),
    ("assess_stage_eligibility", "bijux_proteomics.domain.program_spec"),
    ("best_ca", "bijux_proteomics.domain.structure"),
    ("build_artifact_id", "bijux_proteomics.domain.semantic_ids"),
    ("build_assay_grounded_criteria", "bijux_proteomics.domain.criteria"),
    ("build_cross_study_card_id", "bijux_proteomics.domain.semantic_ids"),
    ("build_matrix_id", "bijux_proteomics.domain.semantic_ids"),
    ("build_mechanism_card_id", "bijux_proteomics.domain.semantic_ids"),
    ("build_pathway_card_id", "bijux_proteomics.domain.semantic_ids"),
    ("build_pathway_claim_id", "bijux_proteomics.domain.semantic_ids"),
    ("build_peptide_id", "bijux_proteomics.domain.semantic_ids"),
    ("build_protein_card_id", "bijux_proteomics.domain.semantic_ids"),
    ("build_protein_claim_id", "bijux_proteomics.domain.semantic_ids"),
    ("build_protein_native_constraints", "bijux_proteomics.domain.constraints"),
    ("build_protein_id", "bijux_proteomics.domain.semantic_ids"),
    ("build_protein_mechanism_card_id", "bijux_proteomics.domain.semantic_ids"),
    ("build_psm_id", "bijux_proteomics.domain.semantic_ids"),
    ("build_ptm_card_id", "bijux_proteomics.domain.semantic_ids"),
    ("build_ptm_claim_id", "bijux_proteomics.domain.semantic_ids"),
    ("build_raw_signal_card_id", "bijux_proteomics.domain.semantic_ids"),
    ("build_regulator_claim_id", "bijux_proteomics.domain.semantic_ids"),
    ("build_sample_card_id", "bijux_proteomics.domain.semantic_ids"),
    ("build_site_id", "bijux_proteomics.domain.semantic_ids"),
    ("classify_semantic_id", "bijux_proteomics.domain.semantic_ids"),
    ("create_program_spec", "bijux_proteomics.domain.program_spec"),
    ("criterion_passes", "bijux_proteomics.domain.criteria"),
    ("decision_timeline", "bijux_proteomics.domain.repositories"),
    ("ensure_semantic_id_namespace", "bijux_proteomics.domain.semantic_ids"),
    ("ensure_program_revision", "bijux_proteomics.domain.repositories"),
    ("ensure_review_clearance", "bijux_proteomics.domain.repositories"),
    ("ensure_unique_gate_decision", "bijux_proteomics.domain.repositories"),
    ("gdt_ha", "bijux_proteomics.domain.structure"),
    ("gdt_ts", "bijux_proteomics.domain.structure"),
    ("get_protein_chain", "bijux_proteomics.domain.structure"),
    ("is_registered_reason_code", "bijux_proteomics.domain.reason_codes"),
    ("kabsch_and_pairs", "bijux_proteomics.domain.structure"),
    ("latest_gate_decision", "bijux_proteomics.domain.repositories"),
    ("load_standard_card_tsv", "bijux_proteomics.domain.card_schema"),
    ("load_structure_from_pdb_text", "bijux_proteomics.domain.structure"),
    ("mean_plddt_from_ca_bfactor", "bijux_proteomics.domain.structure"),
    ("parse_structure_from_pdb_text", "bijux_proteomics.domain.structure"),
    ("per_residue_plddt_ss", "bijux_proteomics.domain.structure"),
    ("primary_summary_from_sequence", "bijux_proteomics.domain.sequence"),
    ("program_summary", "bijux_proteomics.domain.program_spec"),
    ("reason_code_categories", "bijux_proteomics.domain.reason_codes"),
    ("reason_code_registry", "bijux_proteomics.domain.reason_codes"),
    ("require_program", "bijux_proteomics.domain.repositories"),
    ("require_registered_reason_code", "bijux_proteomics.domain.reason_codes"),
    ("require_registered_reason_codes", "bijux_proteomics.domain.reason_codes"),
    ("render_standard_card_row", "bijux_proteomics.domain.card_schema"),
    ("residue_count", "bijux_proteomics.domain.structure"),
    ("revise_program", "bijux_proteomics.domain.program_spec"),
    ("secondary_summary_from_structure", "bijux_proteomics.domain.structure"),
    ("summarize_tractability", "bijux_proteomics.domain.targets"),
    ("target_summary", "bijux_proteomics.domain.targets"),
    ("tertiary_summary_from_structure", "bijux_proteomics.domain.structure"),
    ("tm_score", "bijux_proteomics.domain.structure"),
    ("validate_program", "bijux_proteomics.domain.validation"),
    ("validate_review_decision", "bijux_proteomics.domain.repositories"),
)


def build_domain_export_owner_map() -> dict[str, str]:
    """Return the governed export-owner map for the domain facade."""

    export_owner_map: dict[str, str] = {}
    for export_name, owner_module in _DOMAIN_FACADE_EXPORTS:
        if export_name in export_owner_map:
            raise ValueError(f"duplicate domain export: {export_name}")
        export_owner_map[export_name] = owner_module
    return export_owner_map


def list_domain_export_names() -> tuple[str, ...]:
    """Return ordered governed export names for the domain facade."""

    return tuple(export_name for export_name, _owner in _DOMAIN_FACADE_EXPORTS)


__all__ = [
    "DOMAIN_FACADE_BUDGET",
    "DomainFacadeBudget",
    "build_domain_export_owner_map",
    "list_domain_export_names",
]
