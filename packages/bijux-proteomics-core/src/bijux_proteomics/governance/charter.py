# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Machine-readable charter for the core scientific package boundary."""

from __future__ import annotations

import ast
from enum import StrEnum
from pathlib import Path
import re

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class CoreScientificDomainFamily(StrEnum):
    """Durable domain families that core is allowed to own."""

    PROGRAM_GOVERNANCE = "program_governance"
    SEQUENCE_AND_CHEMISTRY = "sequence_and_chemistry"
    INGESTION_AND_IDENTIFICATION = "ingestion_and_identification"
    QUANTIFICATION_AND_STUDY = "quantification_and_study"
    PTM_AND_DIA = "ptm_and_dia"
    REVIEW_AND_HANDOFF = "review_and_handoff"
    WORKFLOW_CONTRACTS = "workflow_contracts"
    PACKAGE_SURFACE = "package_surface"


class CoreModuleClassification(StrEnum):
    """Allowed audit outcomes for core source modules."""

    SUBSTANTIVE_SCIENTIFIC_SURFACE = "substantive_scientific_surface"
    THIN_ABSTRACTION = "thin_abstraction"
    COMPATIBILITY_EXPORT = "compatibility_export"
    BOUNDARY_GOVERNANCE = "boundary_governance"
    WRONG_PACKAGE_LOGIC = "wrong_package_logic"


class CoreProductCharter(JsonModel):
    """Durable scientific charter for core ownership."""

    model_config = ConfigDict(extra="forbid")

    package_name: str = Field(..., min_length=1)
    value_statement: str = Field(..., min_length=1)
    domain_families: tuple[CoreScientificDomainFamily, ...] = Field(
        default_factory=tuple
    )
    required_inputs: tuple[str, ...] = Field(default_factory=tuple)
    excluded_ownership: tuple[str, ...] = Field(default_factory=tuple)


class CoreDomainFamilyEntry(JsonModel):
    """One durable family of scientific ownership inside core."""

    model_config = ConfigDict(extra="forbid")

    family: CoreScientificDomainFamily
    owned_surface: str = Field(..., min_length=1)
    required_modules: tuple[str, ...] = Field(..., min_length=1)
    release_blocker: str = Field(..., min_length=1)


class CoreModuleAuditEntry(JsonModel):
    """Audit record for one core source module."""

    model_config = ConfigDict(extra="forbid")

    module_path: str = Field(..., min_length=1)
    family: CoreScientificDomainFamily
    classification: CoreModuleClassification
    reason: str = Field(..., min_length=1)


DEFAULT_CORE_CHARTER = CoreProductCharter(
    package_name="bijux-proteomics-core",
    value_statement=(
        "provide the scientific heart of the suite through proteomics domain models, "
        "evidence normalization, uncertainty-aware review artifacts, and workflow "
        "contracts without taking over runtime execution, reference curation, "
        "analytical judgment, or lab operations"
    ),
    domain_families=(
        CoreScientificDomainFamily.PROGRAM_GOVERNANCE,
        CoreScientificDomainFamily.SEQUENCE_AND_CHEMISTRY,
        CoreScientificDomainFamily.INGESTION_AND_IDENTIFICATION,
        CoreScientificDomainFamily.QUANTIFICATION_AND_STUDY,
        CoreScientificDomainFamily.PTM_AND_DIA,
        CoreScientificDomainFamily.REVIEW_AND_HANDOFF,
        CoreScientificDomainFamily.WORKFLOW_CONTRACTS,
        CoreScientificDomainFamily.PACKAGE_SURFACE,
    ),
    required_inputs=(
        "foundation-owned document, hashing, refusal, and provenance primitives",
        "runtime-owned execution backends only through explicit adapters",
    ),
    excluded_ownership=(
        "runtime provider binding and run orchestration",
        "knowledge reference curation and ontology registries",
        "intelligence ranking and recommendation judgment",
        "lab scheduling, protocol control, and operational readiness authority",
    ),
)


DEFAULT_CORE_DOMAIN_ENTRIES: tuple[CoreDomainFamilyEntry, ...] = (
    CoreDomainFamilyEntry(
        family=CoreScientificDomainFamily.PROGRAM_GOVERNANCE,
        owned_surface="Program, target, canonical scientific record, review-gate, and validation semantics that define durable scientific state and progression meaning.",
        required_modules=(
            "domain/confidence.py",
            "domain/program_spec.py",
            "domain/programs.py",
            "domain/records.py",
            "domain/semantic_ids.py",
            "domain/targets.py",
            "domain/validation.py",
        ),
        release_blocker="Core cannot ship if lifecycle and program-state semantics fragment into wrapper-only convenience surfaces or downstream reinterpretation.",
    ),
    CoreDomainFamilyEntry(
        family=CoreScientificDomainFamily.SEQUENCE_AND_CHEMISTRY,
        owned_surface="Sequence parsing, digestion, amino-acid mass calculation, peptide chemistry, isotope labeling, and modification semantics for proteomics evidence preparation.",
        required_modules=(
            "sequences/core.py",
            "sequences/protein_identity_resolution.py",
            "sequences/digestion.py",
            "sequences/protein_region_context.py",
            "sequences/proteogenomic_peptide_support.py",
            "sequences/peptide_chemical_liability.py",
            "sequences/peptide_detectability.py",
            "sequences/peptide_uniqueness_index.py",
            "sequences/protein_index.py",
            "sequences/theoretical_digest.py",
            "chemistry/__init__.py",
            "chemistry/amino_acid_mass.py",
            "chemistry/contracts/__init__.py",
            "chemistry/contracts/fragment_ions.py",
            "chemistry/contracts/mass_projection.py",
            "chemistry/contracts/models.py",
            "chemistry/contracts/modified_peptides.py",
            "chemistry/contracts/registry_access.py",
            "chemistry/isotope_envelope.py",
            "chemistry/modification_packs.py",
            "chemistry/modification_registry.py",
            "chemistry/modified_peptide_parser.py",
            "chemistry/public_api.py",
        ),
        release_blocker="Core cannot ship if sequence and peptide semantics collapse into format glue or tool-specific heuristics.",
    ),
    CoreDomainFamilyEntry(
        family=CoreScientificDomainFamily.INGESTION_AND_IDENTIFICATION,
        owned_surface="Format ingestion, spectrum parsing, search normalization, target-decoy handling, and protein-inference-ready evidence contracts.",
        required_modules=(
            "tabular.py",
            "scientific_tables.py",
            "_output_tables.py",
            "_tabular.py",
            "_scientific_tables.py",
            "io/formats/__init__.py",
            "io/formats/format_validation.py",
            "io/formats/proteomics_formats.py",
            "io/formats/ingestion.py",
            "io/formats/input_integrity.py",
            "io/formats/spectral_library.py",
            "io/formats/spectral_library_intensity_agreement.py",
            "io/tables/__init__.py",
            "io/tables/stable_outputs.py",
            "io/tables/target_panel.py",
            "io/tables/transition_table.py",
            "io/tables/xic_target_table.py",
            "io/raw/__init__.py",
            "io/raw/deisotoping.py",
            "io/raw/mgf_streaming.py",
            "io/raw/mzml_reader.py",
            "io/raw/noise.py",
            "io/raw/run_qc.py",
            "io/raw/xic_extraction.py",
            "io/raw/chromatographic_peak_picking.py",
            "io/raw/retention_time_alignment.py",
            "io/raw/chromatographic_evidence.py",
            "io/raw/dia_fragment_coelution.py",
            "io/raw/fragment_ratio_stability.py",
            "io/raw/precursor_isotope_fit.py",
            "io/raw/raw_signal_evidence_cards.py",
            "io/spectra/__init__.py",
            "io/spectra/spectrum_contracts/__init__.py",
            "io/spectra/spectrum_entropy.py",
            "io/spectra/spectrum_peak_matching.py",
            "io/spectra/chimeric_spectrum.py",
            "io/spectra/precursor_validation.py",
            "io/chromatography/__init__.py",
            "io/chromatography/xic.py",
            "io/chromatography/chromatographic_peak_picking.py",
            "io/chromatography/retention_time_alignment.py",
            "io/chromatography/chromatographic_evidence.py",
            "io/chromatography/dia_fragment_coelution.py",
            "io/chromatography/fragment_ratio_stability.py",
            "identification/contracts/__init__.py",
            "identification/contracts/psm.py",
            "identification/contracts/psm_io.py",
            "identification/contracts/evidence.py",
            "identification/contracts/score_fdr.py",
            "identification/contracts/fdr_levels.py",
            "identification/contracts/grouping.py",
            "identification/contracts/protein_inference.py",
            "identification/contracts/protein_review.py",
            "identification/contracts/confidence.py",
            "identification/contracts/review.py",
            "identification/psm/__init__.py",
            "identification/psm/contaminant_audit.py",
            "identification/psm/contaminant_evidence.py",
            "identification/psm/generic_psm_mapper.py",
            "identification/psm/psm_features.py",
            "identification/psm/psm_inspection.py",
            "identification/psm/psm_rescoring.py",
            "identification/psm/rejected_evidence_table.py",
            "identification/psm/score_separation_diagnostic.py",
            "identification/peptide/__init__.py",
            "identification/peptide/cross_run_reproducibility.py",
            "identification/peptide/error_rate_annotation.py",
            "identification/peptide/peptide_evidence.py",
            "identification/peptide/peptide_evidence_review.py",
            "identification/protein/__init__.py",
            "identification/protein/parsimony_review.py",
            "identification/protein/protein_ambiguity_review.py",
            "identification/protein/protein_coverage.py",
            "identification/protein/protein_coverage_review.py",
            "identification/protein/protein_coverage_visualization.py",
            "identification/protein/protein_evidence.py",
            "identification/protein/protein_evidence_review.py",
            "identification/protein/protein_grouping.py",
            "identification/protein/protein_grouping_review.py",
            "identification/protein/protein_inference_benchmarks.py",
            "identification/protein/protein_parsimony.py",
            "identification/fdr/__init__.py",
            "identification/fdr/calibration_benchmarks.py",
            "identification/fdr/calibration_drift.py",
            "identification/fdr/confidence.py",
            "identification/fdr/evidence_level_fdr_review.py",
            "identification/fdr/peptide_target_decoy_fdr.py",
            "identification/fdr/picked_protein_fdr.py",
            "identification/fdr/picked_protein_fdr_review.py",
            "identification/fdr/protein_target_decoy_fdr.py",
            "identification/fdr/psm_target_decoy_fdr.py",
            "identification/fdr/target_decoy_benchmarks.py",
            "identification/fdr/target_decoy_reference_validation.py",
            "identification/adapters/__init__.py",
            "identification/adapters/comet_import.py",
            "identification/adapters/diann_import.py",
            "identification/adapters/fragpipe_benchmarks.py",
            "identification/adapters/fragpipe_import/bundle_report.py",
            "identification/adapters/maxquant_import.py",
            "identification/adapters/openms_import.py",
            "identification/adapters/sage_import.py",
            "identification/adapters/search_adapter_loss.py",
            "identification/adapters/spectronaut_import.py",
            "identification/search_adapters/__init__.py",
            "identification/search_adapters/comparison.py",
            "identification/search_adapters/conformance.py",
            "identification/search_adapters/contracts.py",
            "identification/search_adapters/corpus.py",
            "identification/search_adapters/corpus_matrix.py",
            "identification/search_adapters/engines/comet.py",
            "identification/search_adapters/engines/diann.py",
            "identification/search_adapters/engines/generic.py",
            "identification/search_adapters/engines/maxquant.py",
            "identification/search_adapters/engines/msfragger.py",
            "identification/search_adapters/engines/sage.py",
            "identification/search_adapters/engines/spectronaut.py",
            "identification/search_adapters/family_policy.py",
            "identification/search_adapters/input_review.py",
            "identification/search_adapters/normalization.py",
            "identification/search_adapters/parameter_review.py",
            "identification/search_adapters/parameter_support.py",
            "identification/search_adapters/registry.py",
            "identification/search_adapters/regression.py",
        ),
        release_blocker="Core cannot ship if external-engine normalization loses explicit support, loss, and refusal boundaries.",
    ),
    CoreDomainFamilyEntry(
        family=CoreScientificDomainFamily.QUANTIFICATION_AND_STUDY,
        owned_surface="Study metadata and experiment-design semantics together with lab-facing QC, troubleshooting, and planning surfaces for reproducible quantitative analysis.",
        required_modules=(
            "study/design/__init__.py",
            "study/design/contrasts.py",
            "study/design/design_classification.py",
            "study/design/design_diagnostics.py",
            "study/design/design_validity.py",
            "study/design/experiment_confidence.py",
            "study/design/experiment_design.py",
            "study/design/experiment_feasibility.py",
            "study/design/replicate_structure.py",
            "study/metadata/__init__.py",
            "study/metadata/contracts.py",
            "study/metadata/sample_metadata.py",
            "study/metadata/sample_run_identity.py",
            "study/metadata/sample_sheet_repairs.py",
            "lab/__init__.py",
            "lab/actions.py",
            "lab/background.py",
            "lab/carryover.py",
            "lab/cohort.py",
            "lab/contamination.py",
            "lab/digestion_diagnosis.py",
            "lab/lc_drift.py",
            "lab/operations.py",
            "lab/planning.py",
            "lab/protocol_consistency.py",
            "lab/protocol_context.py",
            "lab/qc/__init__.py",
            "lab/qc/assessment.py",
            "lab/qc/models.py",
            "lab/qc/review_artifacts.py",
            "lab/qc/run_reports.py",
            "lab/qc/summaries.py",
            "lab/qc/support.py",
            "lab/qc_benchmarks.py",
            "lab/run_diagnosis.py",
            "lab/sample_identity.py",
            "lab/standards.py",
            "quantification/contracts/__init__.py",
            "quantification/contracts/artifact_bundle.py",
            "quantification/contracts/design.py",
            "quantification/contracts/differential.py",
            "quantification/contracts/input_models.py",
            "quantification/contracts/input_parsing.py",
            "quantification/contracts/label_based.py",
            "quantification/contracts/matrix_building.py",
            "quantification/contracts/matrix_models.py",
            "quantification/contracts/missingness.py",
            "quantification/contracts/normalization_imputation.py",
            "quantification/contracts/protein_rollup.py",
            "quantification/contracts/study_qc.py",
            "quantification/matrix/__init__.py",
            "quantification/matrix/core_matrix.py",
            "quantification/matrix/design_matrix.py",
            "quantification/matrix/matrix_archive.py",
            "quantification/matrix/peptide_intensity_matrix.py",
            "quantification/matrix/protein_intensity_matrix.py",
            "quantification/rollup/__init__.py",
            "quantification/rollup/model_rollup.py",
            "quantification/rollup/protein_lfq/__init__.py",
            "quantification/rollup/protein_lfq/builders.py",
            "quantification/rollup/protein_lfq/models.py",
            "quantification/rollup/protein_lfq/rendering.py",
            "quantification/rollup/protein_lfq/row_assembly.py",
            "quantification/rollup/protein_lfq/solving.py",
            "quantification/normalization/__init__.py",
            "quantification/normalization/batch_effect.py",
            "quantification/normalization/composition.py",
            "quantification/normalization/imputation.py",
            "quantification/normalization/normalization.py",
            "quantification/missingness/__init__.py",
            "quantification/missingness/missingness.py",
            "quantification/missingness/summaries/__init__.py",
            "quantification/missingness/summaries/condition_summary.py",
            "quantification/missingness/summaries/entity_summary.py",
            "quantification/missingness/summaries/sample_summary.py",
            "quantification/missingness/peptide_profile_inconsistency.py",
            "quantification/missingness/readiness.py",
            "quantification/statistics/__init__.py",
            "quantification/statistics/censored_differential.py",
            "quantification/statistics/differential_abundance/__init__.py",
            "quantification/statistics/differential_abundance/analysis.py",
            "quantification/statistics/differential_abundance/contrast_statistics.py",
            "quantification/statistics/differential_abundance/design_context.py",
            "quantification/statistics/differential_abundance/observation_vectors.py",
            "quantification/statistics/differential_abundance/rendering.py",
            "quantification/statistics/differential_abundance/weighting.py",
            "quantification/statistics/differential_imputation_dependence.py",
            "quantification/statistics/differential_result_robustness/__init__.py",
            "quantification/statistics/differential_result_robustness/analysis.py",
            "quantification/statistics/differential_result_robustness/bootstrap.py",
            "quantification/statistics/differential_result_robustness/entry_builders.py",
            "quantification/statistics/differential_result_robustness/models.py",
            "quantification/statistics/differential_result_robustness/scoring_policy.py",
            "quantification/statistics/method_agreement.py",
            "quantification/statistics/multi_contrast_consistency.py",
            "quantification/statistics/peptide_level_differential.py",
            "quantification/statistics/power_estimation.py",
            "quantification/statistics/statistical_backend.py",
            "quantification/statistics/time_course_differential.py",
            "quantification/statistics/uncertainty.py",
            "quantification/statistics/variance_model.py",
            "quantification/provenance/__init__.py",
            "quantification/provenance/benchmarks.py",
            "quantification/provenance/heatmap_preparation.py",
            "quantification/provenance/replicate_qc.py",
            "quantification/provenance/review/__init__.py",
            "quantification/provenance/review/models.py",
            "quantification/provenance/review/bundle_assembly.py",
            "quantification/provenance/sample_exploration/__init__.py",
            "quantification/provenance/sample_exploration/analysis.py",
            "quantification/provenance/sample_exploration/exports.py",
            "quantification/provenance/sample_exploration/models.py",
            "quantification/provenance/sample_exploration/rendering.py",
            "quantification/provenance/sample_exploration/sample_space.py",
            "quantification/provenance/sample_exploration/sample_topology.py",
            "quantification/provenance/value_provenance.py",
        ),
        release_blocker="Core cannot ship if quantitative outputs stop carrying design and QC meaning that downstream packages depend on.",
    ),
    CoreDomainFamilyEntry(
        family=CoreScientificDomainFamily.PTM_AND_DIA,
        owned_surface="PTM localization, occupancy, motif-enrichment background semantics, protein-abundance-corrected site differential semantics, and DIA-native evidence surfaces that preserve uncertainty, library identity, and targeted follow-up meaning.",
        required_modules=(
            "targeted/assay_interference/analysis.py",
            "targeted/assay_qc/analysis.py",
            "targeted/biomarker_stability/analysis.py",
            "targeted/carryover.py",
            "targeted/discovery_peptide_selection.py",
            "targeted/fragment_ratios.py",
            "targeted/panel_design.py",
            "targeted/panel_redundancy.py",
            "targeted/result_validation.py",
            "targeted/validation_planning/analysis.py",
            "targeted/validation_evidence_cards.py",
            "targeted/transition_coelution.py",
            "targeted/transition_selection.py",
            "ptm/contracts.py",
            "ptm/parsing/__init__.py",
            "ptm/parsing/peptide_parser.py",
            "ptm/parsing/site_annotation_import.py",
            "ptm/localization/__init__.py",
            "ptm/localization/fragment_scoring.py",
            "ptm/localization/localization_risk.py",
            "ptm/localization/localization_scoring.py",
            "ptm/sites/__init__.py",
            "ptm/sites/ambiguity_handling.py",
            "ptm/sites/context_annotation.py",
            "ptm/sites/ortholog_site_conservation.py",
            "ptm/sites/protein_site_mapping.py",
            "ptm/sites/site_groups.py",
            "ptm/quant/__init__.py",
            "ptm/quant/abundance_correction.py",
            "ptm/quant/acetylation.py",
            "ptm/quant/differential_analysis.py",
            "ptm/quant/occupancy_estimation.py",
            "ptm/quant/oxidation.py",
            "ptm/quant/site_quantification.py",
            "ptm/regulation/__init__.py",
            "ptm/regulation/crosstalk.py",
            "ptm/regulation/hotspots.py",
            "ptm/regulation/kinase_inference.py",
            "ptm/regulation/mechanism_classification.py",
            "ptm/regulation/motif_analysis.py",
            "ptm/regulation/phosphatase_inference.py",
            "ptm/regulation/regulator_enrichment.py",
            "ptm/cards/__init__.py",
            "ptm/cards/benchmarks.py",
            "ptm/cards/evidence_cards/report_building.py",
            "ptm/cards/proteoforms.py",
            "ptm/cards/reporting.py",
            "ptm/cards/review.py",
            "proteoforms/assembly.py",
            "proteoforms/quantification.py",
            "dia/contracts.py",
            "dia/library_coverage.py",
            "dia/precursor_matrix.py",
            "dia/protein_matrix.py",
            "dia/run_qc.py",
            "dia/transition_qc.py",
            "targeted/result_import.py",
            "targeted/target_matrix.py",
        ),
        release_blocker="Core cannot ship if PTM or DIA workflows flatten ambiguity into generic evidence records.",
    ),
    CoreDomainFamilyEntry(
        family=CoreScientificDomainFamily.REVIEW_AND_HANDOFF,
        owned_surface="Typed proteomics evidence graphs, evidence-chain reconstruction, review packets, contradiction-aware evidence summaries, collaboration bundles, and core-owned handoff-ready scientific artifacts.",
        required_modules=(
            "review/evidence_graph/__init__.py",
            "review/evidence_graph/evidence_graph.py",
            "review/evidence_graph/evidence_graph_confidence.py",
            "review/evidence_graph/evidence_graph_contradictions.py",
            "review/evidence_graph/evidence_graph_downgrades.py",
            "review/evidence_graph/evidence_graph_export.py",
            "review/evidence_graph/evidence_graph_queries.py",
            "review/evidence_graph/evidence_graph_run_diff.py",
            "review/evidence_graph/evidence_chain_reconstruction.py",
            "review/claims/__init__.py",
            "review/claims/analysis_recommendations.py",
            "review/claims/biological_claim_validation.py",
            "review/claims/biological_hypotheses.py",
            "review/claims/result_queries.py",
            "review/cards/__init__.py",
            "review/cards/collaboration.py",
            "review/cards/compact_result_summary.py",
            "review/cards/inference_packets.py",
            "review/cards/protein_family_graphs.py",
            "review/belief/__init__.py",
            "review/belief/belief_audit.py",
            "review/belief/biomarker_candidate_ranking.py",
            "review/belief/contracts.py",
            "review/belief/evidence_aware_ranking.py",
            "review/belief/flagship_kernel.py",
            "review/explanations/__init__.py",
            "review/explanations/failure_explanations.py",
            "review/explanations/result_explanations.py",
            "review/explanations/scientific_conflicts.py",
            "review/explanations/scientific_failure_atlas.py",
            "review/explanations/scientific_story.py",
            "review/explanations/volcano_plots.py",
            "review/structure_reports/render.py",
            "interpretation/public_api.py",
            "interpretation/annotation_packs.py",
            "interpretation/biological_context_mapping.py",
            "interpretation/compartment_biology.py",
            "interpretation/complex_activity/__init__.py",
            "interpretation/complex_activity/analysis.py",
            "interpretation/complex_activity/member_resolution.py",
            "interpretation/complex_activity/models.py",
            "interpretation/complex_activity/rendering.py",
            "interpretation/complex_activity/score_calculation.py",
            "interpretation/drug_target_interpretation.py",
            "interpretation/disease_phenotype_interpretation.py",
            "interpretation/foreground_background_model.py",
            "interpretation/pathway_activity/__init__.py",
            "interpretation/pathway_activity/analysis.py",
            "interpretation/pathway_activity/knowledge_coverage.py",
            "interpretation/pathway_activity/member_resolution.py",
            "interpretation/pathway_activity/models.py",
            "interpretation/pathway_activity/rendering.py",
            "interpretation/pathway_activity/score_calculation.py",
            "interpretation/protein_set_enrichment.py",
            "interpretation/protein_set_scoring/__init__.py",
            "interpretation/protein_set_scoring/analysis.py",
            "interpretation/protein_set_scoring/definition_import.py",
            "interpretation/protein_set_scoring/models.py",
            "interpretation/protein_set_scoring/rendering.py",
            "interpretation/protein_set_scoring/score_calculation.py",
            "interpretation/ppi_network_modules/__init__.py",
            "interpretation/ppi_network_modules/analysis.py",
            "interpretation/ppi_network_modules/edge_import.py",
            "interpretation/ppi_network_modules/models.py",
            "interpretation/ppi_network_modules/rendering.py",
            "interpretation/regulator_inference/__init__.py",
            "interpretation/regulator_inference/_table_io.py",
            "interpretation/regulator_inference/evidence_import.py",
            "interpretation/regulator_inference/inference.py",
            "interpretation/regulator_inference/models.py",
            "interpretation/regulator_inference/rendering.py",
            "interpretation/regulator_inference/site_signal_input.py",
            "interpretation/tissue_cell_type_context.py",
            "panels/target_panel.py",
        ),
        release_blocker="Core cannot ship if review-facing scientific artifacts become presentation-only shells without underlying evidence structure.",
    ),
    CoreDomainFamilyEntry(
        family=CoreScientificDomainFamily.WORKFLOW_CONTRACTS,
        owned_surface="Runtime-agnostic workflow blueprints, execution requests, and replayable scientific workflow contracts.",
        required_modules=(
            "workflow/blueprint.py",
            "workflow/cards/__init__.py",
            "workflow/cards/cross_study_evidence_cards.py",
            "workflow/cards/protein_evidence_cards.py",
            "workflow/cards/protein_mechanism_cards.py",
            "workflow/demo/__init__.py",
            "workflow/demo/surprising_demo.py",
            "workflow/demo/surprising_demo_interrogation.py",
            "workflow/exports/__init__.py",
            "workflow/exports/artifact_layout.py",
            "workflow/exports/interactive_result_bundle.py",
            "workflow/exports/interactive_result_comparison.py",
            "workflow/exports/result_archive.py",
            "workflow/exports/result_manifest.py",
            "workflow/exports/result_search_index.py",
            "workflow/pipelines/advanced_diann.py",
            "workflow/pipelines/advanced_fragpipe.py",
            "workflow/pipelines/advanced_maxquant.py",
            "workflow/pipelines/advanced_ptm.py",
            "workflow/pipelines/advanced_targeted.py",
            "workflow/pipelines/advanced_tmt.py",
            "workflow/pipelines/dda_biological_workflow.py",
            "workflow/pipelines/diann_biological_workflow.py",
            "workflow/pipelines/dia_dda_comparison.py",
            "workflow/pipelines/dia_differential_analysis.py",
            "workflow/cohort_stratification.py",
            "workflow/cross_study_effect_comparison.py",
            "workflow/cross_study_meta_analysis.py",
            "workflow/cross_study_pathway_comparison.py",
            "workflow/cross_study_protein_harmonization.py",
            "workflow/cross_species_effect_comparison.py",
            "workflow/pipelines/discovery_to_assay.py",
            "workflow/pipelines/label_based_differential/__init__.py",
            "workflow/pipelines/label_based_differential/analysis.py",
            "workflow/pipelines/label_based_differential/inputs.py",
            "workflow/pipelines/label_based_differential/models.py",
            "workflow/pipelines/label_based_differential/normalization.py",
            "workflow/pipelines/label_based_differential/rendering.py",
            "workflow/pipelines/label_based_differential/statistics.py",
            "workflow/pipelines/label_based_reporting.py",
            "workflow/cards/mechanisms.py",
            "workflow/pipelines/maxquant_biological_workflow.py",
            "workflow/pipelines/multi_study.py",
            "workflow/pipelines/operations/orchestrator.py",
            "workflow/pipelines/ptm_site_workflow.py",
            "workflow/benchmarks/__init__.py",
            "workflow/benchmarks/public_benchmark_descriptors.py",
            "workflow/benchmarks/public_benchmark_subset.py",
            "workflow/pipelines/public_benchmark_runner.py",
            "workflow/public_dataset_comparison.py",
            "workflow/exports/targeted_review_workflow.py",
            "workflow/pipelines/tmt_experiment_workflow.py",
            "workflow/reports/__init__.py",
            "workflow/reports/biological_reporting.py",
            "workflow/reports/biological_report_assembly.py",
            "workflow/reports/biological_report_claims.py",
            "workflow/reports/biological_report_html.py",
            "workflow/reports/biological_report_html_support.py",
            "workflow/reports/biological_report_models.py",
            "workflow/reports/biological_report_ranking.py",
            "workflow/reports/biological_report_rendering.py",
            "workflow/reports/biological_report_section_confidence.py",
            "workflow/reports/biological_report_selection.py",
            "workflow/reports/biological_result_graph.py",
            "workflow/result_types.py",
            "workflow/study_result.py",
            "workflow/pipelines/integrated_scientific_report.py",
            "workflow/benchmarks/synthetic_quant_truth.py",
            "workflow/pipelines/trust_bundle.py",
            "workflow/weak_evidence.py",
            "workflow/pipelines/weak_evidence.py",
            "interfaces/execution/backend.py",
            "interfaces/execution/runner.py",
            "interfaces/execution/runtime_adapter.py",
            "interfaces/runtime_plans.py",
        ),
        release_blocker="Core cannot ship if workflow contracts require runtime internals instead of scientific inputs and explicit adapters.",
    ),
    CoreDomainFamilyEntry(
        family=CoreScientificDomainFamily.PACKAGE_SURFACE,
        owned_surface="Package-level CLI, example surfaces, and adoption contracts that explain and expose core ownership without becoming a shadow runtime.",
        required_modules=(
            "__init__.py",
            "programs.py",
            "interfaces/examples.py",
            "interfaces/support/__init__.py",
            "interfaces/python_api/__init__.py",
            "interfaces/cli/app.py",
            "governance/charter.py",
            "benchmarks/adoption.py",
            "benchmarks/scientific_fixture_corpus.py",
            "benchmarks/weak_evidence.py",
        ),
        release_blocker="Core cannot ship if its public package surface describes the wrong owner story or hides the scientific boundary behind stale compatibility language.",
    ),
)


_COMPATIBILITY_IMPORT_RE = re.compile(
    r"^from\s+(bijux_proteomics(?:\.[a-z0-9_]+)+)\s+import\s+\*(?:\s+#.*)?$",
    flags=re.MULTILINE,
)
_EXPLICIT_COMPATIBILITY_EXPORT_PATHS: frozenset[str] = frozenset()


def _core_source_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve_module_path(module_name: str) -> str:
    relative = module_name.removeprefix("bijux_proteomics.").replace(".", "/")
    source_root = _core_source_root()
    candidate = source_root / f"{relative}.py"
    if candidate.exists():
        return f"{relative}.py"
    package_init = source_root / relative / "__init__.py"
    if package_init.exists():
        return f"{relative}/__init__.py"
    raise ValueError(f"unable to resolve compatibility target for {module_name}")


def _pure_reexport_targets(module_path: str) -> tuple[str, ...]:
    content = (_core_source_root() / module_path).read_text(encoding="utf-8")
    tree = ast.parse(content, filename=module_path)
    targets: list[str] = []
    for node in tree.body:
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            continue
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            continue
        if (
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.startswith("bijux_proteomics.")
            and all(alias.name == "*" for alias in node.names)
        ):
            targets.append(node.module)
            continue
        return ()
    return tuple(targets)


def _compatibility_target(module_path: str) -> str | None:
    if module_path not in _EXPLICIT_COMPATIBILITY_EXPORT_PATHS:
        return None
    content = (_core_source_root() / module_path).read_text(encoding="utf-8")
    match = _COMPATIBILITY_IMPORT_RE.search(content)
    if match is None:
        return None
    return _resolve_module_path(match.group(1))


def _module_family(module_path: str) -> CoreScientificDomainFamily:
    compatibility_target = _compatibility_target(module_path)
    if compatibility_target is not None:
        return _module_family(compatibility_target)
    pure_reexport_targets = _pure_reexport_targets(module_path)
    if pure_reexport_targets:
        target_path = _resolve_module_path(pure_reexport_targets[0])
        if target_path != module_path:
            return _module_family(target_path)

    if module_path.startswith(
        ("workflow/", "interfaces/execution/")
    ) or module_path in {"interfaces/runtime_plans.py"}:
        return CoreScientificDomainFamily.WORKFLOW_CONTRACTS
    if module_path in {"programs.py", "public_api.py"}:
        return CoreScientificDomainFamily.PACKAGE_SURFACE
    if module_path == "__init__.py" or module_path.startswith(
        ("governance/", "interfaces/", "benchmarks/")
    ):
        return CoreScientificDomainFamily.PACKAGE_SURFACE
    if module_path.startswith("domain/"):
        return CoreScientificDomainFamily.PROGRAM_GOVERNANCE
    if module_path.startswith(("sequences/", "chemistry/")) or module_path in {
        "peptide_uniqueness_audit.py",
        "protease_digest_comparison.py",
    }:
        return CoreScientificDomainFamily.SEQUENCE_AND_CHEMISTRY
    if module_path in {
        "_atomic_files.py",
        "_output_tables.py",
        "_tabular.py",
        "_scientific_tables.py",
        "tabular.py",
        "scientific_tables.py",
    } or module_path.startswith(("io/", "identification/")):
        return CoreScientificDomainFamily.INGESTION_AND_IDENTIFICATION
    if module_path.startswith(
        (
            "quantification/",
            "study/",
            "lab/",
            "multiplex/",
            "isotope_labeling/",
            "targeted/",
        )
    ):
        return CoreScientificDomainFamily.QUANTIFICATION_AND_STUDY
    if module_path.startswith(("ptm/", "dia/", "proteoforms/")):
        return CoreScientificDomainFamily.PTM_AND_DIA
    if module_path.startswith(
        (
            "review/",
            "biology/",
            "interpretation/",
            "panels/",
        )
    ):
        return CoreScientificDomainFamily.REVIEW_AND_HANDOFF
    raise ValueError(f"unclassified core module path: {module_path}")


def _module_classification(module_path: str) -> CoreModuleClassification:
    if module_path == "governance/charter.py":
        return CoreModuleClassification.BOUNDARY_GOVERNANCE
    if module_path == "__init__.py" or module_path.endswith("/__init__.py"):
        return CoreModuleClassification.THIN_ABSTRACTION
    if _compatibility_target(module_path) is not None:
        return CoreModuleClassification.COMPATIBILITY_EXPORT
    if _pure_reexport_targets(module_path):
        return CoreModuleClassification.THIN_ABSTRACTION
    return CoreModuleClassification.SUBSTANTIVE_SCIENTIFIC_SURFACE


def _module_reason(
    module_path: str,
    family: CoreScientificDomainFamily,
    classification: CoreModuleClassification,
) -> str:
    if classification is CoreModuleClassification.BOUNDARY_GOVERNANCE:
        return (
            "The machine-readable charter keeps core scientific ownership explicit, "
            "auditable, and release-blocking."
        )
    if classification is CoreModuleClassification.THIN_ABSTRACTION:
        return (
            "Namespace initializers and curated in-tree re-export facades aggregate "
            "stable owned exports without becoming separate scientific owners."
        )
    if classification is CoreModuleClassification.COMPATIBILITY_EXPORT:
        target = _compatibility_target(module_path)
        if target is None:
            raise ValueError(f"missing compatibility target for {module_path}")
        return (
            f"This module is a compatibility export over {target} and must stay a thin "
            "alias rather than growing new scientific logic."
        )
    return {
        CoreScientificDomainFamily.PROGRAM_GOVERNANCE: (
            "This module owns scientific program-state semantics that downstream packages consume."
        ),
        CoreScientificDomainFamily.SEQUENCE_AND_CHEMISTRY: (
            "This module owns sequence and peptide semantics that must stay scientifically precise."
        ),
        CoreScientificDomainFamily.INGESTION_AND_IDENTIFICATION: (
            "This module owns evidence ingestion, support boundaries, or identification semantics."
        ),
        CoreScientificDomainFamily.QUANTIFICATION_AND_STUDY: (
            "This module owns quantitative analysis or study-design meaning instead of workflow transport."
        ),
        CoreScientificDomainFamily.PTM_AND_DIA: (
            "This module owns uncertainty-aware PTM or DIA evidence semantics."
        ),
        CoreScientificDomainFamily.REVIEW_AND_HANDOFF: (
            "This module owns reviewable scientific artifacts and evidence-aware handoff context."
        ),
        CoreScientificDomainFamily.WORKFLOW_CONTRACTS: (
            "This module owns runtime-agnostic scientific workflow contracts or explicit execution adapters."
        ),
        CoreScientificDomainFamily.PACKAGE_SURFACE: (
            "This module owns a package-facing surface that explains or exposes core without taking over runtime authority."
        ),
    }[family]


def _build_module_audit() -> tuple[CoreModuleAuditEntry, ...]:
    source_root = _core_source_root()
    entries: list[CoreModuleAuditEntry] = []
    for path in sorted(source_root.rglob("*.py")):
        module_path = path.relative_to(source_root).as_posix()
        family = _module_family(module_path)
        classification = _module_classification(module_path)
        entries.append(
            CoreModuleAuditEntry(
                module_path=module_path,
                family=family,
                classification=classification,
                reason=_module_reason(module_path, family, classification),
            )
        )
    return tuple(entries)


DEFAULT_CORE_MODULE_AUDIT = _build_module_audit()


def list_core_domain_families() -> tuple[CoreScientificDomainFamily, ...]:
    """Return the exact scientific domain families core is allowed to own."""

    return DEFAULT_CORE_CHARTER.domain_families


def list_core_domain_entries() -> tuple[CoreDomainFamilyEntry, ...]:
    """Return the exact domain-family entries core must satisfy."""

    return DEFAULT_CORE_DOMAIN_ENTRIES


__all__ = [
    "CoreDomainFamilyEntry",
    "CoreModuleAuditEntry",
    "CoreModuleClassification",
    "CoreProductCharter",
    "CoreScientificDomainFamily",
    "DEFAULT_CORE_CHARTER",
    "DEFAULT_CORE_DOMAIN_ENTRIES",
    "DEFAULT_CORE_MODULE_AUDIT",
    "list_core_domain_entries",
    "list_core_domain_families",
]
