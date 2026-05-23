# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""CLI for Bijux Proteomics domain and FASTA operations."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import time
from typing import Any

import click

from bijux_proteomics.chemistry import (
    FragmentIonSeries,
    IsotopicLabelingPolicy,
    ModificationRegistryDocument,
    SearchEngineModifiedPeptideDialect,
    StaticModification,
    VariableModification,
    approximate_peptide_isotope_envelope,
    build_peptide_elemental_composition,
    build_fragment_ion_review_report,
    build_modification_localization_advisory,
    build_modification_resolution_report,
    build_modified_peptide,
    build_peptide_charge_state,
    build_search_engine_modified_peptide_report,
    calculate_fragment_ions,
    canonicalize_modified_peptide,
    get_modification,
    load_modification_registry,
    predict_peptide_isotope_envelopes,
    render_isotope_envelopes_tsv,
    render_fragment_ion_report_tsv,
)
from bijux_proteomics.benchmarks import (
    build_lfq_cohort_biological_case_study_report,
    export_public_biological_case_study_report,
    render_public_biological_case_study_summary_tsv,
)
from bijux_proteomics.domain.errors import (
    ProteomicsOperatorError,
    ProteomicsOperatorErrorCode,
)
from bijux_proteomics.domain.program_spec import (
    ProgramSpec,
    create_program_spec,
    program_summary,
)
from bijux_proteomics.identification import (
    FdrPolicy,
    ParsimonyVariant,
    PsmRecord,
    SearchResultColumnMapping,
    TargetDecoyLabelPolicy,
    TargetDecoyReferenceCase,
    apply_q_values,
    assign_confidence_labels,
    assign_razor_peptides,
    build_calibration_plot_data,
    build_comet_import_report,
    build_contaminant_peptide_match_report,
    build_contaminant_evidence_report,
    build_core_protein_inference_benchmark_suite,
    build_diann_import_report,
    build_evidence_level_fdr_review_report,
    build_fdr_audit_trail,
    build_fragpipe_import_benchmark_report,
    build_fragpipe_import_report,
    build_generic_psm_mapper_report,
    build_maxquant_import_report,
    build_openms_import_report,
    build_parsimony_review_report,
    build_peptide_evidence_review_report,
    build_protein_evidence_review_report,
    build_peptide_summary_report,
    build_peptide_uniqueness_across_database,
    build_picked_protein_fdr_review_report,
    build_protein_ambiguity_review_report,
    build_protein_coverage_map,
    build_protein_coverage_plot_report,
    build_protein_coverage_review_report,
    build_protein_grouping_review_report,
    build_protein_groups,
    build_protein_summary_report,
    build_psm_evidence_inspection_report,
    build_psm_summary_report,
    build_sage_import_report,
    build_search_result_provenance_manifest,
    build_spectronaut_import_report,
    build_target_decoy_reference_validation_report,
    calculate_grouped_fdr,
    calculate_level_specific_fdr,
    calculate_picked_protein_fdr,
    export_psm_jsonl,
    export_psm_tsv,
    filter_psms_by_fdr,
    infer_proteins_by_parsimony,
    parse_psm_tsv,
    render_comet_canonical_psm_tsv,
    render_comet_psm_tsv,
    render_comet_summary_tsv,
    render_contaminant_burden_tsv,
    render_contaminant_proteins_tsv,
    render_diann_precursor_tsv,
    render_diann_protein_group_tsv,
    render_diann_summary_tsv,
    render_evidence_level_fdr_entries_tsv,
    render_evidence_level_fdr_summary_tsv,
    render_fragpipe_benchmark_summary_tsv,
    render_fragpipe_canonical_psm_tsv,
    render_fragpipe_count_comparisons_tsv,
    render_fragpipe_open_search_evidence_tsv,
    render_fragpipe_peptide_tsv,
    render_fragpipe_protein_quantity_tsv,
    render_fragpipe_protein_group_comparison_tsv,
    render_fragpipe_protein_tsv,
    render_fragpipe_psm_tsv,
    render_fragpipe_q_value_comparison_tsv,
    render_fragpipe_summary_tsv,
    render_generic_psm_mapper_tsv,
    render_maxquant_evidence_tsv,
    render_maxquant_lfq_candidate_tsv,
    render_maxquant_peptide_tsv,
    render_maxquant_protein_group_tsv,
    render_maxquant_summary_tsv,
    render_openms_feature_tsv,
    render_openms_protein_tsv,
    render_openms_psm_tsv,
    render_openms_summary_tsv,
    render_parsimony_review_ambiguities_tsv,
    render_parsimony_review_proteins_tsv,
    render_parsimony_review_summary_tsv,
    render_peptide_evidence_entries_tsv,
    render_peptide_evidence_summary_tsv,
    render_protein_evidence_entries_tsv,
    render_protein_evidence_summary_tsv,
    render_picked_protein_fdr_entries_tsv,
    render_picked_protein_fdr_summary_tsv,
    render_protein_ambiguity_entries_tsv,
    render_protein_ambiguity_summary_tsv,
    render_protein_coverage_entries_tsv,
    render_protein_coverage_plot_html,
    render_protein_coverage_plot_positions_tsv,
    render_protein_coverage_plot_svg,
    render_protein_coverage_regions_tsv,
    render_protein_coverage_summary_tsv,
    render_protein_grouping_entries_tsv,
    render_protein_grouping_summary_tsv,
    render_protein_inference_benchmark_assessments_tsv,
    render_protein_inference_benchmark_scenarios_tsv,
    render_protein_inference_benchmark_summary_tsv,
    render_psm_evidence_inspection_summary_tsv,
    render_psm_inspection_distribution_tsv,
    render_sage_canonical_psm_tsv,
    render_sage_psm_tsv,
    render_sage_summary_tsv,
    render_spectronaut_precursor_quantity_tsv,
    render_spectronaut_precursor_tsv,
    render_spectronaut_protein_group_quantity_tsv,
    render_spectronaut_protein_group_tsv,
    render_spectronaut_summary_tsv,
    render_target_decoy_reference_entries_tsv,
    render_target_decoy_reference_summary_tsv,
)
from bijux_proteomics.identification.rejected_evidence_table import (
    render_rejected_evidence_tsv,
)
from bijux_proteomics.identification.cross_run_reproducibility import (
    RunDetectionContext,
    build_peptide_cross_run_reproducibility_report,
    build_protein_cross_run_reproducibility_report,
    render_cross_run_reproducibility_entries_tsv,
    render_cross_run_reproducibility_summary_tsv,
)
from bijux_proteomics.identification.error_rate_annotation import (
    annotate_psm_error_rates,
    build_psm_error_rate_annotation_report,
    render_psm_error_rate_annotation_summary_tsv,
    render_psm_error_rate_annotation_tsv,
)
from bijux_proteomics.identification.psm_target_decoy_fdr import (
    build_psm_target_decoy_fdr_report,
    render_psm_target_decoy_fdr_summary_tsv,
    render_psm_target_decoy_fdr_tsv,
)
from bijux_proteomics.identification.protein_coverage import (
    render_protein_coverage_peptide_coordinates_tsv,
    render_protein_coverage_uncovered_regions_tsv,
)
from bijux_proteomics.identification.score_separation_diagnostic import (
    build_score_separation_diagnostic_report,
    render_score_separation_bins_tsv,
    render_score_separation_summary_tsv,
)
from bijux_proteomics.identification.search_adapters import (
    ScoreOrientation,
    SearchAdapterKind,
    build_search_adapter_capability_matrix,
    build_search_adapter_conformance_report,
    build_search_adapter_provenance_manifest,
    compare_search_result_reports,
    get_search_adapter_manifest,
    normalize_search_results_with_adapter,
    parse_search_parameter_file,
    validate_search_parameters,
)
from bijux_proteomics.dia import (
    DiaPrecursorMatrixPolicy,
    DiaPrecursorQValueFilterTiming,
    DiaPeptideRollupMethod,
    DiaProteinMatrixTargetKind,
    DiaProteinRollupMethod,
    DiaSharedPeptidePolicy,
    build_transition_qc_report_from_table,
    build_dia_protein_matrix_report,
    build_diann_library_coverage_report,
    build_diann_peptide_matrix_report,
    build_diann_precursor_matrix_report,
    build_spectronaut_peptide_matrix_report,
    build_spectronaut_protein_matrix_report,
    build_diann_run_qc_report,
    build_spectronaut_precursor_matrix_report,
    render_dia_library_coverage_condition_tsv,
    render_dia_library_coverage_observed_outside_peptide_tsv,
    render_dia_library_coverage_observed_outside_protein_tsv,
    render_dia_library_coverage_peptide_tsv,
    render_dia_library_coverage_protein_tsv,
    render_dia_library_coverage_sample_tsv,
    render_dia_library_coverage_summary_tsv,
    render_dia_peptide_quantity_matrix_tsv,
    render_dia_protein_rollup_evidence_tsv,
    render_dia_run_qc_correlation_tsv,
    render_dia_run_qc_intensity_distribution_tsv,
    render_dia_run_qc_outlier_tsv,
    render_dia_run_qc_run_table_tsv,
    render_dia_run_qc_summary_tsv,
    render_dia_protein_matrix_summary_tsv,
    render_dia_protein_quantity_matrix_tsv,
    render_dia_precursor_matrix_summary_tsv,
    render_dia_precursor_metadata_tsv,
    render_dia_precursor_q_value_matrix_tsv,
    render_dia_precursor_quantity_matrix_tsv,
    render_transition_qc_sample_tsv,
    render_transition_qc_summary_tsv,
    render_transition_qc_transition_tsv,
    render_transition_qc_weak_tsv,
)
from bijux_proteomics.interfaces.runtime_plans import (
    WorkflowSchedulerKind,
    build_proteomics_workflow_runtime_bundle,
    build_workflow_runtime_validation_report,
)
from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    FormatConversionTarget,
    ProteomicsFormatKind,
    build_mzml_collection_summary,
    build_normalized_run_bundle,
    convert_proteomics_format,
    export_spectra_jsonl,
    extract_mzml_chromatograms,
    parse_experimental_design_table,
    parse_mzml,
    validate_proteomics_input,
)
from bijux_proteomics.io.ingestion import (
    build_mzml_practical_review_report,
    build_streaming_parse_profile,
)
from bijux_proteomics.io.run_qc import (
    build_spectrum_run_qc_plot_payload,
    build_spectrum_run_qc_report,
    render_spectrum_run_qc_distribution_tsv,
    render_spectrum_run_qc_flagged_spectra_tsv,
    render_spectrum_run_qc_spectra_tsv,
    render_spectrum_run_qc_summary_tsv,
    render_spectrum_run_qc_time_bins_tsv,
    render_spectrum_run_qc_trace_tsv,
)
from bijux_proteomics.io.spectra import (
    PrecursorMassErrorQuery,
    SpectralSimilarityMethod,
    SpectrumModel,
    SpectrumSimilarityMode,
    annotate_spectrum_fragments,
    build_precursor_mass_error_report,
    build_spectrum_collection_summary,
    build_spectrum_library_similarity_report,
    build_spectrum_metrics,
    build_spectrum_plot_payload,
    build_spectrum_provenance_manifest,
    build_spectrum_similarity_comparison_report,
    build_spectrum_summary_table_report,
    parse_mgf,
    render_precursor_mass_error_distribution_tsv,
    render_precursor_mass_error_observations_tsv,
    render_precursor_mass_error_summary_tsv,
    render_spectrum_distribution_tsv,
    render_spectrum_similarity_tsv,
    render_spectrum_summary_tsv,
)
from bijux_proteomics.io.spectrum_peak_matching import (
    build_spectrum_peak_match_report,
    export_spectrum_peak_match_tsv,
    export_spectrum_unmatched_peak_tsv,
)
from bijux_proteomics.io.spectral_library import (
    build_spectral_library_index,
    build_spectral_library_summary,
    find_spectral_library_candidates,
    import_spectral_library,
    render_spectral_library_candidates_tsv,
    render_spectral_library_search_tsv,
    render_spectral_library_summary_tsv,
    search_spectral_library,
)
from bijux_proteomics.panels import (
    TargetPanelSourceKind,
    build_diann_peptide_target_panel_report,
    build_diann_protein_target_panel_report,
    build_lfq_peptide_target_panel_report,
    build_lfq_protein_lfq_target_panel_report,
    build_lfq_protein_target_panel_report,
    render_target_panel_intensity_tsv,
    render_target_panel_matrix_tsv,
    render_target_panel_missing_tsv,
    render_target_panel_summary_tsv,
    render_target_panel_target_tsv,
)
from bijux_proteomics.interpretation import (
    BiologicalContextColumnMapping,
    BiologicalContextKind,
    ComplexEnrichmentCorrectionPolicy,
    ComplexMembershipColumnMapping,
    GoAnnotationColumnMapping,
    GoEnrichmentCorrectionPolicy,
    OrthologColumnMapping,
    PathwayEnrichmentCorrectionPolicy,
    PathwayMembershipColumnMapping,
    PpiEdgeColumnMapping,
    ProteinSetColumnMapping,
    ProteinSetScoringPolicy,
    ProteinSetEnrichmentMissingBackgroundPolicy,
    ProteinSetEnrichmentPolicy,
    apply_complex_enrichment_multiple_testing,
    apply_go_enrichment_multiple_testing,
    apply_pathway_enrichment_multiple_testing,
    build_biological_context_mapping_report,
    build_ppi_network_module_report,
    build_complex_enrichment_report,
    build_go_enrichment_report,
    build_ortholog_mapping_report,
    build_pathway_enrichment_report,
    build_protein_set_enrichment_report,
    build_protein_set_scoring_report,
    ProteinAnnotationColumnMapping,
    ProteinReferenceColumnMapping,
    build_protein_annotation_mapping_report,
    parse_biological_context_table,
    parse_complex_membership_table,
    parse_go_annotation_table,
    parse_ortholog_table,
    parse_pathway_membership_table,
    parse_ppi_edge_table,
    parse_protein_annotation_table,
    parse_protein_reference_table,
    parse_protein_set_table,
    render_complex_enrichment_entry_tsv,
    render_complex_enrichment_summary_tsv,
    render_complex_unresolved_member_tsv,
    render_biological_context_mapping_summary_tsv,
    render_biological_context_mapping_tsv,
    render_biological_context_term_tsv,
    render_go_enrichment_summary_tsv,
    render_go_enrichment_term_tsv,
    render_go_enrichment_unannotated_tsv,
    render_mapped_ortholog_tsv,
    render_ortholog_mapping_summary_tsv,
    render_pathway_enrichment_entry_tsv,
    render_pathway_enrichment_summary_tsv,
    render_pathway_unresolved_member_tsv,
    render_ppi_isolated_protein_tsv,
    render_ppi_module_enrichment_tsv,
    render_ppi_module_tsv,
    render_ppi_network_edge_tsv,
    render_ppi_network_module_summary_tsv,
    render_protein_set_enrichment_summary_tsv,
    render_protein_set_enrichment_tsv,
    render_protein_annotation_tsv,
    render_protein_annotation_summary_tsv,
    render_protein_set_universe_gap_tsv,
    render_protein_set_condition_comparison_tsv,
    render_protein_set_condition_score_tsv,
    render_protein_set_sample_score_tsv,
    render_protein_set_score_matrix_tsv,
    render_protein_set_scoring_summary_tsv,
    render_rejected_protein_set_membership_tsv,
    render_protein_set_unresolved_member_tsv,
    render_rejected_complex_membership_tsv,
    render_rejected_pathway_membership_tsv,
    render_rejected_go_annotation_tsv,
    render_rejected_ortholog_tsv,
    render_rejected_ppi_edge_tsv,
    render_rejected_protein_annotation_tsv,
    render_rejected_protein_set_tsv,
    render_rejected_protein_reference_tsv,
    render_rejected_biological_context_tsv,
    render_unmapped_ortholog_tsv,
    render_unmapped_biological_context_tsv,
    render_unmapped_protein_annotation_tsv,
)
from bijux_proteomics.multiplex import (
    TmtInterferencePolicy,
    TmtNormalizationMethod,
    TmtNormalizationPolicy,
    TmtPlexIntegrationPolicy,
    TmtReporterChannelColumn,
    TmtReporterColumnMapping,
    TmtSearchResultSourceKind,
    build_tmt_interference_report,
    build_tmt_normalization_report,
    build_tmt_plex_integration_report,
    build_tmt_ratio_report,
    build_tmt_reporter_feature_bundle,
    build_tmt_reporter_matrix_report,
    build_multiplex_metadata_validation_report,
    export_multiplex_channel_assignment_tsv,
    export_multiplex_duplicate_assignment_tsv,
    export_multiplex_metadata_summary_tsv,
    export_multiplex_missing_condition_tsv,
    export_tmt_filtered_interference_tsv,
    export_tmt_channel_distribution_tsv,
    export_tmt_channel_mapping_tsv,
    export_tmt_channel_totals_tsv,
    export_tmt_interference_channel_summary_tsv,
    export_tmt_interference_observation_tsv,
    export_tmt_interference_summary_tsv,
    export_tmt_normalization_summary_tsv,
    export_tmt_normalization_transform_tsv,
    export_tmt_normalized_peptide_matrix_tsv,
    export_tmt_normalized_protein_matrix_tsv,
    export_tmt_integrated_protein_matrix_tsv,
    export_tmt_peptide_ratio_tsv,
    export_tmt_peptide_matrix_tsv,
    export_tmt_plex_alignment_tsv,
    export_tmt_plex_effect_tsv,
    export_tmt_plex_integration_summary_tsv,
    export_tmt_protein_ratio_tsv,
    export_tmt_protein_matrix_tsv,
    export_tmt_report_summary_tsv,
    export_tmt_ratio_summary_tsv,
    parse_tmt_reporter_table,
)
from bijux_proteomics.isotope_labeling import (
    SilacColumnMapping,
    SilacLabel,
    SilacQuantificationPolicy,
    SilacValidationPolicy,
    TmtValidationPolicy,
    build_silac_ratio_report,
    build_silac_validation_report,
    build_tmt_validation_report,
    export_silac_validation_distribution_tsv,
    export_silac_validation_label_tsv,
    export_silac_peptide_ratio_tsv,
    export_silac_protein_ratio_tsv,
    export_silac_ratio_summary_tsv,
    export_silac_validation_summary_tsv,
    export_silac_validation_weak_tsv,
    export_tmt_validation_channel_tsv,
    export_tmt_validation_distribution_tsv,
    export_tmt_validation_summary_tsv,
    export_tmt_validation_weak_tsv,
    parse_silac_feature_table,
)
from bijux_proteomics.targeted import (
    TargetedResultSourceKind,
    render_targeted_assay_qc_fragment_ratio_tsv,
    render_targeted_assay_qc_replicate_cv_tsv,
    render_targeted_assay_qc_retention_tsv,
    render_targeted_assay_qc_summary_tsv,
    render_targeted_assay_qc_target_tsv,
    render_targeted_assay_qc_transition_tsv,
    render_targeted_assay_qc_transition_qc_tsv,
    render_targeted_assay_qc_unreliable_tsv,
    render_targeted_matrix_excluded_transition_tsv,
    render_targeted_matrix_flagged_tsv,
    render_targeted_matrix_missingness_tsv,
    render_targeted_matrix_retained_transition_tsv,
    render_targeted_matrix_sample_tsv,
    render_targeted_matrix_summary_tsv,
    render_targeted_matrix_target_tsv,
    render_targeted_result_observation_tsv,
)
from bijux_proteomics.ptm import (
    PtmLocalizationColumnMapping,
    PtmMotifComparisonPolicy,
    PtmMotifBackgroundMode,
    PtmMotifRegulationDirection,
    PtmPhosphositeSelectionPolicy,
    PtmRegulatorEnrichmentPolicy,
    PtmProteinCorrectionMode,
    PtmSiteAnnotationColumnMapping,
    PtmSiteContextColumnMapping,
    PtmSiteQuantAmbiguityPolicy,
    PtmPeptideColumnMapping,
    build_ptm_differential_analysis_report,
    build_ptm_enrichment_input,
    build_ptm_phosphosite_motif_enrichment_report,
    build_ptm_ambiguity_review_report,
    build_ptm_site_context_report,
    build_ptm_differential_volcano_plot,
    build_ptm_regulator_enrichment_report,
    build_ptm_site_group_quantification_report,
    build_ptm_site_annotation_biology_summary,
    build_ptm_site_annotation_mapping_report,
    build_ptm_localization_scoring_report,
    build_ptm_occupancy_counterpart_report,
    build_ptm_site_occupancy_report,
    build_ptm_site_quantification_report,
    build_ptm_motif_windows,
    build_ptm_site_coverage_report,
    build_ptm_site_fdr,
    build_ptm_site_table,
    build_ptm_protein_site_mapping_report,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_peptide,
    parse_ptm_peptide_tsv,
    parse_ptm_localization_tsv,
    export_ptm_differential_volcano_tsv,
    export_ptm_mapped_site_annotation_tsv,
    export_ptm_phosphosite_motif_enriched_term_tsv,
    export_ptm_phosphosite_motif_frequency_tsv,
    export_ptm_phosphosite_motif_logo_tsv,
    export_ptm_phosphosite_motif_window_tsv,
    export_ptm_regulator_enrichment_summary_tsv,
    export_ptm_regulator_enrichment_tsv,
    export_ptm_site_annotation_biology_tsv,
    export_ptm_site_annotation_mapping_summary_tsv,
    export_ptm_site_context_summary_tsv,
    export_ptm_site_context_tsv,
    export_ptm_site_differential_tsv,
    export_ptm_site_differential_broken_pairs_tsv,
    export_ptm_unmapped_site_annotation_tsv,
    parse_ptm_site_context_tsv,
    render_ptm_ambiguity_review_summary_tsv,
    render_ptm_coordinate_validation_tsv,
    render_ptm_evidence_site_candidate_tsv,
    render_ptm_localization_scoring_entry_tsv,
    render_ptm_localization_scoring_summary_tsv,
    render_ptm_localized_site_review_tsv,
    render_ptm_occupancy_counterpart_tsv,
    render_ptm_peptide_record_tsv,
    render_ptm_peptide_rejected_tsv,
    render_ptm_peptide_site_tsv,
    render_ptm_site_occupancy_entry_tsv,
    render_ptm_site_occupancy_summary_tsv,
    render_ptm_site_group_quant_matrix_tsv,
    render_ptm_site_group_quant_missingness_tsv,
    render_ptm_site_group_quant_summary_tsv,
    render_ptm_site_quant_excluded_tsv,
    render_ptm_site_quant_matrix_tsv,
    render_ptm_site_quant_missingness_tsv,
    render_ptm_site_quant_summary_tsv,
    render_ptm_peptide_summary_tsv,
    render_ptm_protein_site_mapping_tsv,
    render_ptm_site_coverage_tsv,
    render_ptm_site_table_tsv,
    render_ptm_unmapped_peptide_tsv,
    render_ptm_unlocalized_group_review_tsv,
    validate_ptm_site_coordinates,
    parse_ptm_site_annotation_tsv,
)
from bijux_proteomics.quantification import (
    DifferentialAbundanceTestType,
    HeatmapMissingValuePolicy,
    HeatmapPreparationPolicy,
    ImputationMethod,
    Ms1FeatureColumnMapping,
    NormalizationMethod,
    PeptideMatrixGroupingMode,
    PairedDifferentialPolicy,
    PowerEstimationPolicy,
    PrecursorIntensityColumnMapping,
    ProteinMatrixTargetKind,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
    TimeCourseTestingPolicy,
    build_differential_abundance_report,
    build_batch_effect_estimator_report,
    build_heatmap_preparation_report,
    build_limma_compatible_quant_package,
    build_msstats_compatible_input_report,
    build_quant_design_matrix_report,
    build_statistical_backend_validation_report,
    build_imputation_report,
    build_imputation_sensitivity_report,
    build_label_free_intensity_table,
    build_missingness_classifier_report,
    build_multi_condition_differential_abundance_report,
    build_normalization_comparison_report,
    build_normalization_strategy_comparison_report,
    build_peptide_intensity_matrix_from_features,
    build_peptide_intensity_matrix_from_precursors,
    build_peptide_intensity_matrix_from_psms,
    build_power_estimation_report,
    build_protein_intensity_matrix_from_features,
    build_protein_intensity_matrix_from_psms,
    build_protein_lfq_report_from_features,
    build_protein_lfq_report_from_psms,
    build_replicate_and_batch_qc_report,
    build_sample_exploration_report,
    build_spectral_count_table,
    build_time_course_differential_report,
    export_limma_assay_matrix_tsv,
    export_limma_contrast_matrix_tsv,
    export_limma_design_matrix_tsv,
    export_limma_sample_annotations_tsv,
    export_msstats_compatible_input_tsv,
    export_heatmap_column_metadata_tsv,
    export_differential_abundance_tsv,
    export_differential_broken_pairs_tsv,
    export_batch_effect_batches_tsv,
    export_batch_effect_principal_components_tsv,
    export_batch_effect_summary_tsv,
    export_heatmap_row_metadata_tsv,
    export_heatmap_summary_tsv,
    export_heatmap_matrix_tsv,
    export_power_effect_size_grid_tsv,
    export_power_estimation_summary_tsv,
    export_power_variance_tsv,
    export_sample_cluster_tsv,
    export_sample_correlation_tsv,
    export_sample_distance_tsv,
    export_sample_exploration_summary_tsv,
    export_sample_outlier_tsv,
    export_sample_pca_scores_tsv,
    export_sample_pca_variance_tsv,
    export_quant_design_contrast_estimates_tsv,
    export_quant_design_matrix_tsv,
    export_quant_design_model_coefficients_tsv,
    export_time_course_differential_tsv,
    export_multi_condition_differential_abundance_tsv,
    fit_quant_design_matrix_model,
    impute_label_free_table,
    normalize_label_free_table,
    parse_limma_result_table,
    parse_ms1_feature_table,
    parse_precursor_intensity_table,
    parse_msstats_result_table,
    render_peptide_intensity_aggregation_tsv,
    render_peptide_intensity_missingness_mask_tsv,
    render_peptide_intensity_matrix_summary_tsv,
    render_peptide_intensity_matrix_tsv,
    render_peptide_intensity_missingness_tsv,
    render_protein_peptide_contribution_tsv,
    render_protein_intensity_matrix_summary_tsv,
    render_protein_intensity_matrix_tsv,
    render_protein_intensity_missingness_tsv,
    render_protein_lfq_disconnected_components_tsv,
    render_protein_lfq_matrix_tsv,
    render_protein_lfq_missingness_tsv,
    render_protein_lfq_pairwise_ratios_tsv,
    render_protein_lfq_summary_tsv,
    summarize_missing_values,
)
from bijux_proteomics.review import (
    VolcanoReviewPolicy,
    build_dia_volcano_review,
    build_label_based_volcano_review,
    build_ptm_volcano_review,
    export_volcano_review_html,
    export_volcano_review_json,
    export_volcano_review_svg,
)
from bijux_proteomics.sequences import (
    DecoyGenerationMode,
    DuplicateAccessionPolicy,
    FastaDatabaseProfile,
    FastaParseMode,
    FastaParseReport,
    PeptideUniquenessClass,
    append_contaminant_database,
    build_decoy_generation_manifest,
    build_decoy_generation_report,
    build_fasta_database_profile,
    build_fasta_provenance_manifest,
    build_fasta_stats,
    build_peptide_detectability_report,
    build_peptide_property_report,
    deduplicate_fasta_records,
    filter_fasta_records,
    generate_decoy_records,
    parse_fasta_document,
    render_fasta_profile_length_distribution_tsv,
    render_fasta_profile_invalid_sequence_tsv,
    render_fasta_profile_organism_distribution_tsv,
    render_fasta_profile_summary_tsv,
    render_fasta_records,
    render_peptide_detectability_tsv,
    build_theoretical_digest_bundle,
    export_theoretical_digest_bundle,
    sequence_checksum,
    validate_target_decoy_database,
)
from bijux_proteomics.sequences.core import NormalizedProteinRecord
from bijux_proteomics.sequences.digestion import (
    PeptideDigestionMode,
    ProteaseRule,
    build_digest_manifest,
    digest_protein_records,
    export_peptide_protein_table_tsv,
    export_peptides_fasta,
    export_peptides_jsonl,
    export_peptides_parquet,
    export_peptides_tsv,
    peptide_export_fingerprint,
    resolve_protease_rule,
)
from bijux_proteomics.sequences.peptide_uniqueness_audit import (
    build_peptide_database_lookup_report,
)
from bijux_proteomics.study.qc import (
    QcEvidenceInputFile,
    build_batch_qc_assessment,
    build_instrument_batch_qc_report,
    build_lcms_run_qc_report,
    build_performance_snapshot,
    build_qc_evidence_manifest,
    build_run_qc_assessment,
    default_qc_threshold_policy,
    load_qc_threshold_policy,
    render_qc_assessment_html,
    render_qc_assessment_tsv,
)
from bijux_proteomics.workflow import (
    BiologicalResultSelectionPolicy,
    DiaDifferentialSourceKind,
    ProteomicsRunEngine,
    build_diann_benchmark_report,
    build_maxquant_benchmark_report,
    build_proteomics_run_bundle,
    build_dia_differential_volcano_plot,
    build_diann_differential_analysis_report,
    build_diann_vs_dda_psm_comparison_report,
    build_label_based_differential_volcano_plot,
    build_silac_differential_analysis_report,
    build_tmt_differential_analysis_report,
    build_spectronaut_differential_analysis_report,
    export_dia_differential_matrix_tsv,
    export_dia_differential_qc_summary_tsv,
    export_dia_differential_results_tsv,
    export_dia_differential_volcano_plot_tsv,
    export_dia_normalization_balance_plot_tsv,
    export_label_based_differential_matrix_tsv,
    export_label_based_differential_results_tsv,
    export_label_based_differential_volcano_plot_tsv,
    export_label_based_normalization_balance_plot_tsv,
    export_proteomics_run_bundle,
    render_diann_benchmark_count_comparisons_tsv,
    render_diann_benchmark_protein_quantities_tsv,
    render_diann_benchmark_summary_tsv,
    render_maxquant_benchmark_summary_tsv,
    render_maxquant_differential_comparison_tsv,
    render_maxquant_filtering_comparison_tsv,
    render_maxquant_lfq_comparison_tsv,
    render_maxquant_protein_identity_comparison_tsv,
    render_proteomics_run_summary_tsv,
    render_dia_dda_comparison_summary_tsv,
    render_dia_dda_conflicting_evidence_tsv,
    render_dia_dda_differential_comparison_tsv,
    render_dia_dda_exclusive_evidence_tsv,
    render_dia_dda_peptide_overlap_tsv,
    render_dia_dda_protein_overlap_tsv,
    render_dia_dda_shared_intensity_correlation_tsv,
    render_public_benchmark_suite_failures_tsv,
    render_public_benchmark_suite_summary_tsv,
    run_public_benchmark_descriptor,
    run_public_benchmark_descriptor_suite,
)
from bijux_proteomics.workflow.orchestrator import (
    DdaWorkflowConfig,
    DiannWorkflowConfig,
    LabelFreeWorkflowConfig,
    MaxquantWorkflowConfig,
    PtmWorkflowConfig,
    SilacWorkflowConfig,
    TargetedWorkflowConfig,
    TargetedWorkflowStage,
    TmtWorkflowConfig,
    WorkflowMode,
    run_proteomics_workflow,
)


def _emit_json(payload: Any, *, out_path: Path | None = None) -> None:
    if hasattr(payload, "to_stable_json"):
        rendered = payload.to_stable_json()
    else:
        rendered = json.dumps(payload, indent=2, sort_keys=True)
    if out_path is not None:
        out_path.write_text(rendered + "\n")
    click.echo(rendered)


def _write_text_output(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _build_volcano_review_policy(
    *,
    adjusted_p_value_threshold: float,
    absolute_log2_fold_change_threshold: float,
    top_label_count: int,
) -> VolcanoReviewPolicy:
    return VolcanoReviewPolicy(
        adjusted_p_value_threshold=adjusted_p_value_threshold,
        absolute_log2_fold_change_threshold=absolute_log2_fold_change_threshold,
        top_label_count=top_label_count,
    )


def _run_orchestrated_workflow(config):
    try:
        return run_proteomics_workflow(config)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc


def _validate_proteomics_run_inputs(
    *,
    engine: ProteomicsRunEngine,
    report_path: Path | None,
    peptides_path: Path | None,
    protein_groups_path: Path | None,
    source_protein_tsv: Path | None,
    config_path: Path | None,
) -> None:
    if report_path is None:
        raise click.ClickException("--report is required")
    if engine is ProteomicsRunEngine.MAXQUANT:
        if peptides_path is None:
            raise click.ClickException(
                "MaxQuant runs require --peptides with peptides.txt"
            )
        if protein_groups_path is None:
            raise click.ClickException(
                "MaxQuant runs require --protein-groups with proteinGroups.txt"
            )
        return
    if peptides_path is not None:
        raise click.ClickException(
            f"{engine.value} runs do not accept --peptides; that input is MaxQuant-specific"
        )
    if protein_groups_path is not None:
        raise click.ClickException(
            f"{engine.value} runs do not accept --protein-groups; that input is MaxQuant-specific"
        )
    if engine is not ProteomicsRunEngine.FRAGPIPE and source_protein_tsv is not None:
        raise click.ClickException(
            f"{engine.value} runs do not accept --source-protein-tsv; that input is FragPipe-specific"
        )
    if engine is ProteomicsRunEngine.FRAGPIPE and config_path is not None:
        raise click.ClickException(
            "fragpipe runs do not accept --config-path in the flagship command"
        )


def _export_volcano_review_assets(
    *,
    review_report: Any,
    json_out: Path | None,
    svg_out: Path | None,
    html_out: Path | None,
) -> None:
    if json_out is not None:
        export_volcano_review_json(review_report, json_out)
    if svg_out is not None:
        export_volcano_review_svg(review_report, svg_out)
    if html_out is not None:
        export_volcano_review_html(review_report, html_out)


def _load_similarity_spectra(
    input_path: Path, *, kind: str
) -> tuple[SpectrumModel, ...]:
    resolved_kind = kind
    if resolved_kind == "auto":
        suffix = input_path.suffix.lower()
        if suffix == ".mgf":
            resolved_kind = "mgf"
        elif suffix == ".mzml":
            resolved_kind = "mzml"
        else:
            raise ValueError(
                f"cannot infer spectrum input kind for {input_path.name!r}; "
                "use --query-kind/--reference-kind mgf or mzml"
            )
    if resolved_kind == "mgf":
        return parse_mgf(input_path).accepted_spectra
    if resolved_kind == "mzml":
        return parse_mzml(input_path).accepted_spectra
    raise ValueError("spectrum similarity supports only mgf and mzml inputs")


def _select_similarity_spectrum(
    spectra: tuple[SpectrumModel, ...],
    *,
    input_path: Path,
    spectrum_id: str | None,
) -> SpectrumModel:
    if not spectra:
        raise ValueError(
            f"{input_path.name!r} does not contain an accepted spectrum for comparison"
        )
    if spectrum_id is None:
        return spectra[0]
    try:
        return next(item for item in spectra if item.spectrum_id == spectrum_id)
    except StopIteration as exc:
        raise ValueError(
            f"unknown spectrum id {spectrum_id!r} in {input_path.name!r}"
        ) from exc


def _load_protein_group_map(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("protein group map must include a header row")
        required = {"accession", "protein_group"}
        missing = required.difference(reader.fieldnames)
        if missing:
            missing_columns = ", ".join(sorted(missing))
            raise ValueError(
                "protein group map must include the columns "
                f"'accession' and 'protein_group'; missing: {missing_columns}"
            )
        mapping: dict[str, str] = {}
        for row in reader:
            accession = str(row.get("accession", "")).strip()
            protein_group = str(row.get("protein_group", "")).strip()
            if not accession or not protein_group:
                raise ValueError(
                    "protein group map rows must provide both accession and protein_group"
                )
            mapping[accession] = protein_group
    return mapping


def _resolve_cli_protease_rule(
    *,
    protease: str,
    custom_protease: str | None,
    custom_protease_name: str,
) -> tuple[ProteaseRule, str | None]:
    specification = custom_protease.strip() if custom_protease is not None else ""
    if not specification:
        rule = resolve_protease_rule(protease)
        return rule, None
    if protease != "trypsin":
        raise ValueError(
            "custom protease rules cannot be combined with a second built-in protease name"
        )
    rule = resolve_protease_rule(
        custom_specification=specification,
        custom_name=custom_protease_name,
    )
    return rule, specification


def _resolve_cli_theoretical_digest_modifications(
    *,
    static_modifications: tuple[str, ...],
    variable_modifications: tuple[str, ...],
    registry_path: Path | None,
    allow_isotopic_labels: bool,
    allowed_label_families: tuple[str, ...],
) -> tuple[
    ModificationRegistryDocument | None,
    tuple[StaticModification, ...],
    tuple[VariableModification, ...],
    IsotopicLabelingPolicy | None,
]:
    registry = (
        load_modification_registry(registry_path)
        if registry_path is not None
        else None
    )
    resolved_static: list[StaticModification] = []
    for token in static_modifications:
        definition = get_modification(token, registry=registry)
        if not isinstance(definition, StaticModification):
            raise ValueError(f"static modification {token!r} is not a static definition")
        resolved_static.append(definition)
    resolved_variable: list[VariableModification] = []
    for token in variable_modifications:
        definition = get_modification(token, registry=registry)
        if not isinstance(definition, VariableModification):
            raise ValueError(
                f"variable modification {token!r} is not a variable definition"
            )
        resolved_variable.append(definition)
    labeling_policy = (
        IsotopicLabelingPolicy(
            allow_isotopic_labels=allow_isotopic_labels,
            allowed_label_families=allowed_label_families,
        )
        if allow_isotopic_labels or allowed_label_families
        else None
    )
    return registry, tuple(resolved_static), tuple(resolved_variable), labeling_policy


def _emit_fasta_profile(
    profile: FastaDatabaseProfile,
    *,
    out_path: Path | None,
    summary_tsv_out: Path | None,
    length_tsv_out: Path | None,
    organism_tsv_out: Path | None,
    invalid_sequence_tsv_out: Path | None,
) -> None:
    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_fasta_profile_summary_tsv(profile))
    if length_tsv_out is not None:
        _write_text_output(
            length_tsv_out, render_fasta_profile_length_distribution_tsv(profile)
        )
    if organism_tsv_out is not None:
        _write_text_output(
            organism_tsv_out, render_fasta_profile_organism_distribution_tsv(profile)
        )
    if invalid_sequence_tsv_out is not None:
        _write_text_output(
            invalid_sequence_tsv_out,
            render_fasta_profile_invalid_sequence_tsv(profile),
        )
    _emit_json(profile, out_path=out_path)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_fasta_report(
    input_path: Path,
    *,
    mode: FastaParseMode,
    duplicate_accession_policy: DuplicateAccessionPolicy = DuplicateAccessionPolicy.REJECT,
    allow_rejected: bool,
) -> FastaParseReport:
    report = parse_fasta_document(
        input_path.read_text(),
        mode=mode,
        duplicate_accession_policy=duplicate_accession_policy,
    )
    if report.rejected_records and not allow_rejected:
        rejected = ", ".join(
            rejected.source_identifier for rejected in report.rejected_records
        )
        raise click.ClickException(
            f"FASTA input contains rejected records under {mode.value} mode: {rejected}"
        )
    return report


def _load_precursor_mass_error_queries(
    input_tsv: Path,
    *,
    peptide_column: str,
    observed_mz_column: str,
    charge_column: str,
    spectrum_id_column: str | None,
) -> tuple[PrecursorMassErrorQuery, ...]:
    queries: list[PrecursorMassErrorQuery] = []
    with input_tsv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "precursor mass-error TSV must include a header row"
            )
        for required_column in (peptide_column, observed_mz_column, charge_column):
            if required_column not in reader.fieldnames:
                raise click.ClickException(
                    f"missing required precursor mass-error column {required_column!r}"
                )

        for row_number, row in enumerate(reader, start=2):
            try:
                peptide = str(row.get(peptide_column, "")).strip()
                observed_mz = float(str(row.get(observed_mz_column, "")).strip())
                charge = int(str(row.get(charge_column, "")).strip())
                if not peptide:
                    raise ValueError("peptide must not be blank")
                if observed_mz <= 0:
                    raise ValueError("observed_mz must be greater than zero")
                if charge < 1:
                    raise ValueError("charge must be at least 1")
                spectrum_id = (
                    str(row.get(spectrum_id_column, "")).strip()
                    if spectrum_id_column is not None
                    else ""
                )
                queries.append(
                    PrecursorMassErrorQuery(
                        peptide=peptide,
                        observed_mz=observed_mz,
                        charge=charge,
                        spectrum_id=spectrum_id or None,
                    )
                )
            except (TypeError, ValueError) as exc:
                raise click.ClickException(
                    f"invalid precursor mass-error row at line {row_number}: {exc}"
                ) from exc
    return tuple(queries)


def _mode_choice() -> click.Choice[str]:
    return click.Choice([mode.value for mode in FastaParseMode], case_sensitive=False)


def _duplicate_accession_policy_choice() -> click.Choice[str]:
    return click.Choice(
        [policy.value for policy in DuplicateAccessionPolicy],
        case_sensitive=False,
    )


def _decoy_mode_choice() -> click.Choice[str]:
    return click.Choice(
        [mode.value for mode in DecoyGenerationMode],
        case_sensitive=False,
    )


def _digestion_mode_choice() -> click.Choice[str]:
    return click.Choice(
        [mode.value for mode in PeptideDigestionMode],
        case_sensitive=False,
    )


def _export_format_choice() -> click.Choice[str]:
    return click.Choice(["tsv", "jsonl", "parquet", "fasta"], case_sensitive=False)


def _fragment_series_choice() -> click.Choice[str]:
    return click.Choice(
        [series.value for series in FragmentIonSeries], case_sensitive=False
    )


def _modified_peptide_dialect_choice() -> click.Choice[str]:
    return click.Choice(
        [dialect.value for dialect in SearchEngineModifiedPeptideDialect],
        case_sensitive=False,
    )


def _validate_kind_choice() -> click.Choice[str]:
    return click.Choice(
        ["auto", "fasta", "psm", "mgf", "mzml", "mod-registry", "design-table"],
        case_sensitive=False,
    )


def _conversion_target_choice() -> click.Choice[str]:
    return click.Choice(
        [target.value for target in FormatConversionTarget], case_sensitive=False
    )


def _search_adapter_choice() -> click.Choice[str]:
    return click.Choice(
        [adapter.value for adapter in SearchAdapterKind], case_sensitive=False
    )


def _score_orientation_choice() -> click.Choice[str]:
    return click.Choice(
        [orientation.value for orientation in ScoreOrientation], case_sensitive=False
    )


def _quant_entity_level_choice() -> click.Choice[str]:
    return click.Choice(
        [level.value for level in QuantEntityLevel], case_sensitive=False
    )


def _quant_measure_choice() -> click.Choice[str]:
    return click.Choice(
        [measure.value for measure in QuantMeasureKind], case_sensitive=False
    )


def _quant_rollup_choice() -> click.Choice[str]:
    return click.Choice(
        [method.value for method in QuantRollupMethod], case_sensitive=False
    )


def _normalization_choice() -> click.Choice[str]:
    return click.Choice(
        [method.value for method in NormalizationMethod], case_sensitive=False
    )


def _imputation_choice() -> click.Choice[str]:
    return click.Choice(
        [method.value for method in ImputationMethod], case_sensitive=False
    )


def _heatmap_missing_value_choice() -> click.Choice[str]:
    return click.Choice(
        [policy.value for policy in HeatmapMissingValuePolicy],
        case_sensitive=False,
    )


def _peptide_matrix_input_kind_choice() -> click.Choice[str]:
    return click.Choice(("feature", "psm"), case_sensitive=False)


def _peptide_matrix_builder_input_kind_choice() -> click.Choice[str]:
    return click.Choice(("feature", "precursor", "psm"), case_sensitive=False)


def _peptide_matrix_grouping_choice() -> click.Choice[str]:
    return click.Choice(
        [mode.value for mode in PeptideMatrixGroupingMode], case_sensitive=False
    )


def _protein_matrix_target_choice() -> click.Choice[str]:
    return click.Choice(
        [kind.value for kind in ProteinMatrixTargetKind], case_sensitive=False
    )


def _tmt_source_kind_choice() -> click.Choice[str]:
    return click.Choice(
        [kind.value for kind in TmtSearchResultSourceKind], case_sensitive=False
    )


def _tmt_normalization_method_choice() -> click.Choice[str]:
    return click.Choice(
        [method.value for method in TmtNormalizationMethod], case_sensitive=False
    )


def _tmt_ratio_normalization_choice() -> click.Choice[str]:
    return click.Choice(
        ("none", *[method.value for method in TmtNormalizationMethod]),
        case_sensitive=False,
    )


def _label_based_differential_normalization_choice() -> click.Choice[str]:
    return click.Choice(
        (NormalizationMethod.NONE.value, NormalizationMethod.MEDIAN.value),
        case_sensitive=False,
    )


def _silac_label_choice() -> click.Choice[str]:
    return click.Choice([label.value for label in SilacLabel], case_sensitive=False)


def _workflow_scheduler_choice() -> click.Choice[str]:
    return click.Choice(
        [scheduler.value for scheduler in WorkflowSchedulerKind], case_sensitive=False
    )


def _parse_tmt_channel_column_specs(
    specs: tuple[str, ...],
) -> tuple[TmtReporterChannelColumn, ...]:
    resolved: list[TmtReporterChannelColumn] = []
    for spec in specs:
        if "=" not in spec:
            raise click.ClickException(
                "channel-column must use CHANNEL=COLUMN syntax"
            )
        channel, column_name = spec.split("=", 1)
        channel = channel.strip()
        column_name = column_name.strip()
        if not channel or not column_name:
            raise click.ClickException(
                "channel-column must use CHANNEL=COLUMN syntax"
            )
        resolved.append(
            TmtReporterChannelColumn(
                multiplex_channel=channel,
                column_name=column_name,
            )
        )
    return tuple(resolved)


def _parse_silac_label_spec(spec: str) -> tuple[SilacLabel, ...]:
    labels = tuple(
        SilacLabel(token.strip().lower())
        for token in spec.split(",")
        if token.strip()
    )
    if len(labels) < 2:
        raise click.ClickException("labels must name at least two SILAC label states")
    return labels


def _select_design_entry(
    design_path: Path | None,
    *,
    sample_id: str | None,
    spectra_path: Path,
) -> ExperimentalDesignEntry | None:
    if design_path is None:
        return None
    report = parse_experimental_design_table(design_path)
    if report.rejected_rows:
        raise ProteomicsOperatorError(
            ProteomicsOperatorErrorCode.INPUT_DESIGN_INVALID,
            "design table contains rejected rows",
        )
    if sample_id is not None:
        for entry in report.accepted_entries:
            if entry.sample_id == sample_id:
                return entry
        raise ProteomicsOperatorError(
            ProteomicsOperatorErrorCode.QC_SAMPLE_NOT_FOUND,
            f"sample {sample_id!r} is not present in the design table",
        )
    matching_entries = [
        entry
        for entry in report.accepted_entries
        if Path(entry.spectra_file).name == spectra_path.name
    ]
    if len(matching_entries) == 1:
        return matching_entries[0]
    if len(report.accepted_entries) == 1:
        return report.accepted_entries[0]
    raise ProteomicsOperatorError(
        ProteomicsOperatorErrorCode.QC_SAMPLE_NOT_FOUND,
        "design table requires --sample-id when multiple rows are present",
    )


def _build_psm_mapping(
    *,
    run_id_column: str | None,
    spectrum_id_column: str,
    peptide_column: str,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    posterior_error_probability_column: str | None = None,
    intensity_column: str | None = None,
) -> SearchResultColumnMapping:
    return SearchResultColumnMapping(
        run_id=run_id_column,
        spectrum_id=spectrum_id_column,
        peptide=peptide_column,
        modified_peptide=modified_peptide_column,
        charge=charge_column,
        score=score_column,
        intensity=intensity_column,
        q_value=q_value_column,
        posterior_error_probability=posterior_error_probability_column,
        protein_refs=protein_refs_column,
        decoy_label=decoy_label_column,
        contaminant_label=contaminant_label_column,
        protein_separator=protein_separator,
    )


def _build_decoy_policy(
    *,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
) -> TargetDecoyLabelPolicy:
    return TargetDecoyLabelPolicy(
        protein_prefix=decoy_prefix,
        protein_suffix=decoy_suffix,
    )


def _build_run_detection_contexts(
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> tuple[RunDetectionContext, ...]:
    return tuple(
        RunDetectionContext(
            run_id=entry.spectra_file,
            sample_id=entry.sample_id,
            condition_id=entry.condition,
            replicate_id=str(entry.replicate),
        )
        for entry in design_entries
    )


def _filter_review_psms(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float,
    score_orientation: str,
) -> tuple[PsmRecord, ...]:
    """Preserve imported q-values for review surfaces when they are complete."""
    if records and all(record.q_value is not None for record in records):
        return tuple(
            record
            for record in records
            if record.q_value is not None and record.q_value <= threshold
        )
    return filter_psms_by_fdr(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
    )


def _default_psm_mapping() -> SearchResultColumnMapping:
    return SearchResultColumnMapping(
        spectrum_id="spectrum_id",
        peptide="peptide",
        charge="charge",
        score="score",
        q_value="q_value",
        protein_refs="proteins",
    )


def _infer_input_kind(input_path: Path, explicit_kind: str) -> str:
    if explicit_kind != "auto":
        return explicit_kind
    suffix = input_path.suffix.lower()
    if suffix in {".fasta", ".fa", ".faa"}:
        return "fasta"
    if suffix == ".mgf":
        return "mgf"
    if suffix == ".mzml":
        return "mzml"
    if input_path.name.endswith(".design.tsv") or input_path.name.endswith(
        ".design.csv"
    ):
        return "design-table"
    if suffix == ".tsv":
        return "psm"
    if suffix == ".json":
        return "mod-registry"
    raise click.ClickException(
        f"cannot infer input kind for {input_path.name!r}; use --kind fasta, psm, mgf, mzml, design-table, or mod-registry"
    )


@click.group()
def cli() -> None:
    """Manage program manifests and protein-sequence operations."""


@cli.command("program-template")
@click.option("--program-id", required=True, help="Stable program identifier.")
@click.option("--name", required=True, help="Program name.")
@click.option("--objective", required=True, help="Scientific objective.")
@click.option("--target-id", required=True, help="Stable target identifier.")
@click.option("--target-name", required=True, help="Target name.")
@click.option("--sequence", required=True, help="Reference amino-acid sequence.")
@click.option("--organism", required=True, help="Source organism.")
@click.option("--mechanism", required=True, help="Working target hypothesis.")
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Where to write the JSON document.",
)
def program_template(
    program_id: str,
    name: str,
    objective: str,
    target_id: str,
    target_name: str,
    sequence: str,
    organism: str,
    mechanism: str,
    out_path: Path,
) -> None:
    """Write a starter program manifest."""
    program = create_program_spec(
        program_id=program_id,
        name=name,
        objective=objective,
        target_id=target_id,
        target_name=target_name,
        sequence=sequence,
        organism=organism,
        mechanism=mechanism,
    )
    program.save_json(out_path)
    click.echo(json.dumps(program_summary(program), sort_keys=True))


@cli.command("summarize-program")
@click.argument("program_file", type=click.Path(exists=True, path_type=Path))
def summarize_program(program_file: Path) -> None:
    """Print a compact summary for a program document."""
    program = ProgramSpec.load_json(program_file)
    click.echo(json.dumps(program_summary(program), sort_keys=True))


@cli.command("sequence-checksum")
@click.option(
    "--sequence", required=True, help="Protein sequence to normalize and hash."
)
def sequence_checksum_command(sequence: str) -> None:
    """Emit the normalized sequence checksum for one protein sequence string."""
    normalized = "".join(
        character for character in sequence.upper() if not character.isspace()
    )
    _emit_json(
        {
            "normalized_sequence": normalized,
            "residue_count": len(normalized),
            "sequence_checksum": sequence_checksum(sequence),
        }
    )


@cli.command("fasta-parse")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--duplicate-accession-policy",
    type=_duplicate_accession_policy_choice(),
    default=DuplicateAccessionPolicy.REJECT.value,
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def fasta_parse_command(
    input_fasta: Path,
    mode: str,
    duplicate_accession_policy: str,
    out_path: Path | None,
) -> None:
    """Parse FASTA input and emit normalized acceptance and rejection details."""
    report = parse_fasta_document(
        input_fasta.read_text(),
        mode=FastaParseMode(mode),
        duplicate_accession_policy=DuplicateAccessionPolicy(
            duplicate_accession_policy
        ),
    )
    _emit_json(report, out_path=out_path)


@cli.command("fasta-dedup")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--duplicate-accession-policy",
    type=_duplicate_accession_policy_choice(),
    default=DuplicateAccessionPolicy.REJECT.value,
    show_default=True,
)
@click.option(
    "--out-fasta",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Where to write the deduplicated FASTA.",
)
@click.option(
    "--report-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def fasta_dedup_command(
    input_fasta: Path,
    mode: str,
    duplicate_accession_policy: str,
    out_fasta: Path,
    report_out: Path | None,
) -> None:
    """Deduplicate FASTA records by accession and normalized sequence digest."""
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        duplicate_accession_policy=DuplicateAccessionPolicy(
            duplicate_accession_policy
        ),
        allow_rejected=False,
    )
    deduplicated, dedup_report = deduplicate_fasta_records(report.accepted_records)
    out_fasta.write_text(render_fasta_records(deduplicated))
    _emit_json(dedup_report, out_path=report_out)


@cli.command("fasta-contaminants")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--duplicate-accession-policy",
    type=_duplicate_accession_policy_choice(),
    default=DuplicateAccessionPolicy.REJECT.value,
    show_default=True,
)
@click.option(
    "--include-builtin/--no-include-builtin",
    default=True,
    show_default=True,
    help="Append the owned built-in contaminant panel.",
)
@click.option(
    "--contaminant-fasta",
    "contaminant_fastas",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    multiple=True,
    help="Optional external contaminant FASTA path to append after relabeling.",
)
@click.option(
    "--out-fasta",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Where to write the combined target-plus-contaminant FASTA.",
)
@click.option(
    "--report-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON build report output path.",
)
def fasta_contaminants_command(
    input_fasta: Path,
    mode: str,
    duplicate_accession_policy: str,
    include_builtin: bool,
    contaminant_fastas: tuple[Path, ...],
    out_fasta: Path,
    report_out: Path | None,
) -> None:
    """Append labeled contaminant proteins to one target FASTA database."""
    target_report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=False,
        duplicate_accession_policy=DuplicateAccessionPolicy(
            duplicate_accession_policy
        ),
    )
    external_records: list[NormalizedProteinRecord] = []
    for contaminant_fasta in contaminant_fastas:
        contaminant_report = _load_fasta_report(
            contaminant_fasta,
            mode=FastaParseMode(mode),
            allow_rejected=False,
            duplicate_accession_policy=DuplicateAccessionPolicy(
                duplicate_accession_policy
            ),
        )
        external_records.extend(contaminant_report.accepted_records)
    combined, build_report = append_contaminant_database(
        target_report.accepted_records,
        include_builtin=include_builtin,
        external_contaminant_records=tuple(external_records),
    )
    out_fasta.write_text(render_fasta_records(combined))
    _emit_json(build_report, out_path=report_out)


@cli.command("fasta-filter")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--duplicate-accession-policy",
    type=_duplicate_accession_policy_choice(),
    default=DuplicateAccessionPolicy.REJECT.value,
    show_default=True,
)
@click.option("--min-length", type=int, default=None)
@click.option("--max-length", type=int, default=None)
@click.option(
    "--accession-pattern",
    default=None,
    help="Regular expression over canonical accession.",
)
@click.option(
    "--organism", default=None, help="Exact organism filter, case-insensitive."
)
@click.option("--exclude-contaminants", is_flag=True, default=False)
@click.option(
    "--out-fasta",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Where to write the filtered FASTA.",
)
@click.option(
    "--report-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def fasta_filter_command(
    input_fasta: Path,
    mode: str,
    duplicate_accession_policy: str,
    min_length: int | None,
    max_length: int | None,
    accession_pattern: str | None,
    organism: str | None,
    exclude_contaminants: bool,
    out_fasta: Path,
    report_out: Path | None,
) -> None:
    """Filter FASTA records while emitting explicit exclusion counts."""
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        duplicate_accession_policy=DuplicateAccessionPolicy(
            duplicate_accession_policy
        ),
        allow_rejected=False,
    )
    filtered, filter_report = filter_fasta_records(
        report.accepted_records,
        min_length=min_length,
        max_length=max_length,
        accession_pattern=accession_pattern,
        organism=organism,
        exclude_contaminants=exclude_contaminants,
    )
    out_fasta.write_text(render_fasta_records(filtered))
    _emit_json(filter_report, out_path=report_out)


@cli.command("fasta-stats")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--duplicate-accession-policy",
    type=_duplicate_accession_policy_choice(),
    default=DuplicateAccessionPolicy.REJECT.value,
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def fasta_stats_command(
    input_fasta: Path,
    mode: str,
    duplicate_accession_policy: str,
    out_path: Path | None,
) -> None:
    """Report FASTA record, composition, residue, duplication, and contaminant metrics."""
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        duplicate_accession_policy=DuplicateAccessionPolicy(
            duplicate_accession_policy
        ),
        allow_rejected=True,
    )
    stats = build_fasta_stats(
        report.accepted_records,
        rejected_records=report.rejected_records,
    )
    _emit_json(stats, out_path=out_path)


@cli.command("fasta-profile")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--duplicate-accession-policy",
    type=_duplicate_accession_policy_choice(),
    default=DuplicateAccessionPolicy.REJECT.value,
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON profile output path.",
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional summary TSV output path.",
)
@click.option(
    "--length-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional length-distribution TSV output path.",
)
@click.option(
    "--organism-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional organism-distribution TSV output path.",
)
@click.option(
    "--invalid-sequence-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional invalid-sequence TSV output path.",
)
def fasta_profile_command(
    input_fasta: Path,
    mode: str,
    duplicate_accession_policy: str,
    out_path: Path | None,
    summary_tsv_out: Path | None,
    length_tsv_out: Path | None,
    organism_tsv_out: Path | None,
    invalid_sequence_tsv_out: Path | None,
) -> None:
    """Profile one FASTA database with composition, organism, and rejection ledgers."""
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        duplicate_accession_policy=DuplicateAccessionPolicy(
            duplicate_accession_policy
        ),
        allow_rejected=True,
    )
    profile = build_fasta_database_profile(
        report.accepted_records,
        rejected_records=report.rejected_records,
    )
    _emit_fasta_profile(
        profile,
        out_path=out_path,
        summary_tsv_out=summary_tsv_out,
        length_tsv_out=length_tsv_out,
        organism_tsv_out=organism_tsv_out,
        invalid_sequence_tsv_out=invalid_sequence_tsv_out,
    )


@cli.command("psm-contaminants")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--contaminant-prefix",
    "contaminant_prefixes",
    multiple=True,
    default=("CON__",),
    show_default=True,
    help="Protein-reference prefixes that mark contaminant evidence.",
)
@click.option("--run-id-column", default=None)
@click.option("--intensity-column", default=None)
@click.option(
    "--burden-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--protein-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON contaminant-match report output path.",
)
def psm_contaminants_command(
    input_tsv: Path,
    contaminant_prefixes: tuple[str, ...],
    run_id_column: str | None,
    intensity_column: str | None,
    burden_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Separate contaminant-carrying peptide-spectrum matches from target-only evidence."""
    report = parse_psm_tsv(
        input_tsv,
        mapping=_build_psm_mapping(
            run_id_column=run_id_column,
            spectrum_id_column="spectrum_id",
            peptide_column="peptide",
            modified_peptide_column=None,
            charge_column="charge",
            score_column="score",
            q_value_column="q_value",
            protein_refs_column="proteins",
            decoy_label_column=None,
            contaminant_label_column=None,
            protein_separator=";",
            intensity_column=intensity_column,
        ),
    )
    contaminant_report = build_contaminant_peptide_match_report(
        report.accepted_records,
        contaminant_prefixes=tuple(contaminant_prefixes),
    )
    contaminant_evidence = build_contaminant_evidence_report(
        report.accepted_records,
        contaminant_prefixes=tuple(contaminant_prefixes),
    )
    if burden_tsv_out is not None:
        _write_text_output(
            burden_tsv_out,
            render_contaminant_burden_tsv(contaminant_evidence),
        )
    if protein_tsv_out is not None:
        _write_text_output(
            protein_tsv_out,
            render_contaminant_proteins_tsv(contaminant_evidence),
        )
    _emit_json(
        {
            **contaminant_report.to_dict(),
            "contaminant_evidence": contaminant_evidence.to_dict(),
        },
        out_path=out_path,
    )


@cli.command("fragpipe-import")
@click.argument("psm_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--peptide-tsv",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--protein-tsv",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--quant-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--canonical-psm-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--psm-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--peptide-review-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--protein-review-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--open-search-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--protein-quantity-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--rejected-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def fragpipe_import_command(
    psm_tsv: Path,
    peptide_tsv: Path,
    protein_tsv: Path,
    quant_tsv: Path | None,
    summary_tsv_out: Path | None,
    canonical_psm_tsv_out: Path | None,
    psm_tsv_out: Path | None,
    peptide_review_tsv_out: Path | None,
    protein_review_tsv_out: Path | None,
    open_search_tsv_out: Path | None,
    protein_quantity_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Import one FragPipe result bundle with explicit PSM, peptide, and protein review."""
    try:
        report = build_fragpipe_import_report(
            psm_tsv,
            peptide_tsv_path=peptide_tsv,
            protein_tsv_path=protein_tsv,
            quant_tsv_path=quant_tsv,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_fragpipe_summary_tsv(report.summary))
    if canonical_psm_tsv_out is not None:
        _write_text_output(
            canonical_psm_tsv_out,
            render_fragpipe_canonical_psm_tsv(report.canonical_psms),
        )
    if psm_tsv_out is not None:
        _write_text_output(psm_tsv_out, render_fragpipe_psm_tsv(report.psm_rows))
    if peptide_review_tsv_out is not None:
        _write_text_output(
            peptide_review_tsv_out,
            render_fragpipe_peptide_tsv(report.peptide_rows),
        )
    if protein_review_tsv_out is not None:
        _write_text_output(
            protein_review_tsv_out,
            render_fragpipe_protein_tsv(report.protein_rows),
        )
    if open_search_tsv_out is not None:
        _write_text_output(
            open_search_tsv_out,
            render_fragpipe_open_search_evidence_tsv(report.open_search_evidence),
        )
    if protein_quantity_tsv_out is not None:
        _write_text_output(
            protein_quantity_tsv_out,
            render_fragpipe_protein_quantity_tsv(report.protein_quantity_rows),
        )
    if rejected_tsv_out is not None:
        _write_text_output(
            rejected_tsv_out,
            render_rejected_evidence_tsv(report.rejected_evidence_rows),
        )

    payload = {
        "summary": report.summary.to_dict(),
        "psm_normalization": {
            "adapter": report.psm_normalization.adapter_manifest.to_dict(),
            "accepted_rows": len(
                report.psm_normalization.parse_report.accepted_records
            ),
            "rejected_rows": len(report.psm_normalization.parse_report.rejected_rows),
        },
        "canonical_psms": [row.to_dict() for row in report.canonical_psms],
        "psm_rows": [row.to_dict() for row in report.psm_rows],
        "peptide_rows": [row.to_dict() for row in report.peptide_rows],
        "protein_rows": [row.to_dict() for row in report.protein_rows],
        "open_search_evidence": [row.to_dict() for row in report.open_search_evidence],
        "protein_quantity_rows": [row.to_dict() for row in report.protein_quantity_rows],
        "rejected_evidence_rows": [
            row.to_dict() for row in report.rejected_evidence_rows
        ],
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "canonical_psm_tsv": None
            if canonical_psm_tsv_out is None
            else str(canonical_psm_tsv_out),
            "psm_tsv": None if psm_tsv_out is None else str(psm_tsv_out),
            "peptide_review_tsv": None
            if peptide_review_tsv_out is None
            else str(peptide_review_tsv_out),
            "protein_review_tsv": None
            if protein_review_tsv_out is None
            else str(protein_review_tsv_out),
            "open_search_tsv": None
            if open_search_tsv_out is None
            else str(open_search_tsv_out),
            "protein_quantity_tsv": None
            if protein_quantity_tsv_out is None
            else str(protein_quantity_tsv_out),
            "rejected_tsv": None
            if rejected_tsv_out is None
            else str(rejected_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("fragpipe-benchmark")
@click.argument("psm_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--peptide-tsv",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--protein-tsv",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--count-comparisons-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--protein-groups-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--psm-qvalues-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--peptide-qvalues-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def fragpipe_benchmark_command(
    psm_tsv: Path,
    peptide_tsv: Path,
    protein_tsv: Path,
    summary_tsv_out: Path | None,
    count_comparisons_tsv_out: Path | None,
    protein_groups_tsv_out: Path | None,
    psm_qvalues_tsv_out: Path | None,
    peptide_qvalues_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Benchmark governed FragPipe import behavior against the source FragPipe bundle."""
    try:
        report = build_fragpipe_import_benchmark_report(
            psm_tsv,
            peptide_tsv_path=peptide_tsv,
            protein_tsv_path=protein_tsv,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_fragpipe_benchmark_summary_tsv(report),
        )
    if count_comparisons_tsv_out is not None:
        _write_text_output(
            count_comparisons_tsv_out,
            render_fragpipe_count_comparisons_tsv(report),
        )
    if protein_groups_tsv_out is not None:
        _write_text_output(
            protein_groups_tsv_out,
            render_fragpipe_protein_group_comparison_tsv(report),
        )
    if psm_qvalues_tsv_out is not None:
        _write_text_output(
            psm_qvalues_tsv_out,
            render_fragpipe_q_value_comparison_tsv(report.q_value_behavior.psm_entries),
        )
    if peptide_qvalues_tsv_out is not None:
        _write_text_output(
            peptide_qvalues_tsv_out,
            render_fragpipe_q_value_comparison_tsv(
                report.q_value_behavior.peptide_entries
            ),
        )

    payload = {
        "summary": report.summary.to_dict(),
        "protein_group_comparison": report.protein_group_comparison.to_dict(),
        "q_value_behavior": report.q_value_behavior.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "count_comparisons_tsv": None
            if count_comparisons_tsv_out is None
            else str(count_comparisons_tsv_out),
            "protein_groups_tsv": None
            if protein_groups_tsv_out is None
            else str(protein_groups_tsv_out),
            "psm_qvalues_tsv": None
            if psm_qvalues_tsv_out is None
            else str(psm_qvalues_tsv_out),
            "peptide_qvalues_tsv": None
            if peptide_qvalues_tsv_out is None
            else str(peptide_qvalues_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("sage-import")
@click.argument(
    "result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--canonical-psm-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--psm-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--rejected-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def sage_import_command(
    result_tsv: Path,
    config_path: Path | None,
    summary_tsv_out: Path | None,
    canonical_psm_tsv_out: Path | None,
    psm_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Import one Sage result table with explicit score, q-value, and modification review."""
    try:
        report = build_sage_import_report(result_tsv, config_path=config_path)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_sage_summary_tsv(report.summary))
    if canonical_psm_tsv_out is not None:
        _write_text_output(
            canonical_psm_tsv_out,
            render_sage_canonical_psm_tsv(report.canonical_psms),
        )
    if psm_tsv_out is not None:
        _write_text_output(psm_tsv_out, render_sage_psm_tsv(report.psm_rows))
    if rejected_tsv_out is not None:
        _write_text_output(
            rejected_tsv_out,
            render_rejected_evidence_tsv(report.rejected_evidence_rows),
        )

    payload = {
        "dialect_id": report.dialect_id,
        "summary": report.summary.to_dict(),
        "normalization": {
            "adapter": report.normalization.adapter_manifest.to_dict(),
            "accepted_rows": len(report.normalization.parse_report.accepted_records),
            "rejected_rows": len(report.normalization.parse_report.rejected_rows),
        },
        "parameter_report": None
        if report.parameter_report is None
        else report.parameter_report.to_dict(),
        "canonical_psms": [row.to_dict() for row in report.canonical_psms],
        "psm_rows": [row.to_dict() for row in report.psm_rows],
        "rejected_evidence_rows": [
            row.to_dict() for row in report.rejected_evidence_rows
        ],
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "canonical_psm_tsv": None
            if canonical_psm_tsv_out is None
            else str(canonical_psm_tsv_out),
            "psm_tsv": None if psm_tsv_out is None else str(psm_tsv_out),
            "rejected_tsv": None
            if rejected_tsv_out is None
            else str(rejected_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("comet-import")
@click.argument(
    "result_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--canonical-psm-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--psm-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--rejected-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def comet_import_command(
    result_path: Path,
    config_path: Path | None,
    summary_tsv_out: Path | None,
    canonical_psm_tsv_out: Path | None,
    psm_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Import one Comet tabular or pepXML result file with explicit score review."""
    try:
        report = build_comet_import_report(result_path, config_path=config_path)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_comet_summary_tsv(report.summary))
    if canonical_psm_tsv_out is not None:
        _write_text_output(
            canonical_psm_tsv_out,
            render_comet_canonical_psm_tsv(report.canonical_psms),
        )
    if psm_tsv_out is not None:
        _write_text_output(psm_tsv_out, render_comet_psm_tsv(report.psm_rows))
    if rejected_tsv_out is not None:
        _write_text_output(
            rejected_tsv_out,
            render_rejected_evidence_tsv(report.rejected_evidence_rows),
        )

    payload = {
        "import_kind": report.import_kind.value,
        "summary": report.summary.to_dict(),
        "normalization": None
        if report.normalization is None
        else {
            "adapter": report.normalization.adapter_manifest.to_dict(),
            "accepted_rows": len(report.normalization.parse_report.accepted_records),
            "rejected_rows": len(report.normalization.parse_report.rejected_rows),
        },
        "parameter_report": None
        if report.parameter_report is None
        else report.parameter_report.to_dict(),
        "canonical_psms": [row.to_dict() for row in report.canonical_psms],
        "psm_rows": [row.to_dict() for row in report.psm_rows],
        "rejected_evidence_rows": [
            row.to_dict() for row in report.rejected_evidence_rows
        ],
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "canonical_psm_tsv": None
            if canonical_psm_tsv_out is None
            else str(canonical_psm_tsv_out),
            "psm_tsv": None if psm_tsv_out is None else str(psm_tsv_out),
            "rejected_tsv": None
            if rejected_tsv_out is None
            else str(rejected_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("maxquant-import")
@click.argument(
    "evidence_txt", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--peptides-txt",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--protein-groups-txt",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--evidence-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--peptide-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--protein-group-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option(
    "--lfq-candidate-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option("--rejected-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def maxquant_import_command(
    evidence_txt: Path,
    peptides_txt: Path,
    protein_groups_txt: Path,
    config_path: Path | None,
    summary_tsv_out: Path | None,
    evidence_tsv_out: Path | None,
    peptide_tsv_out: Path | None,
    protein_group_tsv_out: Path | None,
    lfq_candidate_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Import one MaxQuant evidence, peptide, and protein-group bundle."""
    try:
        report = build_maxquant_import_report(
            evidence_txt,
            peptides_txt_path=peptides_txt,
            protein_groups_txt_path=protein_groups_txt,
            config_path=config_path,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_maxquant_summary_tsv(report.summary))
    if evidence_tsv_out is not None:
        _write_text_output(
            evidence_tsv_out,
            render_maxquant_evidence_tsv(report.evidence_rows),
        )
    if peptide_tsv_out is not None:
        _write_text_output(
            peptide_tsv_out, render_maxquant_peptide_tsv(report.peptide_rows)
        )
    if protein_group_tsv_out is not None:
        _write_text_output(
            protein_group_tsv_out,
            render_maxquant_protein_group_tsv(report.protein_group_rows),
        )
    if lfq_candidate_tsv_out is not None:
        _write_text_output(
            lfq_candidate_tsv_out,
            render_maxquant_lfq_candidate_tsv(report.lfq_matrix_candidates),
        )
    if rejected_tsv_out is not None:
        _write_text_output(
            rejected_tsv_out,
            render_rejected_evidence_tsv(report.rejected_evidence_rows),
        )

    payload = {
        "summary": report.summary.to_dict(),
        "evidence_normalization": {
            "adapter": report.evidence_normalization.adapter_manifest.to_dict(),
            "accepted_rows": len(
                report.evidence_normalization.parse_report.accepted_records
            ),
            "rejected_rows": len(
                report.evidence_normalization.parse_report.rejected_rows
            ),
        },
        "parameter_report": None
        if report.parameter_report is None
        else report.parameter_report.to_dict(),
        "evidence_rows": [row.to_dict() for row in report.evidence_rows],
        "peptide_rows": [row.to_dict() for row in report.peptide_rows],
        "protein_group_rows": [row.to_dict() for row in report.protein_group_rows],
        "lfq_matrix_candidates": [
            row.to_dict() for row in report.lfq_matrix_candidates
        ],
        "rejected_evidence_rows": [
            row.to_dict() for row in report.rejected_evidence_rows
        ],
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "evidence_tsv": None if evidence_tsv_out is None else str(evidence_tsv_out),
            "peptide_tsv": None if peptide_tsv_out is None else str(peptide_tsv_out),
            "protein_group_tsv": None
            if protein_group_tsv_out is None
            else str(protein_group_tsv_out),
            "lfq_candidate_tsv": None
            if lfq_candidate_tsv_out is None
            else str(lfq_candidate_tsv_out),
            "rejected_tsv": None
            if rejected_tsv_out is None
            else str(rejected_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("maxquant-benchmark")
@click.argument(
    "evidence_txt", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--peptides-txt",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--protein-groups-txt",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--design-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--condition-a", type=str, default=None)
@click.option("--condition-b", type=str, default=None)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--protein-identity-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--filtering-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--lfq-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--differential-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def maxquant_benchmark_command(
    evidence_txt: Path,
    peptides_txt: Path,
    protein_groups_txt: Path,
    config_path: Path | None,
    design_tsv: Path | None,
    condition_a: str | None,
    condition_b: str | None,
    summary_tsv_out: Path | None,
    protein_identity_tsv_out: Path | None,
    filtering_tsv_out: Path | None,
    lfq_tsv_out: Path | None,
    differential_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Benchmark governed MaxQuant import and LFQ behavior against source tables."""

    design_entries: tuple[ExperimentalDesignEntry, ...] | None = None
    if design_tsv is not None:
        try:
            design_report = parse_experimental_design_table(design_tsv)
        except Exception as exc:  # noqa: BLE001
            raise click.ClickException(str(exc)) from exc
        if design_report.rejected_rows:
            raise click.ClickException(
                "design table contains rejected rows and cannot drive a MaxQuant benchmark differential comparison"
            )
        design_entries = tuple(design_report.accepted_entries)

    try:
        report = build_maxquant_benchmark_report(
            evidence_txt,
            peptides_txt_path=peptides_txt,
            protein_groups_txt_path=protein_groups_txt,
            config_path=config_path,
            design_entries=design_entries,
            condition_a=condition_a,
            condition_b=condition_b,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_maxquant_benchmark_summary_tsv(report),
        )
    if protein_identity_tsv_out is not None:
        _write_text_output(
            protein_identity_tsv_out,
            render_maxquant_protein_identity_comparison_tsv(report),
        )
    if filtering_tsv_out is not None:
        _write_text_output(
            filtering_tsv_out,
            render_maxquant_filtering_comparison_tsv(report),
        )
    if lfq_tsv_out is not None:
        _write_text_output(lfq_tsv_out, render_maxquant_lfq_comparison_tsv(report))
    if differential_tsv_out is not None:
        _write_text_output(
            differential_tsv_out,
            render_maxquant_differential_comparison_tsv(report),
        )

    payload = {
        "summary": report.summary.to_dict(),
        "protein_identity_comparison": report.protein_identity_comparison.to_dict(),
        "filtering_comparison_count": len(report.filtering_comparisons),
        "lfq_comparison_count": len(report.lfq_comparisons),
        "differential_comparison_count": len(report.differential_comparisons),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "protein_identity_tsv": None
            if protein_identity_tsv_out is None
            else str(protein_identity_tsv_out),
            "filtering_tsv": None
            if filtering_tsv_out is None
            else str(filtering_tsv_out),
            "lfq_tsv": None if lfq_tsv_out is None else str(lfq_tsv_out),
            "differential_tsv": None
            if differential_tsv_out is None
            else str(differential_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("diann-import")
@click.argument(
    "result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--precursor-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--protein-group-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option("--rejected-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def diann_import_command(
    result_tsv: Path,
    config_path: Path | None,
    summary_tsv_out: Path | None,
    precursor_tsv_out: Path | None,
    protein_group_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Import one DIA-NN report with explicit precursor and protein-group review."""
    try:
        report = build_diann_import_report(result_tsv, config_path=config_path)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_diann_summary_tsv(report.summary))
    if precursor_tsv_out is not None:
        _write_text_output(
            precursor_tsv_out,
            render_diann_precursor_tsv(report.precursor_rows),
        )
    if protein_group_tsv_out is not None:
        _write_text_output(
            protein_group_tsv_out,
            render_diann_protein_group_tsv(report.protein_group_rows),
        )
    if rejected_tsv_out is not None:
        _write_text_output(
            rejected_tsv_out,
            render_rejected_evidence_tsv(report.rejected_evidence_rows),
        )

    payload = {
        "summary": report.summary.to_dict(),
        "normalization": None
        if report.normalization is None
        else {
            "adapter": report.normalization.adapter_manifest.to_dict(),
            "accepted_rows": len(report.normalization.parse_report.accepted_records),
            "rejected_rows": len(report.normalization.parse_report.rejected_rows),
        },
        "parameter_report": None
        if report.parameter_report is None
        else report.parameter_report.to_dict(),
        "precursor_rows": [row.to_dict() for row in report.precursor_rows],
        "protein_group_rows": [row.to_dict() for row in report.protein_group_rows],
        "rejected_rows": [row.to_dict() for row in report.rejected_rows],
        "rejected_evidence_rows": [
            row.to_dict() for row in report.rejected_evidence_rows
        ],
        "dia_native_report": report.dia_native_report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "precursor_tsv": None
            if precursor_tsv_out is None
            else str(precursor_tsv_out),
            "protein_group_tsv": None
            if protein_group_tsv_out is None
            else str(protein_group_tsv_out),
            "rejected_tsv": None
            if rejected_tsv_out is None
            else str(rejected_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("diann-benchmark")
@click.argument(
    "result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--count-comparisons-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--protein-quantities-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def diann_benchmark_command(
    result_tsv: Path,
    config_path: Path | None,
    summary_tsv_out: Path | None,
    count_comparisons_tsv_out: Path | None,
    protein_quantities_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Benchmark governed DIA-NN import and protein matrix behavior against source rows."""

    try:
        report = build_diann_benchmark_report(
            result_tsv,
            config_path=config_path,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_diann_benchmark_summary_tsv(report))
    if count_comparisons_tsv_out is not None:
        _write_text_output(
            count_comparisons_tsv_out,
            render_diann_benchmark_count_comparisons_tsv(report),
        )
    if protein_quantities_tsv_out is not None:
        _write_text_output(
            protein_quantities_tsv_out,
            render_diann_benchmark_protein_quantities_tsv(report),
        )

    payload = {
        "summary": report.summary.to_dict(),
        "count_comparison_count": len(report.count_comparisons),
        "protein_quantity_comparison_count": len(report.protein_quantity_comparisons),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "count_comparisons_tsv": None
            if count_comparisons_tsv_out is None
            else str(count_comparisons_tsv_out),
            "protein_quantities_tsv": None
            if protein_quantities_tsv_out is None
            else str(protein_quantities_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("public-benchmark-runner")
@click.argument(
    "benchmark_path",
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    "--run-output-root",
    type=click.Path(path_type=Path, file_okay=False),
    default=Path("artifacts/public-benchmark-runs"),
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--failures-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def public_benchmark_runner_command(
    benchmark_path: Path,
    run_output_root: Path,
    summary_tsv_out: Path | None,
    failures_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Run one public benchmark descriptor or a whole public benchmark root."""

    try:
        if benchmark_path.is_dir():
            suite = run_public_benchmark_descriptor_suite(
                benchmark_path,
                output_root=run_output_root,
            )
            payload: Any = suite
        else:
            run_report = run_public_benchmark_descriptor(
                benchmark_path,
                output_root=run_output_root,
            )
            from bijux_proteomics.workflow.public_benchmark_runner import (
                PublicBenchmarkSuiteReport,
            )

            suite = PublicBenchmarkSuiteReport(
                benchmark_root=str(benchmark_path.parent),
                output_root=str(run_output_root),
                runs=(run_report,),
                passed_count=1 if run_report.status == "passed" else 0,
                failed_count=1 if run_report.status == "failed" else 0,
                note=(
                    "single benchmark descriptor wrapped as a one-row suite for "
                    "summary and failure rendering"
                ),
            )
            payload = run_report
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_public_benchmark_suite_summary_tsv(suite),
        )
    if failures_tsv_out is not None:
        _write_text_output(
            failures_tsv_out,
            render_public_benchmark_suite_failures_tsv(suite),
        )
    _emit_json(payload, out_path=out_path)


@cli.command("public-case-study")
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--report-dir",
    type=click.Path(path_type=Path, file_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def public_case_study_command(
    summary_tsv_out: Path | None,
    report_dir: Path | None,
    out_path: Path | None,
) -> None:
    """Run the owned public LFQ case study through final biological reporting."""

    try:
        report = build_lfq_cohort_biological_case_study_report()
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    export_manifest = None
    manifest_path = None
    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_public_biological_case_study_summary_tsv(report),
        )
    if report_dir is not None:
        export_manifest = export_public_biological_case_study_report(report, report_dir)
        manifest_path = report_dir / "public_case_study_manifest.json"
        manifest_path.write_text(
            export_manifest.to_stable_json() + "\n",
            encoding="utf-8",
        )

    payload = {
        "case_study_id": report.summary.case_study_id,
        "workflow_family": report.summary.workflow_family,
        "source_package_id": report.case_study.source_package_id,
        "public_dataset_identity": report.case_study.public_dataset_identity,
        "summary": report.summary.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "report_dir": None if report_dir is None else str(report_dir),
            "report_manifest_json": None
            if manifest_path is None
            else str(manifest_path),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("diann-precursor-matrix")
@click.argument(
    "result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--include-decoys/--exclude-decoys",
    default=False,
    show_default=True,
)
@click.option("--max-q-value", type=float, default=None)
@click.option(
    "--q-value-filter-timing",
    type=click.Choice(
        [timing.value for timing in DiaPrecursorQValueFilterTiming],
        case_sensitive=False,
    ),
    default=DiaPrecursorQValueFilterTiming.BEFORE_MATRIX_CONSTRUCTION.value,
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--matrix-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--qvalue-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--metadata-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def diann_precursor_matrix_command(
    result_tsv: Path,
    config_path: Path | None,
    include_decoys: bool,
    max_q_value: float | None,
    q_value_filter_timing: str,
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    qvalue_tsv_out: Path | None,
    metadata_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Build a DIA precursor-by-sample matrix from one DIA-NN report."""
    try:
        report = build_diann_precursor_matrix_report(
            result_tsv,
            config_path=config_path,
            policy=DiaPrecursorMatrixPolicy(
                include_decoys=include_decoys,
                max_q_value=max_q_value,
                q_value_filter_timing=DiaPrecursorQValueFilterTiming(
                    q_value_filter_timing
                ),
            ),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_dia_precursor_matrix_summary_tsv(report),
        )
    if matrix_tsv_out is not None:
        _write_text_output(
            matrix_tsv_out,
            render_dia_precursor_quantity_matrix_tsv(report),
        )
    if qvalue_tsv_out is not None:
        _write_text_output(
            qvalue_tsv_out,
            render_dia_precursor_q_value_matrix_tsv(report),
        )
    if metadata_tsv_out is not None:
        _write_text_output(
            metadata_tsv_out,
            render_dia_precursor_metadata_tsv(report),
        )

    payload = {
        "source_name": report.source_name,
        "sample_ids": list(report.sample_ids),
        "run_names": list(report.run_names),
        "policy": report.policy.to_dict(),
        "summary": report.summary.to_dict(),
        "rows": [row.to_dict() for row in report.rows],
        "metadata_entries": [entry.to_dict() for entry in report.metadata_entries],
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "matrix_tsv": None if matrix_tsv_out is None else str(matrix_tsv_out),
            "qvalue_tsv": None if qvalue_tsv_out is None else str(qvalue_tsv_out),
            "metadata_tsv": None if metadata_tsv_out is None else str(metadata_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("spectronaut-precursor-matrix")
@click.argument(
    "result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--include-decoys/--exclude-decoys",
    default=False,
    show_default=True,
)
@click.option("--max-q-value", type=float, default=None)
@click.option(
    "--q-value-filter-timing",
    type=click.Choice(
        [timing.value for timing in DiaPrecursorQValueFilterTiming],
        case_sensitive=False,
    ),
    default=DiaPrecursorQValueFilterTiming.BEFORE_MATRIX_CONSTRUCTION.value,
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--matrix-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--qvalue-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--metadata-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def spectronaut_precursor_matrix_command(
    result_tsv: Path,
    config_path: Path | None,
    include_decoys: bool,
    max_q_value: float | None,
    q_value_filter_timing: str,
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    qvalue_tsv_out: Path | None,
    metadata_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Build a DIA precursor-by-sample matrix from one Spectronaut report."""
    try:
        report = build_spectronaut_precursor_matrix_report(
            result_tsv,
            config_path=config_path,
            policy=DiaPrecursorMatrixPolicy(
                include_decoys=include_decoys,
                max_q_value=max_q_value,
                q_value_filter_timing=DiaPrecursorQValueFilterTiming(
                    q_value_filter_timing
                ),
            ),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_dia_precursor_matrix_summary_tsv(report),
        )
    if matrix_tsv_out is not None:
        _write_text_output(
            matrix_tsv_out,
            render_dia_precursor_quantity_matrix_tsv(report),
        )
    if qvalue_tsv_out is not None:
        _write_text_output(
            qvalue_tsv_out,
            render_dia_precursor_q_value_matrix_tsv(report),
        )
    if metadata_tsv_out is not None:
        _write_text_output(
            metadata_tsv_out,
            render_dia_precursor_metadata_tsv(report),
        )

    payload = {
        "source_name": report.source_name,
        "sample_ids": list(report.sample_ids),
        "run_names": list(report.run_names),
        "policy": report.policy.to_dict(),
        "summary": report.summary.to_dict(),
        "rows": [row.to_dict() for row in report.rows],
        "metadata_entries": [entry.to_dict() for entry in report.metadata_entries],
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "matrix_tsv": None if matrix_tsv_out is None else str(matrix_tsv_out),
            "qvalue_tsv": None if qvalue_tsv_out is None else str(qvalue_tsv_out),
            "metadata_tsv": None if metadata_tsv_out is None else str(metadata_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("diann-protein-matrix")
@click.argument(
    "result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--include-decoys/--exclude-decoys",
    default=False,
    show_default=True,
)
@click.option("--max-q-value", type=float, default=None)
@click.option(
    "--peptide-rollup",
    type=click.Choice([method.value for method in DiaPeptideRollupMethod]),
    default=DiaPeptideRollupMethod.MAX.value,
    show_default=True,
)
@click.option(
    "--target-kind",
    type=click.Choice([kind.value for kind in DiaProteinMatrixTargetKind]),
    default=DiaProteinMatrixTargetKind.PROTEIN_GROUP.value,
    show_default=True,
)
@click.option(
    "--shared-peptides",
    type=click.Choice([policy.value for policy in DiaSharedPeptidePolicy]),
    default=DiaSharedPeptidePolicy.INCLUDE.value,
    show_default=True,
)
@click.option(
    "--protein-rollup",
    type=click.Choice([method.value for method in DiaProteinRollupMethod]),
    default=DiaProteinRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--peptide-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--protein-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--rollup-evidence-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def diann_protein_matrix_command(
    result_tsv: Path,
    config_path: Path | None,
    include_decoys: bool,
    max_q_value: float | None,
    peptide_rollup: str,
    target_kind: str,
    shared_peptides: str,
    protein_rollup: str,
    summary_tsv_out: Path | None,
    peptide_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    rollup_evidence_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Build DIA peptide and protein matrices from one DIA-NN report."""
    try:
        peptide_report = build_diann_peptide_matrix_report(
            result_tsv,
            config_path=config_path,
            include_decoys=include_decoys,
            max_q_value=max_q_value,
            rollup_method=DiaPeptideRollupMethod(peptide_rollup),
        )
        protein_report = build_dia_protein_matrix_report(
            peptide_report,
            target_kind=DiaProteinMatrixTargetKind(target_kind),
            shared_peptide_policy=DiaSharedPeptidePolicy(shared_peptides),
            rollup_method=DiaProteinRollupMethod(protein_rollup),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_dia_protein_matrix_summary_tsv(protein_report),
        )
    if peptide_tsv_out is not None:
        _write_text_output(
            peptide_tsv_out,
            render_dia_peptide_quantity_matrix_tsv(peptide_report),
        )
    if protein_tsv_out is not None:
        _write_text_output(
            protein_tsv_out,
            render_dia_protein_quantity_matrix_tsv(protein_report),
        )
    if rollup_evidence_tsv_out is not None:
        _write_text_output(
            rollup_evidence_tsv_out,
            render_dia_protein_rollup_evidence_tsv(protein_report),
        )

    payload = {
        "source_name": protein_report.source_name,
        "sample_ids": list(protein_report.sample_ids),
        "peptide_rollup_method": peptide_report.rollup_method.value,
        "target_kind": protein_report.target_kind.value,
        "shared_peptide_policy": protein_report.shared_peptide_policy.value,
        "protein_rollup_method": protein_report.rollup_method.value,
        "peptide_summary": peptide_report.summary.to_dict(),
        "protein_summary": protein_report.summary.to_dict(),
        "peptide_rows": [row.to_dict() for row in peptide_report.rows],
        "protein_rows": [row.to_dict() for row in protein_report.rows],
        "rollup_evidence_entries": [
            entry.to_dict() for entry in protein_report.rollup_evidence_entries
        ],
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "peptide_tsv": None if peptide_tsv_out is None else str(peptide_tsv_out),
            "protein_tsv": None if protein_tsv_out is None else str(protein_tsv_out),
            "rollup_evidence_tsv": (
                None
                if rollup_evidence_tsv_out is None
                else str(rollup_evidence_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("spectronaut-protein-matrix")
@click.argument(
    "result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--include-decoys/--exclude-decoys",
    default=False,
    show_default=True,
)
@click.option("--max-q-value", type=float, default=None)
@click.option(
    "--peptide-rollup",
    type=click.Choice([method.value for method in DiaPeptideRollupMethod]),
    default=DiaPeptideRollupMethod.MAX.value,
    show_default=True,
)
@click.option(
    "--target-kind",
    type=click.Choice([kind.value for kind in DiaProteinMatrixTargetKind]),
    default=DiaProteinMatrixTargetKind.PROTEIN_GROUP.value,
    show_default=True,
)
@click.option(
    "--shared-peptides",
    type=click.Choice([policy.value for policy in DiaSharedPeptidePolicy]),
    default=DiaSharedPeptidePolicy.INCLUDE.value,
    show_default=True,
)
@click.option(
    "--protein-rollup",
    type=click.Choice([method.value for method in DiaProteinRollupMethod]),
    default=DiaProteinRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--peptide-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--protein-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--rollup-evidence-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def spectronaut_protein_matrix_command(
    result_tsv: Path,
    config_path: Path | None,
    include_decoys: bool,
    max_q_value: float | None,
    peptide_rollup: str,
    target_kind: str,
    shared_peptides: str,
    protein_rollup: str,
    summary_tsv_out: Path | None,
    peptide_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    rollup_evidence_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Build DIA peptide and protein matrices from one Spectronaut report."""
    try:
        peptide_report = build_spectronaut_peptide_matrix_report(
            result_tsv,
            config_path=config_path,
            include_decoys=include_decoys,
            max_q_value=max_q_value,
            rollup_method=DiaPeptideRollupMethod(peptide_rollup),
        )
        protein_report = build_spectronaut_protein_matrix_report(
            result_tsv,
            config_path=config_path,
            include_decoys=include_decoys,
            max_q_value=max_q_value,
            peptide_rollup_method=DiaPeptideRollupMethod(peptide_rollup),
            target_kind=DiaProteinMatrixTargetKind(target_kind),
            shared_peptide_policy=DiaSharedPeptidePolicy(shared_peptides),
            protein_rollup_method=DiaProteinRollupMethod(protein_rollup),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_dia_protein_matrix_summary_tsv(protein_report),
        )
    if peptide_tsv_out is not None:
        _write_text_output(
            peptide_tsv_out,
            render_dia_peptide_quantity_matrix_tsv(peptide_report),
        )
    if protein_tsv_out is not None:
        _write_text_output(
            protein_tsv_out,
            render_dia_protein_quantity_matrix_tsv(protein_report),
        )
    if rollup_evidence_tsv_out is not None:
        _write_text_output(
            rollup_evidence_tsv_out,
            render_dia_protein_rollup_evidence_tsv(protein_report),
        )

    payload = {
        "source_name": protein_report.source_name,
        "sample_ids": list(protein_report.sample_ids),
        "peptide_rollup_method": peptide_report.rollup_method.value,
        "target_kind": protein_report.target_kind.value,
        "shared_peptide_policy": protein_report.shared_peptide_policy.value,
        "protein_rollup_method": protein_report.rollup_method.value,
        "peptide_summary": peptide_report.summary.to_dict(),
        "protein_summary": protein_report.summary.to_dict(),
        "peptide_rows": [row.to_dict() for row in peptide_report.rows],
        "protein_rows": [row.to_dict() for row in protein_report.rows],
        "rollup_evidence_entries": [
            entry.to_dict() for entry in protein_report.rollup_evidence_entries
        ],
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "peptide_tsv": None if peptide_tsv_out is None else str(peptide_tsv_out),
            "protein_tsv": None if protein_tsv_out is None else str(protein_tsv_out),
            "rollup_evidence_tsv": (
                None
                if rollup_evidence_tsv_out is None
                else str(rollup_evidence_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("diann-run-qc")
@click.argument(
    "result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--include-decoys/--exclude-decoys",
    default=False,
    show_default=True,
)
@click.option("--max-q-value", type=float, default=None)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--run-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--intensity-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--correlation-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option("--outlier-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def diann_run_qc_command(
    result_tsv: Path,
    config_path: Path | None,
    include_decoys: bool,
    max_q_value: float | None,
    summary_tsv_out: Path | None,
    run_tsv_out: Path | None,
    intensity_tsv_out: Path | None,
    correlation_tsv_out: Path | None,
    outlier_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Build DIA run-level QC from one DIA-NN report."""
    try:
        report = build_diann_run_qc_report(
            result_tsv,
            config_path=config_path,
            include_decoys=include_decoys,
            max_q_value=max_q_value,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_dia_run_qc_summary_tsv(report))
    if run_tsv_out is not None:
        _write_text_output(run_tsv_out, render_dia_run_qc_run_table_tsv(report))
    if intensity_tsv_out is not None:
        _write_text_output(
            intensity_tsv_out,
            render_dia_run_qc_intensity_distribution_tsv(report),
        )
    if correlation_tsv_out is not None:
        _write_text_output(
            correlation_tsv_out,
            render_dia_run_qc_correlation_tsv(report),
        )
    if outlier_tsv_out is not None:
        _write_text_output(outlier_tsv_out, render_dia_run_qc_outlier_tsv(report))

    payload = {
        "source_name": report.source_name,
        "summary": report.summary.to_dict(),
        "run_entries": [entry.to_dict() for entry in report.run_entries],
        "intensity_distribution": [
            entry.to_dict() for entry in report.intensity_distribution
        ],
        "pairwise_correlations": [
            entry.to_dict() for entry in report.pairwise_correlations
        ],
        "outlier_runs": [entry.to_dict() for entry in report.outlier_runs],
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "run_tsv": None if run_tsv_out is None else str(run_tsv_out),
            "intensity_tsv": (
                None if intensity_tsv_out is None else str(intensity_tsv_out)
            ),
            "correlation_tsv": (
                None if correlation_tsv_out is None else str(correlation_tsv_out)
            ),
            "outlier_tsv": (
                None if outlier_tsv_out is None else str(outlier_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("diann-library-coverage")
@click.argument(
    "result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "library_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--include-decoys/--exclude-decoys",
    default=False,
    show_default=True,
)
@click.option("--max-q-value", type=float, default=None)
@click.option(
    "--shared-peptides",
    type=click.Choice([policy.value for policy in DiaSharedPeptidePolicy]),
    default=DiaSharedPeptidePolicy.INCLUDE.value,
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--sample-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--condition-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option("--peptide-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--protein-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--outside-library-peptide-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--outside-library-protein-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def diann_library_coverage_command(
    result_tsv: Path,
    library_path: Path,
    design_path: Path | None,
    include_decoys: bool,
    max_q_value: float | None,
    shared_peptides: str,
    summary_tsv_out: Path | None,
    sample_tsv_out: Path | None,
    condition_tsv_out: Path | None,
    peptide_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    outside_library_peptide_tsv_out: Path | None,
    outside_library_protein_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Compare DIA-NN observations against spectral-library peptide and protein scope."""
    try:
        report = build_diann_library_coverage_report(
            result_tsv,
            library_path,
            design_path=design_path,
            include_decoys=include_decoys,
            max_q_value=max_q_value,
            shared_peptide_policy=DiaSharedPeptidePolicy(shared_peptides),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_dia_library_coverage_summary_tsv(report),
        )
    if sample_tsv_out is not None:
        _write_text_output(
            sample_tsv_out,
            render_dia_library_coverage_sample_tsv(report),
        )
    if condition_tsv_out is not None:
        _write_text_output(
            condition_tsv_out,
            render_dia_library_coverage_condition_tsv(report),
        )
    if peptide_tsv_out is not None:
        _write_text_output(
            peptide_tsv_out,
            render_dia_library_coverage_peptide_tsv(report),
        )
    if protein_tsv_out is not None:
        _write_text_output(
            protein_tsv_out,
            render_dia_library_coverage_protein_tsv(report),
        )
    if outside_library_peptide_tsv_out is not None:
        _write_text_output(
            outside_library_peptide_tsv_out,
            render_dia_library_coverage_observed_outside_peptide_tsv(report),
        )
    if outside_library_protein_tsv_out is not None:
        _write_text_output(
            outside_library_protein_tsv_out,
            render_dia_library_coverage_observed_outside_protein_tsv(report),
        )

    payload = {
        "source_name": report.source_name,
        "library_source_format": report.library_source_format,
        "summary": report.summary.to_dict(),
        "sample_entries": [entry.to_dict() for entry in report.sample_entries],
        "condition_entries": [entry.to_dict() for entry in report.condition_entries],
        "peptide_entries": [entry.to_dict() for entry in report.peptide_entries],
        "protein_entries": [entry.to_dict() for entry in report.protein_entries],
        "observed_outside_library_peptide_entries": [
            entry.to_dict() for entry in report.observed_outside_library_peptide_entries
        ],
        "observed_outside_library_protein_entries": [
            entry.to_dict() for entry in report.observed_outside_library_protein_entries
        ],
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "sample_tsv": None if sample_tsv_out is None else str(sample_tsv_out),
            "condition_tsv": (
                None if condition_tsv_out is None else str(condition_tsv_out)
            ),
            "peptide_tsv": None if peptide_tsv_out is None else str(peptide_tsv_out),
            "protein_tsv": None if protein_tsv_out is None else str(protein_tsv_out),
            "outside_library_peptide_tsv": (
                None
                if outside_library_peptide_tsv_out is None
                else str(outside_library_peptide_tsv_out)
            ),
            "outside_library_protein_tsv": (
                None
                if outside_library_protein_tsv_out is None
                else str(outside_library_protein_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("transition-qc")
@click.argument(
    "transition_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--weak-detection-fraction-threshold",
    type=float,
    default=0.5,
    show_default=True,
)
@click.option(
    "--weak-relative-share-threshold",
    type=float,
    default=0.1,
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--transition-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--sample-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--weak-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def transition_qc_command(
    transition_table: Path,
    weak_detection_fraction_threshold: float,
    weak_relative_share_threshold: float,
    summary_tsv_out: Path | None,
    transition_tsv_out: Path | None,
    sample_tsv_out: Path | None,
    weak_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Review transition-level quantitative evidence from one canonical table."""
    try:
        report = build_transition_qc_report_from_table(
            transition_table,
            weak_detection_fraction_threshold=weak_detection_fraction_threshold,
            weak_relative_share_threshold=weak_relative_share_threshold,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_transition_qc_summary_tsv(report))
    if transition_tsv_out is not None:
        _write_text_output(
            transition_tsv_out,
            render_transition_qc_transition_tsv(report),
        )
    if sample_tsv_out is not None:
        _write_text_output(sample_tsv_out, render_transition_qc_sample_tsv(report))
    if weak_tsv_out is not None:
        _write_text_output(weak_tsv_out, render_transition_qc_weak_tsv(report))

    payload = {
        "source_name": report.source_name,
        "sample_ids": list(report.sample_ids),
        "summary": report.summary.to_dict(),
        "entries": [entry.to_dict() for entry in report.entries],
        "weak_transitions": [entry.to_dict() for entry in report.weak_transitions],
        "note": report.note,
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "transition_tsv": (
                None if transition_tsv_out is None else str(transition_tsv_out)
            ),
            "sample_tsv": None if sample_tsv_out is None else str(sample_tsv_out),
            "weak_tsv": None if weak_tsv_out is None else str(weak_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("targeted-target-matrix")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--source-kind",
    type=click.Choice([kind.value for kind in TargetedResultSourceKind]),
    required=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--observation-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--target-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--sample-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--flagged-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--retained-transition-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option(
    "--excluded-transition-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option("--missingness-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def targeted_target_matrix_command(
    input_path: Path,
    source_kind: str,
    summary_tsv_out: Path | None,
    observation_tsv_out: Path | None,
    target_tsv_out: Path | None,
    sample_tsv_out: Path | None,
    flagged_tsv_out: Path | None,
    retained_transition_tsv_out: Path | None,
    excluded_transition_tsv_out: Path | None,
    missingness_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Import targeted assay results and build a precursor-target matrix review."""
    result = _run_orchestrated_workflow(
        TargetedWorkflowConfig(
            input_tsv_path=input_path,
            source_kind=TargetedResultSourceKind(source_kind),
            stage=TargetedWorkflowStage.MATRIX,
        )
    )
    import_report = result.source_report
    matrix_report = result.report
    if import_report is None:
        raise click.ClickException("workflow source report was not produced")

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_targeted_matrix_summary_tsv(matrix_report))
    if observation_tsv_out is not None:
        _write_text_output(
            observation_tsv_out,
            render_targeted_result_observation_tsv(import_report),
        )
    if target_tsv_out is not None:
        _write_text_output(target_tsv_out, render_targeted_matrix_target_tsv(matrix_report))
    if sample_tsv_out is not None:
        _write_text_output(sample_tsv_out, render_targeted_matrix_sample_tsv(matrix_report))
    if flagged_tsv_out is not None:
        _write_text_output(flagged_tsv_out, render_targeted_matrix_flagged_tsv(matrix_report))
    if retained_transition_tsv_out is not None:
        _write_text_output(
            retained_transition_tsv_out,
            render_targeted_matrix_retained_transition_tsv(matrix_report),
        )
    if excluded_transition_tsv_out is not None:
        _write_text_output(
            excluded_transition_tsv_out,
            render_targeted_matrix_excluded_transition_tsv(matrix_report),
        )
    if missingness_tsv_out is not None:
        _write_text_output(
            missingness_tsv_out,
            render_targeted_matrix_missingness_tsv(matrix_report),
        )

    payload = {
        "source_kind": import_report.source_kind.value,
        "source_name": matrix_report.source_name,
        "import_summary": import_report.summary.to_dict(),
        "matrix_summary": matrix_report.summary.to_dict(),
        "observations": [item.to_dict() for item in import_report.observations],
        "targets": [row.to_dict() for row in matrix_report.rows],
        "retained_transitions": [
            item.to_dict() for item in matrix_report.retained_transitions
        ],
        "excluded_transitions": [
            item.to_dict() for item in matrix_report.excluded_transitions
        ],
        "missingness": [item.to_dict() for item in matrix_report.missingness],
        "note": matrix_report.note,
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "observation_tsv": (
                None if observation_tsv_out is None else str(observation_tsv_out)
            ),
            "target_tsv": None if target_tsv_out is None else str(target_tsv_out),
            "sample_tsv": None if sample_tsv_out is None else str(sample_tsv_out),
            "flagged_tsv": None if flagged_tsv_out is None else str(flagged_tsv_out),
            "retained_transition_tsv": (
                None
                if retained_transition_tsv_out is None
                else str(retained_transition_tsv_out)
            ),
            "excluded_transition_tsv": (
                None
                if excluded_transition_tsv_out is None
                else str(excluded_transition_tsv_out)
            ),
            "missingness_tsv": (
                None if missingness_tsv_out is None else str(missingness_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("targeted-assay-qc")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--source-kind",
    type=click.Choice([kind.value for kind in TargetedResultSourceKind]),
    required=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--target-qc-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--transition-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--transition-qc-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option(
    "--fragment-ratio-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--retention-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--replicate-cv-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--unreliable-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def targeted_assay_qc_command(
    input_path: Path,
    design_path: Path,
    source_kind: str,
    summary_tsv_out: Path | None,
    target_qc_tsv_out: Path | None,
    transition_tsv_out: Path | None,
    transition_qc_tsv_out: Path | None,
    fragment_ratio_tsv_out: Path | None,
    retention_tsv_out: Path | None,
    replicate_cv_tsv_out: Path | None,
    unreliable_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Import targeted assay results and build assay-QC review ledgers."""
    result = _run_orchestrated_workflow(
        TargetedWorkflowConfig(
            input_tsv_path=input_path,
            source_kind=TargetedResultSourceKind(source_kind),
            stage=TargetedWorkflowStage.ASSAY_QC,
            design_tsv_path=design_path,
        )
    )
    import_report = result.source_report
    assay_qc_report = result.report
    if import_report is None:
        raise click.ClickException("workflow source report was not produced")

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_targeted_assay_qc_summary_tsv(assay_qc_report))
    if target_qc_tsv_out is not None:
        _write_text_output(
            target_qc_tsv_out,
            render_targeted_assay_qc_target_tsv(assay_qc_report),
        )
    if transition_tsv_out is not None:
        _write_text_output(
            transition_tsv_out,
            render_targeted_assay_qc_transition_tsv(assay_qc_report),
        )
    if transition_qc_tsv_out is not None:
        _write_text_output(
            transition_qc_tsv_out,
            render_targeted_assay_qc_transition_qc_tsv(assay_qc_report),
        )
    if fragment_ratio_tsv_out is not None:
        _write_text_output(
            fragment_ratio_tsv_out,
            render_targeted_assay_qc_fragment_ratio_tsv(assay_qc_report),
        )
    if retention_tsv_out is not None:
        _write_text_output(
            retention_tsv_out,
            render_targeted_assay_qc_retention_tsv(assay_qc_report),
        )
    if replicate_cv_tsv_out is not None:
        _write_text_output(
            replicate_cv_tsv_out,
            render_targeted_assay_qc_replicate_cv_tsv(assay_qc_report),
        )
    if unreliable_tsv_out is not None:
        _write_text_output(
            unreliable_tsv_out,
            render_targeted_assay_qc_unreliable_tsv(assay_qc_report),
        )

    payload = {
        "source_kind": import_report.source_kind.value,
        "source_name": assay_qc_report.source_name,
        "import_summary": import_report.summary.to_dict(),
        "design_summary": {
            "accepted_entry_count": result.design_row_count,
            "rejected_row_count": 0,
        },
        "assay_qc_summary": assay_qc_report.summary.to_dict(),
        "target_qc": [entry.to_dict() for entry in assay_qc_report.target_qc],
        "transition_consistency": [
            entry.to_dict() for entry in assay_qc_report.transition_consistency
        ],
        "transition_qc": [entry.to_dict() for entry in assay_qc_report.transition_qc],
        "fragment_ratios": [entry.to_dict() for entry in assay_qc_report.fragment_ratios],
        "retention_time_consistency": [
            entry.to_dict() for entry in assay_qc_report.retention_time_consistency
        ],
        "replicate_cv": [entry.to_dict() for entry in assay_qc_report.replicate_cv],
        "unreliable_targets": [
            entry.to_dict() for entry in assay_qc_report.unreliable_targets
        ],
        "note": assay_qc_report.note,
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "target_qc_tsv": (
                None if target_qc_tsv_out is None else str(target_qc_tsv_out)
            ),
            "transition_tsv": (
                None if transition_tsv_out is None else str(transition_tsv_out)
            ),
            "transition_qc_tsv": (
                None
                if transition_qc_tsv_out is None
                else str(transition_qc_tsv_out)
            ),
            "fragment_ratio_tsv": (
                None if fragment_ratio_tsv_out is None else str(fragment_ratio_tsv_out)
            ),
            "retention_tsv": None if retention_tsv_out is None else str(retention_tsv_out),
            "replicate_cv_tsv": (
                None
                if replicate_cv_tsv_out is None
                else str(replicate_cv_tsv_out)
            ),
            "unreliable_tsv": (
                None if unreliable_tsv_out is None else str(unreliable_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("dia-differential")
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--source-kind",
    type=click.Choice([kind.value for kind in DiaDifferentialSourceKind]),
    required=True,
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--max-q-value", type=float, default=0.01, show_default=True)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option("--design-batch-field", default="batch", show_default=True)
@click.option("--design-pairing-field", default=None)
@click.option("--design-covariate", "design_covariates", multiple=True)
@click.option("--matrix-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--normalized-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--differential-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--qc-summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--design-matrix-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--design-coefficients-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--volcano-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--volcano-json-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--volcano-svg-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--volcano-html-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--volcano-adjusted-p-value-threshold",
    type=float,
    default=0.1,
    show_default=True,
)
@click.option(
    "--volcano-absolute-log2-fold-change-threshold",
    type=float,
    default=1.0,
    show_default=True,
)
@click.option(
    "--volcano-top-label-count",
    type=int,
    default=10,
    show_default=True,
)
@click.option(
    "--sample-balance-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def dia_differential_command(
    input_path: Path,
    design_path: Path,
    source_kind: str,
    config_path: Path | None,
    max_q_value: float,
    normalization: str,
    condition_a: str | None,
    condition_b: str | None,
    design_batch_field: str,
    design_pairing_field: str | None,
    design_covariates: tuple[str, ...],
    matrix_tsv_out: Path | None,
    normalized_matrix_tsv_out: Path | None,
    differential_tsv_out: Path | None,
    qc_summary_tsv_out: Path | None,
    design_matrix_tsv_out: Path | None,
    design_coefficients_tsv_out: Path | None,
    volcano_tsv_out: Path | None,
    volcano_json_out: Path | None,
    volcano_svg_out: Path | None,
    volcano_html_out: Path | None,
    volcano_adjusted_p_value_threshold: float,
    volcano_absolute_log2_fold_change_threshold: float,
    volcano_top_label_count: int,
    sample_balance_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Run DIA-native differential analysis from DIA-NN or Spectronaut evidence."""
    try:
        design_report = parse_experimental_design_table(design_path)
        if design_report.rejected_rows:
            raise click.ClickException("design table contains rejected rows")
        selected_source = DiaDifferentialSourceKind(source_kind)
        if selected_source is DiaDifferentialSourceKind.DIANN:
            report = build_diann_differential_analysis_report(
                input_path,
                design_report.accepted_entries,
                config_path=config_path,
                max_q_value=max_q_value,
                normalization_method=NormalizationMethod(normalization),
                condition_a=condition_a,
                condition_b=condition_b,
                batch_field=design_batch_field,
                covariate_fields=tuple(dict.fromkeys(design_covariates)),
                pairing_field=design_pairing_field,
            )
        else:
            report = build_spectronaut_differential_analysis_report(
                input_path,
                design_report.accepted_entries,
                config_path=config_path,
                max_q_value=max_q_value,
                normalization_method=NormalizationMethod(normalization),
                condition_a=condition_a,
                condition_b=condition_b,
                batch_field=design_batch_field,
                covariate_fields=tuple(dict.fromkeys(design_covariates)),
                pairing_field=design_pairing_field,
            )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    volcano_plot = report.volcano_plot
    volcano_review = None
    if (
        volcano_tsv_out is not None
        or volcano_json_out is not None
        or volcano_svg_out is not None
        or volcano_html_out is not None
    ):
        if report.differential_abundance_report is None:
            raise click.ClickException(
                "volcano export requires a resolvable contrast or exactly two conditions"
            )
        volcano_plot = build_dia_differential_volcano_plot(
            report.differential_abundance_report,
            protein_refs_by_entity=report.input_report.table.entity_protein_refs,
            adjusted_p_value_threshold=volcano_adjusted_p_value_threshold,
            absolute_log2_fold_change_threshold=(
                volcano_absolute_log2_fold_change_threshold
            ),
        )
        volcano_review = build_dia_volcano_review(
            volcano_plot,
            policy=_build_volcano_review_policy(
                adjusted_p_value_threshold=volcano_adjusted_p_value_threshold,
                absolute_log2_fold_change_threshold=(
                    volcano_absolute_log2_fold_change_threshold
                ),
                top_label_count=volcano_top_label_count,
            ),
        )

    if matrix_tsv_out is not None:
        export_dia_differential_matrix_tsv(report.input_report.table, matrix_tsv_out)
    if normalized_matrix_tsv_out is not None:
        export_dia_differential_matrix_tsv(report.normalized_table, normalized_matrix_tsv_out)
    if differential_tsv_out is not None:
        export_dia_differential_results_tsv(report, differential_tsv_out)
    if qc_summary_tsv_out is not None:
        export_dia_differential_qc_summary_tsv(report, qc_summary_tsv_out)
    if design_matrix_tsv_out is not None:
        export_quant_design_matrix_tsv(report.design_matrix, design_matrix_tsv_out)
    if design_coefficients_tsv_out is not None:
        export_quant_design_model_coefficients_tsv(
            report.design_model_fit,
            design_coefficients_tsv_out,
        )
    if sample_balance_tsv_out is not None:
        export_dia_normalization_balance_plot_tsv(
            report.normalization_balance_plot,
            sample_balance_tsv_out,
        )
    if volcano_tsv_out is not None:
        assert volcano_plot is not None
        export_dia_differential_volcano_plot_tsv(volcano_plot, volcano_tsv_out)
    if volcano_review is not None:
        _export_volcano_review_assets(
            review_report=volcano_review,
            json_out=volcano_json_out,
            svg_out=volcano_svg_out,
            html_out=volcano_html_out,
        )

    payload = {
        "source_kind": report.input_report.source_kind.value,
        "source_name": report.input_report.source_name,
        "matrix_summary": report.input_report.matrix_summary.to_dict(),
        "table": report.input_report.table.to_dict(),
        "normalized_table": report.normalized_table.to_dict(),
        "normalization_comparison": report.normalization_comparison.to_dict(),
        "design_matrix": report.design_matrix.to_dict(),
        "design_model_fit": report.design_model_fit.to_dict(),
        "qc_summary": report.qc_summary.to_dict(),
        "differential_abundance": (
            report.differential_abundance_report.to_dict()
            if report.differential_abundance_report is not None
            else None
        ),
        "differential_abundance_multi_condition": (
            report.differential_abundance_multi_condition_report.to_dict()
            if report.differential_abundance_multi_condition_report is not None
            else None
        ),
        "normalization_balance_plot": report.normalization_balance_plot.to_dict(),
        "volcano_plot": None if volcano_plot is None else volcano_plot.to_dict(),
        "volcano_review": (
            None if volcano_review is None else volcano_review.to_dict()
        ),
        "note": report.note,
        "outputs": {
            "matrix_tsv": None if matrix_tsv_out is None else str(matrix_tsv_out),
            "normalized_matrix_tsv": (
                None if normalized_matrix_tsv_out is None else str(normalized_matrix_tsv_out)
            ),
            "differential_tsv": (
                None if differential_tsv_out is None else str(differential_tsv_out)
            ),
            "qc_summary_tsv": (
                None if qc_summary_tsv_out is None else str(qc_summary_tsv_out)
            ),
            "design_matrix_tsv": (
                None if design_matrix_tsv_out is None else str(design_matrix_tsv_out)
            ),
            "design_coefficients_tsv": (
                None
                if design_coefficients_tsv_out is None
                else str(design_coefficients_tsv_out)
            ),
            "volcano_tsv": None if volcano_tsv_out is None else str(volcano_tsv_out),
            "volcano_json": (
                None if volcano_json_out is None else str(volcano_json_out)
            ),
            "volcano_svg": None if volcano_svg_out is None else str(volcano_svg_out),
            "volcano_html": (
                None if volcano_html_out is None else str(volcano_html_out)
            ),
            "sample_balance_tsv": (
                None if sample_balance_tsv_out is None else str(sample_balance_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("dia-dda-compare")
@click.argument(
    "diann_report_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "dda_psm_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--max-q-value", type=float, default=0.05, show_default=True)
@click.option(
    "--dia-differential-tsv",
    "dia_differential_tsv_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--dda-differential-tsv",
    "dda_differential_tsv_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--differential-significance-threshold",
    type=float,
    default=0.05,
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--protein-overlap-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--peptide-overlap-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--correlation-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--exclusive-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--conflicts-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--differential-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def dia_dda_compare_command(
    diann_report_path: Path,
    dda_psm_path: Path,
    max_q_value: float,
    dia_differential_tsv_path: Path | None,
    dda_differential_tsv_path: Path | None,
    differential_significance_threshold: float,
    summary_tsv_out: Path | None,
    protein_overlap_tsv_out: Path | None,
    peptide_overlap_tsv_out: Path | None,
    correlation_tsv_out: Path | None,
    exclusive_tsv_out: Path | None,
    conflicts_tsv_out: Path | None,
    differential_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Compare DIA-NN and DDA evidence, conflicts, and optional differential results."""
    try:
        comparison_report = build_diann_vs_dda_psm_comparison_report(
            diann_report_path,
            dda_psm_path,
            max_q_value=max_q_value,
            dia_differential_tsv_path=dia_differential_tsv_path,
            dda_differential_tsv_path=dda_differential_tsv_path,
            differential_significance_threshold=differential_significance_threshold,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_dia_dda_comparison_summary_tsv(comparison_report),
        )
    if protein_overlap_tsv_out is not None:
        _write_text_output(
            protein_overlap_tsv_out,
            render_dia_dda_protein_overlap_tsv(comparison_report),
        )
    if peptide_overlap_tsv_out is not None:
        _write_text_output(
            peptide_overlap_tsv_out,
            render_dia_dda_peptide_overlap_tsv(comparison_report),
        )
    if correlation_tsv_out is not None:
        _write_text_output(
            correlation_tsv_out,
            render_dia_dda_shared_intensity_correlation_tsv(comparison_report),
        )
    if exclusive_tsv_out is not None:
        _write_text_output(
            exclusive_tsv_out,
            render_dia_dda_exclusive_evidence_tsv(comparison_report),
        )
    if conflicts_tsv_out is not None:
        _write_text_output(
            conflicts_tsv_out,
            render_dia_dda_conflicting_evidence_tsv(comparison_report),
        )
    if differential_tsv_out is not None:
        _write_text_output(
            differential_tsv_out,
            render_dia_dda_differential_comparison_tsv(comparison_report),
        )

    payload = {
        "dia_source_name": comparison_report.dia_source_name,
        "dda_source_name": comparison_report.dda_source_name,
        "summary": comparison_report.summary.to_dict(),
        "protein_overlap": [entry.to_dict() for entry in comparison_report.protein_overlap],
        "peptide_overlap": [entry.to_dict() for entry in comparison_report.peptide_overlap],
        "shared_intensity_correlation": [
            entry.to_dict() for entry in comparison_report.shared_intensity_correlation
        ],
        "exclusive_evidence": [
            entry.to_dict() for entry in comparison_report.exclusive_evidence
        ],
        "conflicting_evidence": [
            entry.to_dict() for entry in comparison_report.conflicting_evidence
        ],
        "differential_comparison": [
            entry.to_dict() for entry in comparison_report.differential_comparison
        ],
        "note": comparison_report.note,
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "protein_overlap_tsv": (
                None
                if protein_overlap_tsv_out is None
                else str(protein_overlap_tsv_out)
            ),
            "peptide_overlap_tsv": (
                None
                if peptide_overlap_tsv_out is None
                else str(peptide_overlap_tsv_out)
            ),
            "correlation_tsv": (
                None if correlation_tsv_out is None else str(correlation_tsv_out)
            ),
            "exclusive_tsv": (
                None if exclusive_tsv_out is None else str(exclusive_tsv_out)
            ),
            "conflicts_tsv": (
                None if conflicts_tsv_out is None else str(conflicts_tsv_out)
            ),
            "differential_tsv": (
                None
                if differential_tsv_out is None
                else str(differential_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("target-panel-review")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "panel_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--source-kind",
    type=click.Choice([kind.value for kind in TargetPanelSourceKind]),
    required=True,
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--include-decoys/--exclude-decoys",
    default=False,
    show_default=True,
)
@click.option("--max-q-value", type=float, default=None)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--target-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--missing-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--intensity-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--matrix-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def target_panel_review_command(
    input_path: Path,
    panel_path: Path,
    source_kind: str,
    config_path: Path | None,
    include_decoys: bool,
    max_q_value: float | None,
    summary_tsv_out: Path | None,
    target_tsv_out: Path | None,
    missing_tsv_out: Path | None,
    intensity_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Review a user-defined peptide or protein panel against DIA or LFQ matrices."""
    try:
        selected_source = TargetPanelSourceKind(source_kind)
        if selected_source is TargetPanelSourceKind.DIA_PEPTIDE:
            report = build_diann_peptide_target_panel_report(
                input_path,
                panel_path,
                config_path=config_path,
                include_decoys=include_decoys,
                max_q_value=max_q_value,
            )
        elif selected_source is TargetPanelSourceKind.DIA_PROTEIN:
            report = build_diann_protein_target_panel_report(
                input_path,
                panel_path,
                config_path=config_path,
                include_decoys=include_decoys,
                max_q_value=max_q_value,
            )
        elif selected_source is TargetPanelSourceKind.LFQ_PEPTIDE:
            report = build_lfq_peptide_target_panel_report(input_path, panel_path)
        elif selected_source is TargetPanelSourceKind.LFQ_PROTEIN:
            report = build_lfq_protein_target_panel_report(input_path, panel_path)
        else:
            report = build_lfq_protein_lfq_target_panel_report(input_path, panel_path)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_target_panel_summary_tsv(report))
    if target_tsv_out is not None:
        _write_text_output(target_tsv_out, render_target_panel_target_tsv(report))
    if missing_tsv_out is not None:
        _write_text_output(missing_tsv_out, render_target_panel_missing_tsv(report))
    if intensity_tsv_out is not None:
        _write_text_output(
            intensity_tsv_out,
            render_target_panel_intensity_tsv(report),
        )
    if matrix_tsv_out is not None:
        _write_text_output(matrix_tsv_out, render_target_panel_matrix_tsv(report))

    payload = {
        "source_kind": report.source_kind.value,
        "source_name": report.source_name,
        "sample_ids": list(report.sample_ids),
        "summary": report.summary.to_dict(),
        "matched_targets": [entry.to_dict() for entry in report.matched_targets],
        "missing_targets": [entry.to_dict() for entry in report.missing_targets],
        "filtered_rows": [row.to_dict() for row in report.filtered_rows],
        "intensity_entries": [entry.to_dict() for entry in report.intensity_entries],
        "note": report.note,
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "target_tsv": None if target_tsv_out is None else str(target_tsv_out),
            "missing_tsv": None if missing_tsv_out is None else str(missing_tsv_out),
            "intensity_tsv": (
                None if intensity_tsv_out is None else str(intensity_tsv_out)
            ),
            "matrix_tsv": None if matrix_tsv_out is None else str(matrix_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("spectronaut-import")
@click.argument(
    "result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--precursor-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--precursor-quantity-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option(
    "--protein-group-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option(
    "--protein-group-quantity-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--rejected-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def spectronaut_import_command(
    result_tsv: Path,
    config_path: Path | None,
    summary_tsv_out: Path | None,
    precursor_tsv_out: Path | None,
    precursor_quantity_tsv_out: Path | None,
    protein_group_tsv_out: Path | None,
    protein_group_quantity_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Import one Spectronaut report with explicit precursor and protein-group review."""
    try:
        report = build_spectronaut_import_report(result_tsv, config_path=config_path)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_spectronaut_summary_tsv(report.summary),
        )
    if precursor_tsv_out is not None:
        _write_text_output(
            precursor_tsv_out,
            render_spectronaut_precursor_tsv(report.precursor_rows),
        )
    if precursor_quantity_tsv_out is not None:
        _write_text_output(
            precursor_quantity_tsv_out,
            render_spectronaut_precursor_quantity_tsv(report.precursor_quantity_rows),
        )
    if protein_group_tsv_out is not None:
        _write_text_output(
            protein_group_tsv_out,
            render_spectronaut_protein_group_tsv(report.protein_group_rows),
        )
    if protein_group_quantity_tsv_out is not None:
        _write_text_output(
            protein_group_quantity_tsv_out,
            render_spectronaut_protein_group_quantity_tsv(
                report.protein_group_quantity_rows
            ),
        )
    if rejected_tsv_out is not None:
        _write_text_output(
            rejected_tsv_out,
            render_rejected_evidence_tsv(report.rejected_evidence_rows),
        )

    payload = {
        "summary": report.summary.to_dict(),
        "normalization": {
            "adapter": report.normalization.adapter_manifest.to_dict(),
            "accepted_rows": len(report.normalization.parse_report.accepted_records),
            "rejected_rows": len(report.normalization.parse_report.rejected_rows),
        },
        "parameter_report": None
        if report.parameter_report is None
        else report.parameter_report.to_dict(),
        "precursor_evidence_rows": [
            row.to_dict() for row in report.precursor_evidence_rows
        ],
        "precursor_rows": [row.to_dict() for row in report.precursor_rows],
        "precursor_quantity_rows": [
            row.to_dict() for row in report.precursor_quantity_rows
        ],
        "protein_group_rows": [row.to_dict() for row in report.protein_group_rows],
        "protein_group_quantity_rows": [
            row.to_dict() for row in report.protein_group_quantity_rows
        ],
        "rejected_evidence_rows": [
            row.to_dict() for row in report.rejected_evidence_rows
        ],
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "precursor_tsv": None
            if precursor_tsv_out is None
            else str(precursor_tsv_out),
            "precursor_quantity_tsv": None
            if precursor_quantity_tsv_out is None
            else str(precursor_quantity_tsv_out),
            "protein_group_tsv": None
            if protein_group_tsv_out is None
            else str(protein_group_tsv_out),
            "protein_group_quantity_tsv": None
            if protein_group_quantity_tsv_out is None
            else str(protein_group_quantity_tsv_out),
            "rejected_tsv": None
            if rejected_tsv_out is None
            else str(rejected_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("openms-import")
@click.argument(
    "idxml_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--feature-table",
    "feature_table_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--psm-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--protein-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--feature-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--rejected-feature-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def openms_import_command(
    idxml_path: Path,
    feature_table_path: Path,
    summary_tsv_out: Path | None,
    psm_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    feature_tsv_out: Path | None,
    rejected_feature_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Import one OpenMS idXML bundle with practical exported feature evidence."""
    try:
        report = build_openms_import_report(
            idxml_path,
            feature_table_path=feature_table_path,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_openms_summary_tsv(report.summary))
    if psm_tsv_out is not None:
        _write_text_output(psm_tsv_out, render_openms_psm_tsv(report.psm_rows))
    if protein_tsv_out is not None:
        _write_text_output(
            protein_tsv_out,
            render_openms_protein_tsv(report.protein_rows),
        )
    if feature_tsv_out is not None:
        _write_text_output(
            feature_tsv_out,
            render_openms_feature_tsv(report.feature_rows),
        )
    if rejected_feature_tsv_out is not None:
        _write_text_output(
            rejected_feature_tsv_out,
            render_rejected_evidence_tsv(report.rejected_evidence_rows),
        )

    payload = {
        "summary": report.summary.to_dict(),
        "feature_parse_summary": report.feature_parse_summary.to_dict(),
        "psm_rows": [row.to_dict() for row in report.psm_rows],
        "protein_rows": [row.to_dict() for row in report.protein_rows],
        "feature_rows": [row.to_dict() for row in report.feature_rows],
        "rejected_feature_rows": [
            row.to_dict() for row in report.rejected_feature_rows
        ],
        "rejected_evidence_rows": [
            row.to_dict() for row in report.rejected_evidence_rows
        ],
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "psm_tsv": None if psm_tsv_out is None else str(psm_tsv_out),
            "protein_tsv": None if protein_tsv_out is None else str(protein_tsv_out),
            "feature_tsv": None if feature_tsv_out is None else str(feature_tsv_out),
            "rejected_feature_tsv": None
            if rejected_feature_tsv_out is None
            else str(rejected_feature_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("fasta-provenance")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--duplicate-accession-policy",
    type=_duplicate_accession_policy_choice(),
    default=DuplicateAccessionPolicy.REJECT.value,
    show_default=True,
)
@click.option("--operation", default="fasta-parse", show_default=True)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Where to write the provenance manifest JSON.",
)
def fasta_provenance_command(
    input_fasta: Path,
    mode: str,
    duplicate_accession_policy: str,
    operation: str,
    out_path: Path,
) -> None:
    """Write a provenance manifest for one FASTA processing step."""
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        duplicate_accession_policy=DuplicateAccessionPolicy(
            duplicate_accession_policy
        ),
        allow_rejected=True,
    )
    manifest = build_fasta_provenance_manifest(
        operation=operation,
        source_path=input_fasta,
        parse_mode=FastaParseMode(mode),
        input_record_count=report.total_records,
        accepted_record_count=len(report.accepted_records),
        rejected_record_count=len(report.rejected_records),
        output_record_count=len(report.accepted_records),
        parameters={
            "operation": operation,
            "duplicate_accession_policy": duplicate_accession_policy,
        },
    )
    _emit_json(manifest, out_path=out_path)


@cli.command("fasta-decoy")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--decoy-mode",
    type=_decoy_mode_choice(),
    default=DecoyGenerationMode.REVERSE.value,
    show_default=True,
)
@click.option("--prefix", default="DECOY_", show_default=True)
@click.option("--seed", type=int, default=17, show_default=True)
@click.option(
    "--decoys-only",
    is_flag=True,
    default=False,
    help="Write only decoy records instead of target+decoy output.",
)
@click.option(
    "--out-fasta",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Where to write the generated target/decoy FASTA.",
)
@click.option(
    "--report-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON validation report output path.",
)
@click.option(
    "--manifest-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON manifest output path.",
)
def fasta_decoy_command(
    input_fasta: Path,
    mode: str,
    decoy_mode: str,
    prefix: str,
    seed: int,
    decoys_only: bool,
    out_fasta: Path,
    report_out: Path | None,
    manifest_out: Path | None,
) -> None:
    """Generate target/decoy FASTA output and validate the result."""
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=False,
    )
    try:
        decoys = generate_decoy_records(
            report.accepted_records,
            mode=DecoyGenerationMode(decoy_mode),
            prefix=prefix,
            seed=seed,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    output_records = decoys if decoys_only else (*report.accepted_records, *decoys)
    out_fasta.write_text(render_fasta_records(tuple(output_records)))
    generation_report = build_decoy_generation_report(
        report.accepted_records,
        decoys,
        mode=DecoyGenerationMode(decoy_mode),
        prefix=prefix,
        seed=seed,
    )
    manifest = build_decoy_generation_manifest(
        input_records=report.accepted_records,
        output_records=tuple(output_records),
        mode=DecoyGenerationMode(decoy_mode),
        prefix=prefix,
        seed=seed,
        source_path=input_fasta,
    )
    if manifest_out is not None:
        manifest_out.write_text(manifest.to_stable_json() + "\n")
    validation = validate_target_decoy_database(tuple(output_records), prefix=prefix)
    payload = validation.to_dict()
    payload["reproducibility_hash"] = manifest.reproducibility_hash
    payload["output_sha256"] = manifest.output_sha256
    payload["generation_report"] = generation_report.to_dict()
    _emit_json(payload, out_path=report_out)


@cli.command("target-decoy-validate")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option("--prefix", default="DECOY_", show_default=True)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def target_decoy_validate_command(
    input_fasta: Path,
    mode: str,
    prefix: str,
    out_path: Path | None,
) -> None:
    """Validate target/decoy pairing completeness for a FASTA collection."""
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=False,
    )
    validation = validate_target_decoy_database(report.accepted_records, prefix=prefix)
    _emit_json(validation, out_path=out_path)


@cli.command("digest")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option("--protease", default="trypsin", show_default=True)
@click.option(
    "--custom-protease",
    default=None,
    help=(
        "Custom rule such as 'after=KR;block_next=P', "
        "'before=D;block_previous=P', or "
        "'pattern=(?<!P)(?P<site>D);cut_before=site'."
    ),
)
@click.option(
    "--custom-protease-name",
    default="custom",
    show_default=True,
    help="Stable name recorded for a custom protease rule.",
)
@click.option("--missed-cleavages", type=int, default=0, show_default=True)
@click.option(
    "--digestion-mode",
    type=_digestion_mode_choice(),
    default=PeptideDigestionMode.FULL.value,
    show_default=True,
)
@click.option("--min-length", type=int, default=1, show_default=True)
@click.option("--max-length", type=int, default=None)
@click.option("--min-mass", type=float, default=None)
@click.option("--max-mass", type=float, default=None)
@click.option(
    "--format",
    "export_format",
    type=_export_format_choice(),
    default="tsv",
    show_default=True,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), required=True
)
@click.option(
    "--manifest-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--peptide-protein-table-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def digest_command(
    input_fasta: Path,
    mode: str,
    protease: str,
    custom_protease: str | None,
    custom_protease_name: str,
    missed_cleavages: int,
    digestion_mode: str,
    min_length: int,
    max_length: int | None,
    min_mass: float | None,
    max_mass: float | None,
    export_format: str,
    out_path: Path,
    manifest_out: Path | None,
    peptide_protein_table_out: Path | None,
) -> None:
    """Digest FASTA records into peptide exports."""
    try:
        protease_rule, custom_specification = _resolve_cli_protease_rule(
            protease=protease,
            custom_protease=custom_protease,
            custom_protease_name=custom_protease_name,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=False,
    )
    peptides = digest_protein_records(
        report.accepted_records,
        protease=protease_rule,
        missed_cleavages=missed_cleavages,
        mode=PeptideDigestionMode(digestion_mode),
        min_length=min_length,
        max_length=max_length,
        min_mass=min_mass,
        max_mass=max_mass,
    )

    try:
        if export_format == "tsv":
            export_peptides_tsv(peptides, out_path)
        elif export_format == "jsonl":
            export_peptides_jsonl(peptides, out_path)
        elif export_format == "fasta":
            export_peptides_fasta(peptides, out_path)
        else:
            export_peptides_parquet(peptides, out_path)
        if peptide_protein_table_out is not None:
            export_peptide_protein_table_tsv(peptides, peptide_protein_table_out)
    except (RuntimeError, OSError) as exc:
        raise click.ClickException(str(exc)) from exc

    manifest = build_digest_manifest(
        peptides=peptides,
        protease=protease_rule,
        digestion_mode=PeptideDigestionMode(digestion_mode),
        missed_cleavages=missed_cleavages,
        min_length=min_length,
        max_length=max_length,
        min_mass=min_mass,
        max_mass=max_mass,
        source_path=input_fasta,
        input_record_count=report.total_records,
    )
    if manifest_out is not None:
        manifest_out.write_text(manifest.to_stable_json() + "\n")

    payload = {
        "input_record_count": report.total_records,
        "output_peptide_count": len(peptides),
        "protease": protease_rule.name,
        "custom_protease": custom_specification,
        "digestion_mode": digestion_mode,
        "policy_hash": manifest.policy_hash,
        "export_format": export_format,
        "output_sha256": peptide_export_fingerprint(peptides),
        "output_path": str(out_path),
    }
    if peptide_protein_table_out is not None:
        payload["peptide_protein_table_path"] = str(peptide_protein_table_out)
        payload["peptide_protein_table_sha256"] = hashlib.sha256(
            peptide_protein_table_out.read_bytes()
        ).hexdigest()
    _emit_json(payload)


@cli.command("theoretical-digest")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option("--protease", default="trypsin", show_default=True)
@click.option(
    "--custom-protease",
    default=None,
    help=(
        "Custom rule such as 'after=KR;block_next=P', "
        "'before=D;block_previous=P', or "
        "'pattern=(?<!P)(?P<site>D);cut_before=site'."
    ),
)
@click.option(
    "--custom-protease-name",
    default="custom",
    show_default=True,
    help="Stable name recorded for a custom protease rule.",
)
@click.option("--missed-cleavages", type=int, default=0, show_default=True)
@click.option(
    "--digestion-mode",
    type=_digestion_mode_choice(),
    default=PeptideDigestionMode.FULL.value,
    show_default=True,
)
@click.option("--min-length", type=int, default=1, show_default=True)
@click.option("--max-length", type=int, default=None)
@click.option("--min-mass", type=float, default=None)
@click.option("--max-mass", type=float, default=None)
@click.option(
    "--static-mod",
    "static_modifications",
    multiple=True,
    help="Repeat for each static modification name or controlled id.",
)
@click.option(
    "--variable-mod",
    "variable_modifications",
    multiple=True,
    help="Repeat for each variable modification name or controlled id.",
)
@click.option(
    "--modification-registry",
    "registry_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--allow-isotopic-labels/--disallow-isotopic-labels",
    default=False,
    show_default=True,
)
@click.option(
    "--allowed-label-family",
    "allowed_label_families",
    multiple=True,
    help="Repeat for each allowed isotopic label family.",
)
@click.option(
    "--max-variants-per-peptide",
    type=int,
    default=128,
    show_default=True,
)
@click.option(
    "--out-dir",
    type=click.Path(path_type=Path, file_okay=False),
    required=True,
)
def theoretical_digest_command(
    input_fasta: Path,
    mode: str,
    protease: str,
    custom_protease: str | None,
    custom_protease_name: str,
    missed_cleavages: int,
    digestion_mode: str,
    min_length: int,
    max_length: int | None,
    min_mass: float | None,
    max_mass: float | None,
    static_modifications: tuple[str, ...],
    variable_modifications: tuple[str, ...],
    registry_path: Path | None,
    allow_isotopic_labels: bool,
    allowed_label_families: tuple[str, ...],
    max_variants_per_peptide: int,
    out_dir: Path,
) -> None:
    """Build the governed theoretical digest TSV bundle."""
    try:
        protease_rule, custom_specification = _resolve_cli_protease_rule(
            protease=protease,
            custom_protease=custom_protease,
            custom_protease_name=custom_protease_name,
        )
        (
            registry,
            resolved_static,
            resolved_variable,
            labeling_policy,
        ) = _resolve_cli_theoretical_digest_modifications(
            static_modifications=static_modifications,
            variable_modifications=variable_modifications,
            registry_path=registry_path,
            allow_isotopic_labels=allow_isotopic_labels,
            allowed_label_families=allowed_label_families,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=False,
    )
    bundle = build_theoretical_digest_bundle(
        report.accepted_records,
        protease=protease_rule,
        missed_cleavages=missed_cleavages,
        digestion_mode=PeptideDigestionMode(digestion_mode),
        min_length=min_length,
        max_length=max_length,
        min_mass=min_mass,
        max_mass=max_mass,
        static_modifications=resolved_static,
        variable_modifications=resolved_variable,
        registry=registry,
        labeling_policy=labeling_policy,
        max_variable_variants_per_peptide=max_variants_per_peptide,
    )

    try:
        peptides_path, mappings_path, summary_path = export_theoretical_digest_bundle(
            bundle,
            out_dir,
        )
    except OSError as exc:
        raise click.ClickException(str(exc)) from exc

    _emit_json(
        {
            "input_record_count": report.total_records,
            "protease": protease_rule.name,
            "custom_protease": custom_specification,
            "digestion_mode": digestion_mode,
            "static_modification_names": [
                definition.name for definition in resolved_static
            ],
            "variable_modification_names": [
                definition.name for definition in resolved_variable
            ],
            "search_space_hash": bundle.search_space_hash,
            "output_candidate_peptide_count": bundle.summary.output_candidate_peptide_count,
            "output_mapping_count": bundle.summary.output_mapping_count,
            "digest_peptides_path": str(peptides_path),
            "peptide_to_protein_path": str(mappings_path),
            "digest_summary_path": str(summary_path),
        }
    )


@cli.command("peptide-index")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--peptide",
    "peptides",
    multiple=True,
    required=True,
    help="Repeat for each peptide or modified peptide query to index.",
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option("--protease", default="trypsin", show_default=True)
@click.option(
    "--custom-protease",
    default=None,
    help=(
        "Custom rule such as 'after=KR;block_next=P', "
        "'before=D;block_previous=P', or "
        "'pattern=(?<!P)(?P<site>D);cut_before=site'."
    ),
)
@click.option(
    "--custom-protease-name",
    default="custom",
    show_default=True,
    help="Stable name recorded for a custom protease rule.",
)
@click.option("--missed-cleavages", type=int, default=0, show_default=True)
@click.option(
    "--digestion-mode",
    type=_digestion_mode_choice(),
    default=PeptideDigestionMode.FULL.value,
    show_default=True,
)
@click.option(
    "--il-equivalent/--exact-il",
    default=False,
    show_default=True,
    help="Optionally collapse isoleucine and leucine during peptide lookup.",
)
@click.option(
    "--protein-group-map",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional TSV with accession and protein_group columns.",
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def peptide_index_command(
    input_fasta: Path,
    peptides: tuple[str, ...],
    mode: str,
    protease: str,
    custom_protease: str | None,
    custom_protease_name: str,
    missed_cleavages: int,
    digestion_mode: str,
    il_equivalent: bool,
    protein_group_map: Path | None,
    out_path: Path | None,
) -> None:
    """Index peptide queries against a digested FASTA database."""
    try:
        protease_rule, custom_specification = _resolve_cli_protease_rule(
            protease=protease,
            custom_protease=custom_protease,
            custom_protease_name=custom_protease_name,
        )
        report = _load_fasta_report(
            input_fasta,
            mode=FastaParseMode(mode),
            allow_rejected=False,
        )
        group_map = (
            _load_protein_group_map(protein_group_map)
            if protein_group_map is not None
            else {}
        )
        lookup = build_peptide_database_lookup_report(
            peptides,
            report.accepted_records,
            protease=protease_rule,
            missed_cleavages=missed_cleavages,
            digestion_mode=PeptideDigestionMode(digestion_mode),
            treat_isoleucine_as_leucine=il_equivalent,
            protein_group_by_accession=group_map,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    _emit_json(
        {
            "input_record_count": report.total_records,
            "query_peptide_count": len(peptides),
            "protease": protease_rule.name,
            "custom_protease": custom_specification,
            "digestion_mode": digestion_mode,
            "missed_cleavages": missed_cleavages,
            "il_equivalent": il_equivalent,
            "protein_group_map_supplied": protein_group_map is not None,
            "report": lookup.to_dict(),
        },
        out_path=out_path,
    )


@cli.command("peptide-mass")
@click.argument("sequence")
@click.option(
    "--mod",
    "modifications",
    multiple=True,
    help="Modification assignment like Oxidation@3 or Acetyl@n-term.",
)
@click.option("--charge", type=int, default=2, show_default=True)
@click.option(
    "--fragment-series",
    multiple=True,
    type=_fragment_series_choice(),
    default=("a", "b", "y"),
    show_default=True,
)
@click.option("--include-neutral-losses", is_flag=True, default=False)
@click.option("--isotope-peaks", type=int, default=6, show_default=True)
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional JSON modification registry path.",
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def peptide_mass_command(
    sequence: str,
    modifications: tuple[str, ...],
    charge: int,
    fragment_series: tuple[str, ...],
    include_neutral_losses: bool,
    isotope_peaks: int,
    registry_path: Path | None,
    out_path: Path | None,
) -> None:
    """Emit peptide chemistry diagnostics for one sequence plus optional modifications."""
    try:
        registry = (
            load_modification_registry(registry_path)
            if registry_path is not None
            else None
        )
        peptide = build_modified_peptide(
            sequence,
            assignments=tuple(modifications),
            registry=registry,
        )
        composition = build_peptide_elemental_composition(
            peptide,
            registry=registry,
        )
        charge_state = build_peptide_charge_state(
            peptide,
            charge=charge,
            registry=registry,
        )
        envelope = approximate_peptide_isotope_envelope(
            peptide,
            charge=charge,
            peak_count=isotope_peaks,
            registry=registry,
        )
        localization = build_modification_localization_advisory(
            peptide,
            registry=registry,
        )
        fragments = calculate_fragment_ions(
            peptide,
            charges=(charge,),
            series=tuple(FragmentIonSeries(series) for series in fragment_series),
            include_neutral_losses=include_neutral_losses,
            registry=registry,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    payload = {
        "canonical_notation": canonicalize_modified_peptide(peptide, registry=registry),
        "elemental_composition": composition.to_dict(),
        "charge_state": charge_state.to_dict(),
        "isotope_envelope": envelope.to_dict(),
        "localization": localization.to_dict(),
        "fragment_ion_count": len(fragments),
        "fragments": [fragment.to_dict() for fragment in fragments],
    }
    _emit_json(payload, out_path=out_path)


@cli.command("isotope-envelope")
@click.argument("sequence")
@click.option(
    "--mod",
    "modifications",
    multiple=True,
    help="Modification assignment like Oxidation@3 or Acetyl@n-term.",
)
@click.option(
    "--charge",
    "charges",
    multiple=True,
    type=int,
    default=(2,),
    show_default=True,
)
@click.option(
    "--max-isotope-index",
    type=int,
    default=5,
    show_default=True,
)
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional JSON modification registry path.",
)
@click.option(
    "--tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional isotope envelope TSV output path.",
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def isotope_envelope_command(
    sequence: str,
    modifications: tuple[str, ...],
    charges: tuple[int, ...],
    max_isotope_index: int,
    registry_path: Path | None,
    tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Predict M+0 through M+n isotope envelopes for one peptide."""
    try:
        registry = (
            load_modification_registry(registry_path)
            if registry_path is not None
            else None
        )
        peptide = build_modified_peptide(
            sequence,
            assignments=tuple(modifications),
            registry=registry,
        )
        composition = build_peptide_elemental_composition(
            peptide,
            registry=registry,
        )
        envelopes = predict_peptide_isotope_envelopes(
            peptide,
            charges=charges,
            max_isotope_index=max_isotope_index,
            registry=registry,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if tsv_out is not None:
        _write_text_output(tsv_out, render_isotope_envelopes_tsv(envelopes))

    payload = {
        "canonical_notation": peptide.canonical_notation,
        "elemental_composition": composition.to_dict(),
        "charges": list(charges),
        "max_isotope_index": max_isotope_index,
        "envelopes": [envelope.to_dict() for envelope in envelopes],
        "tsv_out": str(tsv_out) if tsv_out else None,
    }
    _emit_json(payload, out_path=out_path)


@cli.command("fragment-ions")
@click.argument("sequence")
@click.option(
    "--mod",
    "modifications",
    multiple=True,
    help="Modification assignment like Oxidation@3 or Acetyl@n-term.",
)
@click.option(
    "--charge",
    "charges",
    multiple=True,
    type=int,
    default=(1, 2, 3),
    show_default=True,
)
@click.option(
    "--fragment-series",
    multiple=True,
    type=_fragment_series_choice(),
    default=("a", "b", "y"),
    show_default=True,
)
@click.option("--include-neutral-losses", is_flag=True, default=False)
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional JSON modification registry path.",
)
@click.option(
    "--tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def fragment_ions_command(
    sequence: str,
    modifications: tuple[str, ...],
    charges: tuple[int, ...],
    fragment_series: tuple[str, ...],
    include_neutral_losses: bool,
    registry_path: Path | None,
    tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Emit one dedicated theoretical fragment-ion review report."""
    try:
        registry = (
            load_modification_registry(registry_path)
            if registry_path is not None
            else None
        )
        peptide = build_modified_peptide(
            sequence,
            assignments=tuple(modifications),
            registry=registry,
        )
        report = build_fragment_ion_review_report(
            peptide,
            charges=tuple(charges),
            series=tuple(
                FragmentIonSeries(series_name) for series_name in fragment_series
            ),
            include_neutral_losses=include_neutral_losses,
            registry=registry,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if tsv_out is not None:
        _write_text_output(tsv_out, render_fragment_ion_report_tsv(report))

    payload = report.to_dict()
    payload["tsv_out"] = str(tsv_out) if tsv_out else None
    _emit_json(payload, out_path=out_path)


@cli.command("peptide-properties")
@click.argument("sequence")
@click.option(
    "--mod",
    "modifications",
    multiple=True,
    help="Modification assignment like Oxidation@3 or Acetyl@n-term.",
)
@click.option("--charge", type=int, default=2, show_default=True)
@click.option("--protease", default="trypsin", show_default=True)
@click.option(
    "--custom-protease",
    default=None,
    help=(
        "Custom rule such as 'after=KR;block_next=P', "
        "'before=D;block_previous=P', or "
        "'pattern=(?<!P)(?P<site>D);cut_before=site'."
    ),
)
@click.option(
    "--custom-protease-name",
    default="custom",
    show_default=True,
    help="Stable name recorded for a custom protease rule.",
)
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional JSON modification registry path.",
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def peptide_properties_command(
    sequence: str,
    modifications: tuple[str, ...],
    charge: int,
    protease: str,
    custom_protease: str | None,
    custom_protease_name: str,
    registry_path: Path | None,
    out_path: Path | None,
) -> None:
    """Emit peptide property diagnostics for filtering and review."""
    try:
        protease_rule, custom_specification = _resolve_cli_protease_rule(
            protease=protease,
            custom_protease=custom_protease,
            custom_protease_name=custom_protease_name,
        )
        registry = (
            load_modification_registry(registry_path)
            if registry_path is not None
            else None
        )
        report = build_peptide_property_report(
            sequence,
            modification_assignments=modifications,
            charge=charge,
            protease=protease_rule,
            registry=registry,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    payload = report.to_dict()
    payload["custom_protease"] = custom_specification
    _emit_json(payload, out_path=out_path)


@cli.command("peptide-detectability")
@click.argument("sequence")
@click.option(
    "--mod",
    "modifications",
    multiple=True,
    help="Modification assignment like Oxidation@3 or Acetyl@n-term.",
)
@click.option("--charge", type=int, default=2, show_default=True)
@click.option("--protease", default="trypsin", show_default=True)
@click.option(
    "--custom-protease",
    default=None,
    help=(
        "Custom rule such as 'after=KR;block_next=P', "
        "'before=D;block_previous=P', or "
        "'pattern=(?<!P)(?P<site>D);cut_before=site'."
    ),
)
@click.option(
    "--custom-protease-name",
    default="custom",
    show_default=True,
    help="Stable name recorded for a custom protease rule.",
)
@click.option(
    "--uniqueness-class",
    type=click.Choice([entry.value for entry in PeptideUniquenessClass]),
    default=None,
    help="Optional database uniqueness class from the owned uniqueness index.",
)
@click.option(
    "--uniqueness-score",
    type=float,
    default=None,
    help="Optional explicit uniqueness score from 0.0 to 1.0.",
)
@click.option(
    "--observed-psm-count",
    type=int,
    default=None,
    help="Optional observed PSM count to boost detectability with real evidence.",
)
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional JSON modification registry path.",
)
@click.option(
    "--tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional detectability TSV output path.",
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def peptide_detectability_command(
    sequence: str,
    modifications: tuple[str, ...],
    charge: int,
    protease: str,
    custom_protease: str | None,
    custom_protease_name: str,
    uniqueness_class: str | None,
    uniqueness_score: float | None,
    observed_psm_count: int | None,
    registry_path: Path | None,
    tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Score peptide observability from owned sequence and chemistry semantics."""
    try:
        protease_rule, custom_specification = _resolve_cli_protease_rule(
            protease=protease,
            custom_protease=custom_protease,
            custom_protease_name=custom_protease_name,
        )
        registry = (
            load_modification_registry(registry_path)
            if registry_path is not None
            else None
        )
        report = build_peptide_detectability_report(
            sequence,
            modification_assignments=modifications,
            charge=charge,
            protease=protease_rule,
            registry=registry,
            uniqueness_class=uniqueness_class,
            uniqueness_score=uniqueness_score,
            observed_psm_count=observed_psm_count,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if tsv_out is not None:
        _write_text_output(tsv_out, render_peptide_detectability_tsv(report))

    payload = report.to_dict()
    payload["custom_protease"] = custom_specification
    payload["tsv_out"] = str(tsv_out) if tsv_out else None
    _emit_json(payload, out_path=out_path)


@cli.command("precursor-mass-error")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--observed-mz-column", default="observed_mz", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--max-isotope-offset", type=int, default=3, show_default=True)
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional JSON modification registry path.",
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--observations-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--ppm-distribution-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--charge-distribution-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--isotope-distribution-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def precursor_mass_error_command(
    input_tsv: Path,
    peptide_column: str,
    observed_mz_column: str,
    charge_column: str,
    spectrum_id_column: str,
    max_isotope_offset: int,
    registry_path: Path | None,
    summary_tsv_out: Path | None,
    observations_tsv_out: Path | None,
    ppm_distribution_tsv_out: Path | None,
    charge_distribution_tsv_out: Path | None,
    isotope_distribution_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Report precursor mass error from peptide plus observed-m/z tables."""
    try:
        registry = (
            load_modification_registry(registry_path)
            if registry_path is not None
            else None
        )
        queries = _load_precursor_mass_error_queries(
            input_tsv,
            peptide_column=peptide_column,
            observed_mz_column=observed_mz_column,
            charge_column=charge_column,
            spectrum_id_column=spectrum_id_column,
        )
        report = build_precursor_mass_error_report(
            queries,
            registry=registry,
            max_isotope_offset=max_isotope_offset,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_precursor_mass_error_summary_tsv(report),
        )
    if observations_tsv_out is not None:
        _write_text_output(
            observations_tsv_out,
            render_precursor_mass_error_observations_tsv(report.observations),
        )
    if ppm_distribution_tsv_out is not None:
        _write_text_output(
            ppm_distribution_tsv_out,
            render_precursor_mass_error_distribution_tsv(
                report.ppm_error_distribution,
                distribution_name="abs_ppm",
            ),
        )
    if charge_distribution_tsv_out is not None:
        _write_text_output(
            charge_distribution_tsv_out,
            render_precursor_mass_error_distribution_tsv(
                report.charge_distribution,
                distribution_name="charge",
            ),
        )
    if isotope_distribution_tsv_out is not None:
        _write_text_output(
            isotope_distribution_tsv_out,
            render_precursor_mass_error_distribution_tsv(
                report.isotope_offset_distribution,
                distribution_name="recommended_isotope_offset",
            ),
        )

    payload = report.to_dict()
    payload["input_row_count"] = len(queries)
    payload["summary_tsv_out"] = str(summary_tsv_out) if summary_tsv_out else None
    payload["observations_tsv_out"] = (
        str(observations_tsv_out) if observations_tsv_out else None
    )
    payload["ppm_distribution_tsv_out"] = (
        str(ppm_distribution_tsv_out) if ppm_distribution_tsv_out else None
    )
    payload["charge_distribution_tsv_out"] = (
        str(charge_distribution_tsv_out) if charge_distribution_tsv_out else None
    )
    payload["isotope_distribution_tsv_out"] = (
        str(isotope_distribution_tsv_out) if isotope_distribution_tsv_out else None
    )
    _emit_json(payload, out_path=out_path)


@cli.command("modified-peptide-parse")
@click.argument("notation")
@click.option(
    "--dialect",
    type=_modified_peptide_dialect_choice(),
    required=True,
    help="Search-engine peptide notation dialect to normalize.",
)
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional JSON modification registry path.",
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def modified_peptide_parse_command(
    notation: str,
    dialect: str,
    registry_path: Path | None,
    out_path: Path | None,
) -> None:
    """Normalize one search-engine modified peptide notation."""
    try:
        registry = (
            load_modification_registry(registry_path)
            if registry_path is not None
            else None
        )
        report = build_search_engine_modified_peptide_report(
            notation,
            dialect=dialect,
            registry=registry,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    _emit_json(report.to_dict(), out_path=out_path)


@cli.command("modification-resolve")
@click.argument("token")
@click.option(
    "--residue",
    default=None,
    help="Optional residue for residue-compatibility review.",
)
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional JSON modification registry path.",
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def modification_resolve_command(
    token: str,
    residue: str | None,
    registry_path: Path | None,
    out_path: Path | None,
) -> None:
    """Resolve one modification token against builtin or custom registries."""
    try:
        registry = (
            load_modification_registry(registry_path)
            if registry_path is not None
            else None
        )
        report = build_modification_resolution_report(
            token,
            residue=residue,
            registry=registry,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    _emit_json(report.to_dict(), out_path=out_path)


@cli.command("psm-map")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mapping",
    "mapping_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--normalized-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def psm_map_command(
    input_tsv: Path,
    mapping_path: Path,
    normalized_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Map a lab-local PSM table through an explicit YAML or JSON column map."""
    try:
        report = build_generic_psm_mapper_report(
            input_tsv,
            mapping_path=mapping_path,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if normalized_tsv_out is not None:
        _write_text_output(
            normalized_tsv_out,
            render_generic_psm_mapper_tsv(report.mapped_rows),
        )
    if rejected_tsv_out is not None:
        _write_text_output(
            rejected_tsv_out,
            render_rejected_evidence_tsv(report.rejected_evidence_rows),
        )

    payload = {
        "column_mapping": report.column_mapping.to_dict(),
        "source_columns": list(report.source_columns),
        "normalization": {
            "adapter": report.normalization.adapter_manifest.to_dict(),
            "accepted_rows": len(report.normalization.parse_report.accepted_records),
            "rejected_rows": len(report.normalization.parse_report.rejected_rows),
        },
        "summary": report.summary.to_dict(),
        "rejected_rows": [row.to_dict() for row in report.rejected_rows],
        "rejected_evidence_rows": [
            row.to_dict() for row in report.rejected_evidence_rows
        ],
        "mapped_rows": [row.to_dict() for row in report.mapped_rows],
        "outputs": {
            "normalized_tsv": None
            if normalized_tsv_out is None
            else str(normalized_tsv_out),
            "rejected_tsv": None if rejected_tsv_out is None else str(rejected_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("psm-inspect")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--run-id-column", default=None)
@click.option("--modified-peptide-column", default=None)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--protease", default="trypsin", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--jsonl-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--provenance-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--score-distribution-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--q-value-distribution-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--charge-distribution-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--peptide-length-distribution-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--missed-cleavage-distribution-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def psm_inspect_command(
    input_tsv: Path,
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    pep_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    protease: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    jsonl_out: Path | None,
    tsv_out: Path | None,
    provenance_out: Path | None,
    summary_tsv_out: Path | None,
    score_distribution_tsv_out: Path | None,
    q_value_distribution_tsv_out: Path | None,
    charge_distribution_tsv_out: Path | None,
    peptide_length_distribution_tsv_out: Path | None,
    missed_cleavage_distribution_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Inspect a generic PSM TSV and emit normalized summaries."""
    try:
        mapping = _build_psm_mapping(
            run_id_column=run_id_column,
            spectrum_id_column=spectrum_id_column,
            peptide_column=peptide_column,
            modified_peptide_column=modified_peptide_column,
            charge_column=charge_column,
            score_column=score_column,
            q_value_column=q_value_column,
            posterior_error_probability_column=pep_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            contaminant_label_column=contaminant_label_column,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        normalized = apply_q_values(report.accepted_records)
        inspection = build_psm_evidence_inspection_report(report, protease=protease)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if jsonl_out is not None:
        export_psm_jsonl(normalized, jsonl_out)
    if tsv_out is not None:
        export_psm_tsv(normalized, tsv_out)
    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_psm_evidence_inspection_summary_tsv(inspection),
        )
    if score_distribution_tsv_out is not None:
        _write_text_output(
            score_distribution_tsv_out,
            render_psm_inspection_distribution_tsv(inspection.score_distribution),
        )
    if q_value_distribution_tsv_out is not None:
        _write_text_output(
            q_value_distribution_tsv_out,
            render_psm_inspection_distribution_tsv(inspection.q_value_distribution),
        )
    if charge_distribution_tsv_out is not None:
        _write_text_output(
            charge_distribution_tsv_out,
            render_psm_inspection_distribution_tsv(inspection.charge_distribution),
        )
    if peptide_length_distribution_tsv_out is not None:
        _write_text_output(
            peptide_length_distribution_tsv_out,
            render_psm_inspection_distribution_tsv(
                inspection.peptide_length_distribution
            ),
        )
    if missed_cleavage_distribution_tsv_out is not None:
        _write_text_output(
            missed_cleavage_distribution_tsv_out,
            render_psm_inspection_distribution_tsv(
                inspection.missed_cleavage_distribution
            ),
        )

    provenance = build_search_result_provenance_manifest(
        source_path=input_tsv,
        parse_report=report,
        decoy_policy=decoy_policy,
    )
    if provenance_out is not None:
        provenance_out.write_text(provenance.to_stable_json() + "\n")

    payload = {
        "accepted_rows": len(report.accepted_records),
        "rejected_rows": len(report.rejected_rows),
        "inspection": inspection.to_dict(),
        "psm_summary": build_psm_summary_report(normalized).to_dict(),
        "peptide_summary": build_peptide_summary_report(normalized).to_dict(),
        "protein_summary": build_protein_summary_report(normalized).to_dict(),
        "provenance": provenance.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "score_distribution_tsv": None
            if score_distribution_tsv_out is None
            else str(score_distribution_tsv_out),
            "q_value_distribution_tsv": None
            if q_value_distribution_tsv_out is None
            else str(q_value_distribution_tsv_out),
            "charge_distribution_tsv": None
            if charge_distribution_tsv_out is None
            else str(charge_distribution_tsv_out),
            "peptide_length_distribution_tsv": None
            if peptide_length_distribution_tsv_out is None
            else str(peptide_length_distribution_tsv_out),
            "missed_cleavage_distribution_tsv": None
            if missed_cleavage_distribution_tsv_out is None
            else str(missed_cleavage_distribution_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("peptide-evidence")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--threshold", type=float, default=0.05, show_default=True)
@click.option(
    "--score-orientation",
    type=_score_orientation_choice(),
    default=ScoreOrientation.HIGHER_BETTER.value,
    show_default=True,
)
@click.option("--strong-q-value", type=float, default=0.01, show_default=True)
@click.option(
    "--reproducible-spectrum-count", type=int, default=2, show_default=True
)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--run-id-column", default=None)
@click.option("--modified-peptide-column", default=None)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--pep-column", default=None)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--entries-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def peptide_evidence_command(
    input_tsv: Path,
    threshold: float,
    score_orientation: str,
    strong_q_value: float,
    reproducible_spectrum_count: int,
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    pep_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    summary_tsv_out: Path | None,
    entries_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Review classified peptide evidence with strong, moderate, shared, and weak states."""
    try:
        mapping = _build_psm_mapping(
            run_id_column=run_id_column,
            spectrum_id_column=spectrum_id_column,
            peptide_column=peptide_column,
            modified_peptide_column=modified_peptide_column,
            charge_column=charge_column,
            score_column=score_column,
            q_value_column=q_value_column,
            posterior_error_probability_column=pep_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            contaminant_label_column=contaminant_label_column,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        review = build_peptide_evidence_review_report(
            report.accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
            strong_q_value=strong_q_value,
            reproducible_spectrum_count=reproducible_spectrum_count,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_peptide_evidence_summary_tsv(review),
        )
    if entries_tsv_out is not None:
        _write_text_output(
            entries_tsv_out,
            render_peptide_evidence_entries_tsv(review),
        )

    payload = review.to_dict()
    payload["accepted_rows"] = len(report.accepted_records)
    payload["rejected_rows"] = len(report.rejected_rows)
    payload["outputs"] = {
        "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
        "entries_tsv": None if entries_tsv_out is None else str(entries_tsv_out),
    }
    _emit_json(payload, out_path=out_path)


@cli.command("protein-evidence")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--high-q-value", type=float, default=0.01, show_default=True)
@click.option("--moderate-q-value", type=float, default=0.05, show_default=True)
@click.option(
    "--score-orientation",
    type=_score_orientation_choice(),
    default=ScoreOrientation.HIGHER_BETTER.value,
    show_default=True,
)
@click.option(
    "--design-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--exploratory-protein", multiple=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--run-id-column", default=None)
@click.option("--modified-peptide-column", default=None)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--pep-column", default=None)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--entries-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def protein_evidence_command(
    input_tsv: Path,
    high_q_value: float,
    moderate_q_value: float,
    score_orientation: str,
    design_tsv: Path | None,
    exploratory_protein: tuple[str, ...],
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    pep_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    summary_tsv_out: Path | None,
    entries_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Review final protein evidence tiers with explicit downgrade reasons."""
    try:
        mapping = _build_psm_mapping(
            run_id_column=run_id_column,
            spectrum_id_column=spectrum_id_column,
            peptide_column=peptide_column,
            modified_peptide_column=modified_peptide_column,
            charge_column=charge_column,
            score_column=score_column,
            q_value_column=q_value_column,
            posterior_error_probability_column=pep_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            contaminant_label_column=contaminant_label_column,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        run_contexts: tuple[RunDetectionContext, ...] = ()
        if design_tsv is not None:
            design_report = parse_experimental_design_table(design_tsv)
            if design_report.rejected_rows:
                raise ValueError("design table contains rejected rows")
            run_contexts = _build_run_detection_contexts(design_report.accepted_entries)
        review = build_protein_evidence_review_report(
            report.accepted_records,
            high_q_value=high_q_value,
            moderate_q_value=moderate_q_value,
            score_orientation=score_orientation,
            run_contexts=run_contexts,
            exploratory_protein_refs=exploratory_protein,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_protein_evidence_summary_tsv(review),
        )
    if entries_tsv_out is not None:
        _write_text_output(
            entries_tsv_out,
            render_protein_evidence_entries_tsv(review),
        )

    payload = review.to_dict()
    payload["accepted_rows"] = len(report.accepted_records)
    payload["rejected_rows"] = len(report.rejected_rows)
    payload["outputs"] = {
        "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
        "entries_tsv": None if entries_tsv_out is None else str(entries_tsv_out),
    }
    _emit_json(payload, out_path=out_path)


@cli.command("cross-run-reproducibility")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--entity-type",
    type=click.Choice(("peptide", "protein"), case_sensitive=False),
    default="peptide",
    show_default=True,
)
@click.option(
    "--design-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option("--exploratory-entity", multiple=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--run-id-column", default="run_id", show_default=True)
@click.option("--modified-peptide-column", default=None)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--entries-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def cross_run_reproducibility_command(
    input_tsv: Path,
    entity_type: str,
    design_tsv: Path,
    exploratory_entity: tuple[str, ...],
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    summary_tsv_out: Path | None,
    entries_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Score peptide or protein evidence by cross-run detection consistency."""
    try:
        mapping = _build_psm_mapping(
            run_id_column=run_id_column,
            spectrum_id_column=spectrum_id_column,
            peptide_column=peptide_column,
            modified_peptide_column=modified_peptide_column,
            charge_column=charge_column,
            score_column=score_column,
            q_value_column=q_value_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            contaminant_label_column=contaminant_label_column,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        psm_report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        design_report = parse_experimental_design_table(design_tsv)
        if design_report.rejected_rows:
            raise ValueError("design table contains rejected rows")
        run_contexts = _build_run_detection_contexts(design_report.accepted_entries)
        if entity_type == "peptide":
            reproducibility_report = build_peptide_cross_run_reproducibility_report(
                psm_report.accepted_records,
                run_contexts=run_contexts,
                exploratory_canonical_peptides=exploratory_entity,
            )
        else:
            reproducibility_report = build_protein_cross_run_reproducibility_report(
                psm_report.accepted_records,
                run_contexts=run_contexts,
                exploratory_protein_refs=exploratory_entity,
            )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_cross_run_reproducibility_summary_tsv(reproducibility_report),
        )
    if entries_tsv_out is not None:
        _write_text_output(
            entries_tsv_out,
            render_cross_run_reproducibility_entries_tsv(reproducibility_report),
        )

    payload = reproducibility_report.to_dict()
    payload["accepted_rows"] = len(psm_report.accepted_records)
    payload["rejected_rows"] = len(psm_report.rejected_rows)
    payload["outputs"] = {
        "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
        "entries_tsv": None if entries_tsv_out is None else str(entries_tsv_out),
    }
    _emit_json(payload, out_path=out_path)


@cli.command("fdr")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--threshold", type=float, default=0.01, show_default=True)
@click.option(
    "--score-orientation",
    type=_score_orientation_choice(),
    default=ScoreOrientation.HIGHER_BETTER.value,
    show_default=True,
)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--run-id-column", default=None)
@click.option("--modified-peptide-column", default=None)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--pep-column", default=None)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--jsonl-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--provenance-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--entries-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--audit-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--calibration-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--score-separation-summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--score-separation-bins-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--error-rate-summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--error-rate-entries-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def fdr_command(
    input_tsv: Path,
    threshold: float,
    score_orientation: str,
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    pep_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    jsonl_out: Path | None,
    tsv_out: Path | None,
    provenance_out: Path | None,
    summary_tsv_out: Path | None,
    entries_tsv_out: Path | None,
    audit_out: Path | None,
    calibration_out: Path | None,
    score_separation_summary_tsv_out: Path | None,
    score_separation_bins_tsv_out: Path | None,
    error_rate_summary_tsv_out: Path | None,
    error_rate_entries_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Apply basic target-decoy FDR and emit filtered PSM summaries."""
    try:
        mapping = _build_psm_mapping(
            run_id_column=run_id_column,
            spectrum_id_column=spectrum_id_column,
            peptide_column=peptide_column,
            modified_peptide_column=modified_peptide_column,
            charge_column=charge_column,
            score_column=score_column,
            q_value_column=q_value_column,
            posterior_error_probability_column=pep_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            contaminant_label_column=contaminant_label_column,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        parse_report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        annotated_records = annotate_psm_error_rates(
            parse_report.accepted_records,
            score_orientation=score_orientation,
        )
        fdr_report = build_psm_target_decoy_fdr_report(
            annotated_records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        error_rate_report = build_psm_error_rate_annotation_report(
            parse_report.accepted_records,
            score_orientation=score_orientation,
        )
        accepted = tuple(
            entry.psm.model_copy(update={"q_value": entry.q_value})
            for entry in fdr_report.entries
            if entry.accepted
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if jsonl_out is not None:
        export_psm_jsonl(accepted, jsonl_out)
    if tsv_out is not None:
        export_psm_tsv(accepted, tsv_out)
    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_psm_target_decoy_fdr_summary_tsv(fdr_report), encoding="utf-8"
        )
    if entries_tsv_out is not None:
        entries_tsv_out.write_text(
            render_psm_target_decoy_fdr_tsv(fdr_report), encoding="utf-8"
        )

    fdr_policy = FdrPolicy(
        threshold=threshold,
        score_orientation=score_orientation,
        decoy_policy=decoy_policy,
    )
    provenance = build_search_result_provenance_manifest(
        source_path=input_tsv,
        parse_report=parse_report,
        decoy_policy=decoy_policy,
        fdr_policy=fdr_policy,
    )
    audit_trail = build_fdr_audit_trail(
        parse_report.accepted_records,
        threshold=threshold,
        score_orientation=score_orientation,
    )
    calibration_plot = build_calibration_plot_data(
        annotated_records,
        score_orientation=score_orientation,
    )
    score_separation = build_score_separation_diagnostic_report(
        annotated_records,
        score_orientation=score_orientation,
    )
    if provenance_out is not None:
        provenance_out.write_text(provenance.to_stable_json() + "\n")
    if audit_out is not None:
        audit_out.write_text(audit_trail.to_stable_json() + "\n")
    if calibration_out is not None:
        calibration_out.write_text(calibration_plot.to_stable_json() + "\n")
    if score_separation_summary_tsv_out is not None:
        score_separation_summary_tsv_out.write_text(
            render_score_separation_summary_tsv(score_separation),
            encoding="utf-8",
        )
    if score_separation_bins_tsv_out is not None:
        score_separation_bins_tsv_out.write_text(
            render_score_separation_bins_tsv(score_separation),
            encoding="utf-8",
        )
    if error_rate_summary_tsv_out is not None:
        error_rate_summary_tsv_out.write_text(
            render_psm_error_rate_annotation_summary_tsv(error_rate_report),
            encoding="utf-8",
        )
    if error_rate_entries_tsv_out is not None:
        error_rate_entries_tsv_out.write_text(
            render_psm_error_rate_annotation_tsv(error_rate_report),
            encoding="utf-8",
        )

    payload = {
        "threshold": threshold,
        "score_orientation": score_orientation,
        "input_psms": len(parse_report.accepted_records),
        "accepted_psms": len(accepted),
        "fdr_unstable": score_separation.summary.fdr_unstable,
        "fdr_report": fdr_report.summary.to_dict(),
        "fdr_reproducibility_hash": fdr_report.reproducibility_hash,
        "error_rate_annotation": error_rate_report.to_dict(),
        "psm_summary": build_psm_summary_report(accepted).to_dict(),
        "peptide_summary": build_peptide_summary_report(accepted).to_dict(),
        "protein_summary": build_protein_summary_report(accepted).to_dict(),
        "audit_trail": audit_trail.to_dict(),
        "calibration_plot": calibration_plot.to_dict(),
        "score_separation": score_separation.to_dict(),
        "provenance": provenance.to_dict(),
    }
    _emit_json(payload, out_path=out_path)


@cli.command("fdr-reference-check")
@click.argument(
    "reference_json", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--entries-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def fdr_reference_check_command(
    reference_json: Path,
    summary_tsv_out: Path | None,
    entries_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Validate curated target-decoy reference cases against the owned FDR surface."""
    try:
        raw_cases = json.loads(reference_json.read_text(encoding="utf-8"))
        cases = tuple(
            TargetDecoyReferenceCase.model_validate(case) for case in raw_cases
        )
        report = build_target_decoy_reference_validation_report(cases)
    except (ValueError, TypeError) as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_target_decoy_reference_summary_tsv(report),
        )
    if entries_tsv_out is not None:
        _write_text_output(
            entries_tsv_out,
            render_target_decoy_reference_entries_tsv(report),
        )

    payload = report.to_dict()
    payload["outputs"] = {
        "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
        "entries_tsv": None if entries_tsv_out is None else str(entries_tsv_out),
    }
    _emit_json(payload, out_path=out_path)


@cli.command("fdr-levels")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--threshold",
    "thresholds",
    type=float,
    multiple=True,
    default=(0.01, 0.05, 0.1),
    show_default=True,
)
@click.option(
    "--score-orientation",
    type=_score_orientation_choice(),
    default=ScoreOrientation.HIGHER_BETTER.value,
    show_default=True,
)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--run-id-column", default=None)
@click.option("--modified-peptide-column", default=None)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--entries-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def fdr_levels_command(
    input_tsv: Path,
    thresholds: tuple[float, ...],
    score_orientation: str,
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    summary_tsv_out: Path | None,
    entries_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Compare PSM, peptide, and protein FDR counts across explicit thresholds."""
    try:
        mapping = _build_psm_mapping(
            run_id_column=run_id_column,
            spectrum_id_column=spectrum_id_column,
            peptide_column=peptide_column,
            modified_peptide_column=modified_peptide_column,
            charge_column=charge_column,
            score_column=score_column,
            q_value_column=q_value_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            contaminant_label_column=contaminant_label_column,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        parse_report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        review = build_evidence_level_fdr_review_report(
            parse_report.accepted_records,
            thresholds=tuple(thresholds),
            score_orientation=score_orientation,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_evidence_level_fdr_summary_tsv(review),
        )
    if entries_tsv_out is not None:
        _write_text_output(
            entries_tsv_out,
            render_evidence_level_fdr_entries_tsv(review),
        )

    payload = review.to_dict()
    payload["accepted_rows"] = len(parse_report.accepted_records)
    payload["rejected_rows"] = len(parse_report.rejected_rows)
    payload["outputs"] = {
        "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
        "entries_tsv": None if entries_tsv_out is None else str(entries_tsv_out),
    }
    _emit_json(payload, out_path=out_path)


@cli.command("picked-protein-fdr")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--threshold",
    "thresholds",
    type=float,
    multiple=True,
    default=(0.01, 0.05, 0.1),
    show_default=True,
)
@click.option(
    "--score-orientation",
    type=_score_orientation_choice(),
    default=ScoreOrientation.HIGHER_BETTER.value,
    show_default=True,
)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--run-id-column", default=None)
@click.option("--modified-peptide-column", default=None)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--entries-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def picked_protein_fdr_command(
    input_tsv: Path,
    thresholds: tuple[float, ...],
    score_orientation: str,
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    summary_tsv_out: Path | None,
    entries_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Review picked target-decoy protein FDR across explicit thresholds."""
    try:
        mapping = _build_psm_mapping(
            run_id_column=run_id_column,
            spectrum_id_column=spectrum_id_column,
            peptide_column=peptide_column,
            modified_peptide_column=modified_peptide_column,
            charge_column=charge_column,
            score_column=score_column,
            q_value_column=q_value_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            contaminant_label_column=contaminant_label_column,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        parse_report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        review = build_picked_protein_fdr_review_report(
            parse_report.accepted_records,
            thresholds=tuple(thresholds),
            score_orientation=score_orientation,
            decoy_policy=decoy_policy,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_picked_protein_fdr_summary_tsv(review),
        )
    if entries_tsv_out is not None:
        _write_text_output(
            entries_tsv_out,
            render_picked_protein_fdr_entries_tsv(review),
        )

    payload = review.to_dict()
    payload["accepted_rows"] = len(parse_report.accepted_records)
    payload["rejected_rows"] = len(parse_report.rejected_rows)
    payload["outputs"] = {
        "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
        "entries_tsv": None if entries_tsv_out is None else str(entries_tsv_out),
    }
    _emit_json(payload, out_path=out_path)


@cli.command("protein-groups")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--threshold", type=float, default=0.05, show_default=True)
@click.option(
    "--score-orientation",
    type=_score_orientation_choice(),
    default=ScoreOrientation.HIGHER_BETTER.value,
    show_default=True,
)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--run-id-column", default=None)
@click.option("--modified-peptide-column", default=None)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--group-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def protein_groups_command(
    input_tsv: Path,
    threshold: float,
    score_orientation: str,
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    summary_tsv_out: Path | None,
    group_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Review grouped protein evidence from FDR-filtered PSM rows."""
    try:
        mapping = _build_psm_mapping(
            run_id_column=run_id_column,
            spectrum_id_column=spectrum_id_column,
            peptide_column=peptide_column,
            modified_peptide_column=modified_peptide_column,
            charge_column=charge_column,
            score_column=score_column,
            q_value_column=q_value_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            contaminant_label_column=contaminant_label_column,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        parse_report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        filtered_records = filter_psms_by_fdr(
            parse_report.accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        review = build_protein_grouping_review_report(filtered_records)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_protein_grouping_summary_tsv(review),
        )
    if group_tsv_out is not None:
        _write_text_output(
            group_tsv_out,
            render_protein_grouping_entries_tsv(review),
        )

    payload = {
        "threshold": threshold,
        "score_orientation": score_orientation,
        "accepted_rows": len(parse_report.accepted_records),
        "rejected_rows": len(parse_report.rejected_rows),
        "grouped_rows": len(filtered_records),
        **review.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "group_tsv": None if group_tsv_out is None else str(group_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("protein-ambiguity")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--threshold", type=float, default=0.05, show_default=True)
@click.option(
    "--score-orientation",
    type=_score_orientation_choice(),
    default=ScoreOrientation.HIGHER_BETTER.value,
    show_default=True,
)
@click.option("--high-q-value", type=float, default=0.01, show_default=True)
@click.option("--medium-q-value", type=float, default=0.05, show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--run-id-column", default=None)
@click.option("--modified-peptide-column", default=None)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--ambiguity-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def protein_ambiguity_command(
    input_tsv: Path,
    threshold: float,
    score_orientation: str,
    high_q_value: float,
    medium_q_value: float,
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    summary_tsv_out: Path | None,
    ambiguity_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Review ambiguous protein groups from FDR-filtered PSM rows."""
    try:
        mapping = _build_psm_mapping(
            run_id_column=run_id_column,
            spectrum_id_column=spectrum_id_column,
            peptide_column=peptide_column,
            modified_peptide_column=modified_peptide_column,
            charge_column=charge_column,
            score_column=score_column,
            q_value_column=q_value_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            contaminant_label_column=contaminant_label_column,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        parse_report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        filtered_records = filter_psms_by_fdr(
            parse_report.accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        review = build_protein_ambiguity_review_report(
            filtered_records,
            threshold=threshold,
            high_q_value=high_q_value,
            medium_q_value=medium_q_value,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_protein_ambiguity_summary_tsv(review),
        )
    if ambiguity_tsv_out is not None:
        _write_text_output(
            ambiguity_tsv_out,
            render_protein_ambiguity_entries_tsv(review),
        )

    payload = {
        "threshold": threshold,
        "score_orientation": score_orientation,
        "high_q_value": high_q_value,
        "medium_q_value": medium_q_value,
        "accepted_rows": len(parse_report.accepted_records),
        "rejected_rows": len(parse_report.rejected_rows),
        "grouped_rows": len(filtered_records),
        "ambiguity_rows": len(review.entries),
        **review.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "ambiguity_tsv": (
                None if ambiguity_tsv_out is None else str(ambiguity_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("protein-inference-benchmarks")
@click.option("--picked-threshold", type=float, default=0.05, show_default=True)
@click.option(
    "--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--scenarios-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--assessments-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def protein_inference_benchmarks_command(
    picked_threshold: float,
    summary_tsv_out: Path | None,
    scenarios_tsv_out: Path | None,
    assessments_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Review the owned protein-inference benchmark catalog."""
    try:
        suite = build_core_protein_inference_benchmark_suite(
            picked_threshold=picked_threshold
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_protein_inference_benchmark_summary_tsv(suite),
        )
    if scenarios_tsv_out is not None:
        _write_text_output(
            scenarios_tsv_out,
            render_protein_inference_benchmark_scenarios_tsv(suite),
        )
    if assessments_tsv_out is not None:
        _write_text_output(
            assessments_tsv_out,
            render_protein_inference_benchmark_assessments_tsv(suite),
        )

    payload = suite.to_dict()
    payload["picked_threshold"] = picked_threshold
    payload["outputs"] = {
        "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
        "scenarios_tsv": None if scenarios_tsv_out is None else str(scenarios_tsv_out),
        "assessments_tsv": (
            None if assessments_tsv_out is None else str(assessments_tsv_out)
        ),
    }
    _emit_json(payload, out_path=out_path)


@cli.command("protein-coverage")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--fasta",
    "fasta_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option("--threshold", type=float, default=0.05, show_default=True)
@click.option(
    "--score-orientation",
    type=_score_orientation_choice(),
    default=ScoreOrientation.HIGHER_BETTER.value,
    show_default=True,
)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--run-id-column", default=None)
@click.option("--modified-peptide-column", default=None)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--coverage-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--regions-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--uncovered-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--peptide-coordinate-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def protein_coverage_command(
    input_tsv: Path,
    fasta_path: Path,
    threshold: float,
    score_orientation: str,
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    summary_tsv_out: Path | None,
    coverage_tsv_out: Path | None,
    regions_tsv_out: Path | None,
    uncovered_tsv_out: Path | None,
    peptide_coordinate_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Review protein sequence coverage from accepted peptide evidence."""
    try:
        mapping = _build_psm_mapping(
            run_id_column=run_id_column,
            spectrum_id_column=spectrum_id_column,
            peptide_column=peptide_column,
            modified_peptide_column=modified_peptide_column,
            charge_column=charge_column,
            score_column=score_column,
            q_value_column=q_value_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            contaminant_label_column=contaminant_label_column,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        accepted_records = filter_psms_by_fdr(
            report.accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        fasta_report = parse_fasta_document(
            fasta_path.read_text(),
            mode=FastaParseMode.STRICT,
        )
        if fasta_report.rejected_records:
            rejected = ", ".join(
                row.source_identifier for row in fasta_report.rejected_records
            )
            raise click.ClickException(
                f"FASTA input contains rejected records under strict mode: {rejected}"
            )
        protein_sequences = {
            record.canonical_accession: record.residues
            for record in fasta_report.accepted_records
        }
        review = build_protein_coverage_review_report(
            accepted_records,
            protein_sequences=protein_sequences,
            threshold=threshold,
            score_orientation=score_orientation,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_protein_coverage_summary_tsv(review),
        )
    if coverage_tsv_out is not None:
        _write_text_output(
            coverage_tsv_out,
            render_protein_coverage_entries_tsv(review),
        )
    if regions_tsv_out is not None:
        _write_text_output(
            regions_tsv_out,
            render_protein_coverage_regions_tsv(review),
        )
    if uncovered_tsv_out is not None:
        _write_text_output(
            uncovered_tsv_out,
            render_protein_coverage_uncovered_regions_tsv(review),
        )
    if peptide_coordinate_tsv_out is not None:
        _write_text_output(
            peptide_coordinate_tsv_out,
            render_protein_coverage_peptide_coordinates_tsv(review),
        )

    payload = review.to_dict()
    payload["accepted_rows"] = len(accepted_records)
    payload["rejected_rows"] = len(report.rejected_rows)
    payload["outputs"] = {
        "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
        "coverage_tsv": None if coverage_tsv_out is None else str(coverage_tsv_out),
        "regions_tsv": None if regions_tsv_out is None else str(regions_tsv_out),
        "uncovered_tsv": None if uncovered_tsv_out is None else str(uncovered_tsv_out),
        "peptide_coordinate_tsv": (
            None
            if peptide_coordinate_tsv_out is None
            else str(peptide_coordinate_tsv_out)
        ),
    }
    _emit_json(payload, out_path=out_path)


@cli.command("protein-coverage-plot")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--fasta",
    "fasta_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option("--threshold", type=float, default=0.05, show_default=True)
@click.option(
    "--score-orientation",
    type=_score_orientation_choice(),
    default=ScoreOrientation.HIGHER_BETTER.value,
    show_default=True,
)
@click.option("--high-q-value", type=float, default=0.01, show_default=True)
@click.option("--medium-q-value", type=float, default=0.05, show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--run-id-column", default=None)
@click.option("--modified-peptide-column", default=None)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--intensity-column", default=None)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--positions-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--svg-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--html-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def protein_coverage_plot_command(
    input_tsv: Path,
    fasta_path: Path,
    threshold: float,
    score_orientation: str,
    high_q_value: float,
    medium_q_value: float,
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    intensity_column: str | None,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    positions_tsv_out: Path | None,
    svg_out: Path | None,
    html_out: Path | None,
    out_path: Path | None,
) -> None:
    """Build plot-ready peptide-to-protein coverage payloads and static plots."""
    try:
        mapping = _build_psm_mapping(
            run_id_column=run_id_column,
            spectrum_id_column=spectrum_id_column,
            peptide_column=peptide_column,
            modified_peptide_column=modified_peptide_column,
            charge_column=charge_column,
            score_column=score_column,
            q_value_column=q_value_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            contaminant_label_column=contaminant_label_column,
            protein_separator=protein_separator,
            intensity_column=intensity_column,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        accepted_records = _filter_review_psms(
            report.accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        fasta_report = parse_fasta_document(
            fasta_path.read_text(),
            mode=FastaParseMode.STRICT,
        )
        if fasta_report.rejected_records:
            rejected = ", ".join(
                row.source_identifier for row in fasta_report.rejected_records
            )
            raise click.ClickException(
                f"FASTA input contains rejected records under strict mode: {rejected}"
            )
        protein_sequences = {
            record.canonical_accession: record.residues
            for record in fasta_report.accepted_records
        }
        plot = build_protein_coverage_plot_report(
            accepted_records,
            protein_sequences=protein_sequences,
            threshold=threshold,
            score_orientation=score_orientation,
            high_q_value=high_q_value,
            medium_q_value=medium_q_value,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if positions_tsv_out is not None:
        _write_text_output(
            positions_tsv_out,
            render_protein_coverage_plot_positions_tsv(plot),
        )
    if svg_out is not None:
        _write_text_output(svg_out, render_protein_coverage_plot_svg(plot))
    if html_out is not None:
        _write_text_output(html_out, render_protein_coverage_plot_html(plot))

    payload = plot.to_dict()
    payload["accepted_rows"] = len(accepted_records)
    payload["rejected_rows"] = len(report.rejected_rows)
    payload["outputs"] = {
        "positions_tsv": None if positions_tsv_out is None else str(positions_tsv_out),
        "svg": None if svg_out is None else str(svg_out),
        "html": None if html_out is None else str(html_out),
    }
    _emit_json(payload, out_path=out_path)


@cli.command("protein-parsimony")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--threshold", type=float, default=0.05, show_default=True)
@click.option(
    "--score-orientation",
    type=_score_orientation_choice(),
    default=ScoreOrientation.HIGHER_BETTER.value,
    show_default=True,
)
@click.option(
    "--variant",
    type=click.Choice([variant.value for variant in ParsimonyVariant]),
    default=ParsimonyVariant.GREEDY_COVERAGE.value,
    show_default=True,
)
@click.option(
    "--review-variant",
    "review_variants",
    type=click.Choice([variant.value for variant in ParsimonyVariant]),
    multiple=True,
    default=tuple(variant.value for variant in ParsimonyVariant),
    show_default=True,
)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--run-id-column", default=None)
@click.option("--modified-peptide-column", default=None)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--protein-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--ambiguity-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def protein_parsimony_command(
    input_tsv: Path,
    threshold: float,
    score_orientation: str,
    variant: str,
    review_variants: tuple[str, ...],
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    summary_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    ambiguity_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Review one parsimony-selected protein set and its remaining ambiguity."""
    try:
        mapping = _build_psm_mapping(
            run_id_column=run_id_column,
            spectrum_id_column=spectrum_id_column,
            peptide_column=peptide_column,
            modified_peptide_column=modified_peptide_column,
            charge_column=charge_column,
            score_column=score_column,
            q_value_column=q_value_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            contaminant_label_column=contaminant_label_column,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        parse_report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        filtered_records = filter_psms_by_fdr(
            parse_report.accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        review = build_parsimony_review_report(
            filtered_records,
            variant=ParsimonyVariant(variant),
            review_variants=tuple(
                ParsimonyVariant(review_variant) for review_variant in review_variants
            ),
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_parsimony_review_summary_tsv(review),
        )
    if protein_tsv_out is not None:
        _write_text_output(
            protein_tsv_out,
            render_parsimony_review_proteins_tsv(review),
        )
    if ambiguity_tsv_out is not None:
        _write_text_output(
            ambiguity_tsv_out,
            render_parsimony_review_ambiguities_tsv(review),
        )

    payload = {
        "threshold": threshold,
        "score_orientation": score_orientation,
        "accepted_rows": len(parse_report.accepted_records),
        "rejected_rows": len(parse_report.rejected_rows),
        "grouped_rows": len(filtered_records),
        **review.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "protein_tsv": None if protein_tsv_out is None else str(protein_tsv_out),
            "ambiguity_tsv": None
            if ambiguity_tsv_out is None
            else str(ambiguity_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


@cli.command("infer-proteins")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--threshold", type=float, default=0.01, show_default=True)
@click.option(
    "--score-orientation",
    type=_score_orientation_choice(),
    default=ScoreOrientation.HIGHER_BETTER.value,
    show_default=True,
)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--fasta",
    "fasta_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def infer_proteins_command(
    input_tsv: Path,
    threshold: float,
    score_orientation: str,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    fasta_path: Path | None,
    out_path: Path | None,
) -> None:
    """Infer proteins, group evidence, and emit multi-level FDR artifacts."""
    try:
        mapping = _build_psm_mapping(
            run_id_column=None,
            spectrum_id_column=spectrum_id_column,
            peptide_column=peptide_column,
            modified_peptide_column=None,
            charge_column=charge_column,
            score_column=score_column,
            q_value_column=q_value_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            contaminant_label_column=None,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        parse_report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        accepted_records = filter_psms_by_fdr(
            parse_report.accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        level_fdr = calculate_level_specific_fdr(
            parse_report.accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        grouped_charge = calculate_grouped_fdr(
            parse_report.accepted_records,
            group_by="charge_state",
            threshold=threshold,
            score_orientation=score_orientation,
        )
        grouped_modification = calculate_grouped_fdr(
            parse_report.accepted_records,
            group_by="modification_state",
            threshold=threshold,
            score_orientation=score_orientation,
        )
        protein_groups = build_protein_groups(accepted_records)
        confidence_labels = assign_confidence_labels(
            calculate_picked_protein_fdr(
                accepted_records,
                threshold=threshold,
                score_orientation=score_orientation,
                decoy_policy=decoy_policy,
            )
        )
        parsimony = infer_proteins_by_parsimony(accepted_records)
        picked_fdr = calculate_picked_protein_fdr(
            accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
            decoy_policy=decoy_policy,
        )
        protein_sequences: dict[str, str] | None = None
        coverage_payload = None
        uniqueness_payload = None
        if fasta_path is not None:
            fasta_report = parse_fasta_document(
                fasta_path.read_text(), mode=FastaParseMode.STRICT
            )
            if fasta_report.rejected_records:
                rejected = ", ".join(
                    record.source_identifier for record in fasta_report.rejected_records
                )
                raise click.ClickException(
                    f"FASTA input contains rejected records under strict mode: {rejected}"
                )
            protein_sequences = {
                record.canonical_accession: record.residues
                for record in fasta_report.accepted_records
            }
            coverage_payload = [
                entry.to_dict()
                for entry in build_protein_coverage_map(
                    accepted_records,
                    protein_sequences=protein_sequences,
                )
            ]
            uniqueness_payload = [
                entry.to_dict()
                for entry in build_peptide_uniqueness_across_database(
                    tuple(
                        dict.fromkeys(
                            record.canonical_peptide for record in accepted_records
                        )
                    ),
                    protein_records=fasta_report.accepted_records,
                )
            ]
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    payload = {
        "threshold": threshold,
        "score_orientation": score_orientation,
        "input_psms": len(parse_report.accepted_records),
        "accepted_psms": len(accepted_records),
        "level_fdr": level_fdr.to_dict(),
        "grouped_fdr": {
            "charge_state": grouped_charge.to_dict(),
            "modification_state": grouped_modification.to_dict(),
        },
        "protein_groups": [entry.to_dict() for entry in protein_groups],
        "parsimony_proteins": [entry.to_dict() for entry in parsimony],
        "picked_protein_fdr": [entry.to_dict() for entry in picked_fdr],
        "confidence_labels": [entry.to_dict() for entry in confidence_labels],
        "razor_assignments": [
            entry.to_dict() for entry in assign_razor_peptides(accepted_records)
        ],
        "protein_coverage": coverage_payload,
        "database_uniqueness": uniqueness_payload,
    }
    _emit_json(payload, out_path=out_path)


def _parse_timepoint_order_file(path: Path) -> tuple[str, ...]:
    labels: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        label = line.split("\t", 1)[0].strip()
        if label:
            labels.append(label)
    if labels and labels[0].casefold() in {"timepoint", "label"}:
        labels = labels[1:]
    ordered_labels = tuple(labels)
    if not ordered_labels:
        raise ValueError("timepoint order file must contain at least one label")
    return ordered_labels


@cli.command("quantify")
@click.argument(
    "input_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--measure",
    type=_quant_measure_choice(),
    default=QuantMeasureKind.INTENSITY.value,
    show_default=True,
)
@click.option(
    "--entity-level",
    type=_quant_entity_level_choice(),
    default=QuantEntityLevel.PROTEIN.value,
    show_default=True,
)
@click.option(
    "--aggregation",
    type=_quant_rollup_choice(),
    default=QuantRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=3, show_default=True)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option(
    "--imputation",
    type=_imputation_choice(),
    default=ImputationMethod.NONE.value,
    show_default=True,
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--mz-column", default="mz", show_default=True)
@click.option(
    "--retention-time-column", default="retention_time_seconds", show_default=True
)
@click.option("--missing-reason-column", default="missing_reason", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option(
    "--differential-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--broken-pairs-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--batch-effect-summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--batch-effect-batches-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--batch-effect-components-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--time-course-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--design-covariate",
    "design_covariates",
    multiple=True,
)
@click.option(
    "--design-batch-field",
    default="batch",
    show_default=True,
)
@click.option(
    "--design-pairing-field",
    default=None,
)
@click.option(
    "--design-timepoint-field",
    default=None,
)
@click.option(
    "--design-timepoint-order-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--design-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--design-coefficients-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--design-contrasts-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--limma-assay-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--limma-samples-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--limma-design-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--limma-contrasts-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--msstats-input-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--limma-results",
    "limma_results_path",
    type=click.Path(exists=True, path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--msstats-results",
    "msstats_results_path",
    type=click.Path(exists=True, path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--report-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def quantify_command(
    input_table: Path,
    measure: str,
    entity_level: str,
    aggregation: str,
    top_n: int,
    normalization: str,
    imputation: str,
    sample_column: str,
    feature_id_column: str,
    peptide_column: str,
    intensity_column: str,
    protein_refs_column: str | None,
    charge_column: str | None,
    mz_column: str | None,
    retention_time_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    design_path: Path | None,
    condition_a: str | None,
    condition_b: str | None,
    differential_tsv_out: Path | None,
    broken_pairs_tsv_out: Path | None,
    batch_effect_summary_tsv_out: Path | None,
    batch_effect_batches_tsv_out: Path | None,
    batch_effect_components_tsv_out: Path | None,
    time_course_tsv_out: Path | None,
    design_covariates: tuple[str, ...],
    design_batch_field: str,
    design_pairing_field: str | None,
    design_timepoint_field: str | None,
    design_timepoint_order_file: Path | None,
    design_matrix_tsv_out: Path | None,
    design_coefficients_tsv_out: Path | None,
    design_contrasts_tsv_out: Path | None,
    limma_assay_tsv_out: Path | None,
    limma_samples_tsv_out: Path | None,
    limma_design_tsv_out: Path | None,
    limma_contrasts_tsv_out: Path | None,
    msstats_input_tsv_out: Path | None,
    limma_results_path: Path | None,
    msstats_results_path: Path | None,
    report_out: Path | None,
    out_path: Path | None,
) -> None:
    """Build a quantification matrix and optional differential report from MS1 features."""
    try:
        mapping = Ms1FeatureColumnMapping(
            sample_id=sample_column,
            feature_id=feature_id_column,
            peptide=peptide_column,
            intensity=intensity_column,
            protein_refs=protein_refs_column,
            charge=charge_column,
            mz=mz_column,
            retention_time_seconds=retention_time_column,
            missing_reason=missing_reason_column,
            protein_separator=protein_separator,
        )
        parse_report = parse_ms1_feature_table(
            input_table,
            mapping=mapping,
        )
        quant_entity_level = QuantEntityLevel(entity_level)
        quant_measure = QuantMeasureKind(measure)
        rollup_method = QuantRollupMethod(aggregation)
        design_entries: tuple[ExperimentalDesignEntry, ...] = ()
        if design_path is not None:
            design_report = parse_experimental_design_table(design_path)
            if design_report.rejected_rows:
                raise click.ClickException("design table contains rejected rows")
            design_entries = design_report.accepted_entries
        missingness_entity_summary = None
        missingness_condition_summary = None
        missingness_intensity_dependence = None
        missingness_mechanism_report = None
        normalization_comparison = None
        normalization_strategy = None
        imputation_report = None
        imputation_sensitivity = None
        if quant_measure is QuantMeasureKind.SPECTRAL_COUNT:
            table = build_spectral_count_table(
                parse_report.accepted_records,
                entity_level=quant_entity_level,
            )
        else:
            raw_table = build_label_free_intensity_table(
                parse_report.accepted_records,
                entity_level=quant_entity_level,
                aggregation_method=rollup_method,
                top_n=top_n,
            )
            normalization_strategy = build_normalization_strategy_comparison_report(
                raw_table
            )
            normalized_table = normalize_label_free_table(
                raw_table,
                method=NormalizationMethod(normalization),
            )
            normalization_comparison = build_normalization_comparison_report(
                raw_table,
                normalized_table,
            )
            table = impute_label_free_table(
                normalized_table,
                method=ImputationMethod(imputation),
                design_entries=design_entries,
            )
            imputation_report = build_imputation_report(
                normalized_table,
                table,
            )
        missing_summary = summarize_missing_values(table)
        batch_effect = None
        replicate_correlations = None
        replicate_qc = None
        design_matrix = None
        design_model_fit = None
        limma_package = None
        msstats_input_report = None
        time_course_differential = None
        selected_contrast: tuple[str, str] | None = None
        differential = None
        differential_multi_condition = None
        if design_path is not None:
            effective_pairing_field = design_pairing_field
            if effective_pairing_field is None and all(
                entry.pair_id not in (None, "") for entry in design_entries
            ):
                effective_pairing_field = "pair_id"
            effective_covariates = tuple(dict.fromkeys(design_covariates))
            effective_timepoint_field = design_timepoint_field
            if effective_timepoint_field is None and "timepoint" in effective_covariates:
                effective_timepoint_field = "timepoint"
                effective_covariates = tuple(
                    field for field in effective_covariates if field != "timepoint"
                )
            elif effective_timepoint_field is None and all(
                entry.metadata.get("timepoint") not in (None, "")
                for entry in design_entries
            ):
                effective_timepoint_field = "timepoint"
            declared_timepoint_order = (
                _parse_timepoint_order_file(design_timepoint_order_file)
                if design_timepoint_order_file is not None
                else ()
            )
            design_matrix = build_quant_design_matrix_report(
                design_entries,
                batch_field=design_batch_field,
                covariate_fields=effective_covariates,
                pairing_field=effective_pairing_field,
                timepoint_field=effective_timepoint_field,
            )
            design_model_fit = fit_quant_design_matrix_model(
                table,
                design_matrix,
            )
            if quant_measure is QuantMeasureKind.INTENSITY:
                limma_package = build_limma_compatible_quant_package(
                    table,
                    design_entries,
                    batch_field=design_batch_field,
                    covariate_fields=effective_covariates,
                    pairing_field=effective_pairing_field,
                    timepoint_field=effective_timepoint_field,
                )
                msstats_input_report = build_msstats_compatible_input_report(
                    parse_report.accepted_records,
                    design_entries,
                )
            batch_effect = build_batch_effect_estimator_report(
                table,
                design_entries,
                batch_field=design_batch_field or "batch",
            )
            replicate_qc = build_replicate_and_batch_qc_report(
                table,
                design_entries=design_entries,
            )
            replicate_correlations = replicate_qc.replicate_correlation_report
            if effective_timepoint_field is not None:
                time_course_differential = build_time_course_differential_report(
                    table,
                    design_entries,
                    policy=TimeCourseTestingPolicy(
                        timepoint_field=effective_timepoint_field,
                        ordered_timepoints=declared_timepoint_order,
                        batch_field=design_batch_field or None,
                        pairing_field=effective_pairing_field,
                        covariate_fields=effective_covariates,
                    ),
                )
            if quant_measure is QuantMeasureKind.INTENSITY:
                conditions = tuple(
                    sorted({entry.condition for entry in design_entries if entry.condition})
                )
                missingness_classifier = build_missingness_classifier_report(
                    table,
                    design_entries=design_entries,
                )
                missingness_entity_summary = missingness_classifier.entity_summary
                missingness_condition_summary = (
                    missingness_classifier.condition_summary
                )
                missingness_intensity_dependence = (
                    missingness_classifier.intensity_dependence
                )
                missingness_mechanism_report = (
                    missingness_classifier.mechanism_report
                )
                if condition_a is not None or condition_b is not None:
                    if not condition_a or not condition_b:
                        raise click.ClickException(
                            "both --condition-a and --condition-b are required together"
                        )
                    selected_contrast = (condition_a, condition_b)
                elif len(conditions) == 2:
                    selected_contrast = (conditions[0], conditions[1])

                if selected_contrast is not None:
                    sensitivity_methods = (
                        ImputationMethod.NONE,
                        ImputationMethod.LOW_INTENSITY,
                        ImputationMethod.KNN,
                    )
                    selected_imputation_method = ImputationMethod(imputation)
                    if selected_imputation_method is ImputationMethod.GROUP_AWARE_LOW_INTENSITY:
                        sensitivity_methods = sensitivity_methods + (
                            ImputationMethod.GROUP_AWARE_LOW_INTENSITY,
                        )
                    imputation_sensitivity = build_imputation_sensitivity_report(
                        normalized_table,
                        design_entries,
                        condition_a=selected_contrast[0],
                        condition_b=selected_contrast[1],
                        methods=sensitivity_methods,
                    )
                    paired_policy = (
                        PairedDifferentialPolicy(
                            pair_id_field=effective_pairing_field,
                        )
                        if effective_pairing_field is not None
                        else None
                    )
                    differential = build_differential_abundance_report(
                        table,
                        design_entries,
                        condition_a=selected_contrast[0],
                        condition_b=selected_contrast[1],
                        test_type=(
                            DifferentialAbundanceTestType.PAIRED_T_TEST
                            if paired_policy is not None
                            else DifferentialAbundanceTestType.LINEAR_MODEL_CONTRAST
                        ),
                        design_matrix=design_matrix,
                        paired_policy=paired_policy,
                    )
                elif len(conditions) > 2:
                    differential_multi_condition = (
                        build_multi_condition_differential_abundance_report(
                            table,
                            design_entries,
                        )
                    )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if differential_tsv_out is not None:
        if differential is not None:
            export_differential_abundance_tsv(differential, differential_tsv_out)
        elif differential_multi_condition is not None:
            export_multi_condition_differential_abundance_tsv(
                differential_multi_condition,
                differential_tsv_out,
            )
        else:
            raise click.ClickException(
                "differential tsv export requires a resolvable contrast or at least two conditions"
            )
    if broken_pairs_tsv_out is not None:
        if differential is None:
            raise click.ClickException(
                "broken-pair export requires a resolvable two-condition differential contrast"
            )
        export_differential_broken_pairs_tsv(differential, broken_pairs_tsv_out)
    if batch_effect_summary_tsv_out is not None:
        if batch_effect is None:
            raise click.ClickException("batch effect export requires --design")
        export_batch_effect_summary_tsv(batch_effect, batch_effect_summary_tsv_out)
    if batch_effect_batches_tsv_out is not None:
        if batch_effect is None:
            raise click.ClickException("batch effect export requires --design")
        export_batch_effect_batches_tsv(batch_effect, batch_effect_batches_tsv_out)
    if batch_effect_components_tsv_out is not None:
        if batch_effect is None:
            raise click.ClickException("batch effect export requires --design")
        export_batch_effect_principal_components_tsv(
            batch_effect,
            batch_effect_components_tsv_out,
        )
    if time_course_tsv_out is not None:
        if time_course_differential is None:
            raise click.ClickException(
                "time-course export requires --design with populated ordered timepoint metadata"
            )
        export_time_course_differential_tsv(
            time_course_differential,
            time_course_tsv_out,
        )
    if design_matrix_tsv_out is not None:
        if design_matrix is None:
            raise click.ClickException("design matrix export requires --design")
        export_quant_design_matrix_tsv(design_matrix, design_matrix_tsv_out)
    if design_coefficients_tsv_out is not None:
        if design_model_fit is None:
            raise click.ClickException("design coefficient export requires --design")
        export_quant_design_model_coefficients_tsv(
            design_model_fit,
            design_coefficients_tsv_out,
        )
    if design_contrasts_tsv_out is not None:
        if design_model_fit is None:
            raise click.ClickException("design contrast export requires --design")
        export_quant_design_contrast_estimates_tsv(
            design_model_fit,
            design_contrasts_tsv_out,
        )
    if limma_assay_tsv_out is not None:
        if limma_package is None:
            raise click.ClickException(
                "limma assay export requires intensity quantification with --design"
            )
        export_limma_assay_matrix_tsv(limma_package, limma_assay_tsv_out)
    if limma_samples_tsv_out is not None:
        if limma_package is None:
            raise click.ClickException(
                "limma sample export requires intensity quantification with --design"
            )
        export_limma_sample_annotations_tsv(limma_package, limma_samples_tsv_out)
    if limma_design_tsv_out is not None:
        if limma_package is None:
            raise click.ClickException(
                "limma design export requires intensity quantification with --design"
            )
        export_limma_design_matrix_tsv(limma_package, limma_design_tsv_out)
    if limma_contrasts_tsv_out is not None:
        if limma_package is None:
            raise click.ClickException(
                "limma contrast export requires intensity quantification with --design"
            )
        export_limma_contrast_matrix_tsv(limma_package, limma_contrasts_tsv_out)
    if msstats_input_tsv_out is not None:
        if msstats_input_report is None:
            raise click.ClickException(
                "msstats input export requires intensity quantification with --design"
            )
        export_msstats_compatible_input_tsv(
            msstats_input_report,
            msstats_input_tsv_out,
        )
    limma_result_import = None
    limma_validation = None
    if limma_results_path is not None:
        if selected_contrast is None or differential is None:
            raise click.ClickException(
                "limma result import requires intensity quantification with --design and a resolvable contrast"
            )
        limma_result_import = parse_limma_result_table(
            limma_results_path,
            condition_a=selected_contrast[0],
            condition_b=selected_contrast[1],
        )
        limma_validation = build_statistical_backend_validation_report(
            limma_result_import,
            differential,
        )
    msstats_result_import = None
    msstats_validation = None
    if msstats_results_path is not None:
        if selected_contrast is None or differential is None:
            raise click.ClickException(
                "msstats result import requires intensity quantification with --design and a resolvable contrast"
            )
        msstats_result_import = parse_msstats_result_table(
            msstats_results_path,
            condition_a=selected_contrast[0],
            condition_b=selected_contrast[1],
        )
        msstats_validation = build_statistical_backend_validation_report(
            msstats_result_import,
            differential,
        )

    payload = {
        "accepted_features": len(parse_report.accepted_records),
        "rejected_features": len(parse_report.rejected_rows),
        "table": table.to_dict(),
        "missing_summary": missing_summary.to_dict(),
        "missingness_entity_summary": (
            missingness_entity_summary.to_dict()
            if missingness_entity_summary is not None
            else None
        ),
        "missingness_condition_summary": (
            missingness_condition_summary.to_dict()
            if missingness_condition_summary is not None
            else None
        ),
        "missingness_intensity_dependence": (
            missingness_intensity_dependence.to_dict()
            if missingness_intensity_dependence is not None
            else None
        ),
        "missingness_mechanism_report": (
            missingness_mechanism_report.to_dict()
            if missingness_mechanism_report is not None
            else None
        ),
        "normalization_comparison": (
            normalization_comparison.to_dict()
            if normalization_comparison is not None
            else None
        ),
        "normalization_strategy": (
            normalization_strategy.to_dict()
            if normalization_strategy is not None
            else None
        ),
        "imputation_report": (
            imputation_report.to_dict() if imputation_report is not None else None
        ),
        "imputation_sensitivity": (
            imputation_sensitivity.to_dict()
            if imputation_sensitivity is not None
            else None
        ),
        "design_entries": len(design_entries),
        "design_matrix": design_matrix.to_dict() if design_matrix is not None else None,
        "design_model_fit": (
            design_model_fit.to_dict() if design_model_fit is not None else None
        ),
        "limma_compatible_package": (
            limma_package.to_dict() if limma_package is not None else None
        ),
        "msstats_compatible_input_report": (
            msstats_input_report.to_dict()
            if msstats_input_report is not None
            else None
        ),
        "limma_result_import": (
            limma_result_import.to_dict() if limma_result_import is not None else None
        ),
        "limma_validation": (
            limma_validation.to_dict() if limma_validation is not None else None
        ),
        "msstats_result_import": (
            msstats_result_import.to_dict()
            if msstats_result_import is not None
            else None
        ),
        "msstats_validation": (
            msstats_validation.to_dict() if msstats_validation is not None else None
        ),
        "batch_effect": batch_effect.to_dict() if batch_effect is not None else None,
        "replicate_correlations": (
            replicate_correlations.to_dict()
            if replicate_correlations is not None
            else None
        ),
        "replicate_qc": replicate_qc.to_dict() if replicate_qc is not None else None,
        "replicate_cv": (
            replicate_qc.replicate_cv_report.to_dict()
            if replicate_qc is not None
            else None
        ),
        "sample_pca": (
            replicate_qc.sample_pca_report.to_dict()
            if replicate_qc is not None and replicate_qc.sample_pca_report is not None
            else None
        ),
        "condition_clustering": (
            replicate_qc.condition_clustering_report.to_dict()
            if replicate_qc is not None
            and replicate_qc.condition_clustering_report is not None
            else None
        ),
        "differential_abundance_multi_condition": (
            differential_multi_condition.to_dict()
            if differential_multi_condition is not None
            else None
        ),
        "time_course_differential": (
            time_course_differential.to_dict()
            if time_course_differential is not None
            else None
        ),
        "differential_abundance": differential.to_dict()
        if differential is not None
        else None,
        "outputs": {
            "differential_tsv": (
                str(differential_tsv_out)
                if differential_tsv_out is not None
                else None
            ),
            "broken_pairs_tsv": (
                str(broken_pairs_tsv_out)
                if broken_pairs_tsv_out is not None
                else None
            ),
            "batch_effect_summary_tsv": (
                str(batch_effect_summary_tsv_out)
                if batch_effect_summary_tsv_out is not None
                else None
            ),
            "batch_effect_batches_tsv": (
                str(batch_effect_batches_tsv_out)
                if batch_effect_batches_tsv_out is not None
                else None
            ),
            "batch_effect_components_tsv": (
                str(batch_effect_components_tsv_out)
                if batch_effect_components_tsv_out is not None
                else None
            ),
            "time_course_tsv": (
                str(time_course_tsv_out)
                if time_course_tsv_out is not None
                else None
            ),
            "design_matrix_tsv": (
                str(design_matrix_tsv_out)
                if design_matrix_tsv_out is not None
                else None
            ),
            "design_coefficients_tsv": (
                str(design_coefficients_tsv_out)
                if design_coefficients_tsv_out is not None
                else None
            ),
            "design_contrasts_tsv": (
                str(design_contrasts_tsv_out)
                if design_contrasts_tsv_out is not None
                else None
            ),
            "limma_assay_tsv": (
                str(limma_assay_tsv_out) if limma_assay_tsv_out is not None else None
            ),
            "limma_samples_tsv": (
                str(limma_samples_tsv_out)
                if limma_samples_tsv_out is not None
                else None
            ),
            "limma_design_tsv": (
                str(limma_design_tsv_out)
                if limma_design_tsv_out is not None
                else None
            ),
            "limma_contrasts_tsv": (
                str(limma_contrasts_tsv_out)
                if limma_contrasts_tsv_out is not None
                else None
            ),
            "msstats_input_tsv": (
                str(msstats_input_tsv_out)
                if msstats_input_tsv_out is not None
                else None
            ),
            "json_report": str(report_out or out_path)
            if (report_out or out_path) is not None
            else None,
        },
    }
    _emit_json(payload, out_path=report_out or out_path)


@cli.command("heatmap-matrix")
@click.argument(
    "input_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--entity-level",
    type=_quant_entity_level_choice(),
    default=QuantEntityLevel.PROTEIN.value,
    show_default=True,
)
@click.option(
    "--aggregation",
    type=_quant_rollup_choice(),
    default=QuantRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=3, show_default=True)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--mz-column", default="mz", show_default=True)
@click.option(
    "--retention-time-column", default="retention_time_seconds", show_default=True
)
@click.option("--missing-reason-column", default="missing_reason", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--entity-id", "entity_ids", multiple=True)
@click.option("--protein-ref", "protein_refs", multiple=True)
@click.option(
    "--min-observed-fraction",
    type=float,
    default=0.5,
    show_default=True,
)
@click.option("--max-entities", type=int, default=None)
@click.option("--z-score/--no-z-score", default=True, show_default=True)
@click.option(
    "--missing-value-policy",
    type=_heatmap_missing_value_choice(),
    default=HeatmapMissingValuePolicy.FILL_ROW_MEDIAN.value,
    show_default=True,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--row-metadata-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--column-metadata-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def heatmap_matrix_command(
    input_table: Path,
    entity_level: str,
    aggregation: str,
    top_n: int,
    normalization: str,
    sample_column: str,
    feature_id_column: str,
    peptide_column: str,
    intensity_column: str,
    protein_refs_column: str | None,
    charge_column: str | None,
    mz_column: str | None,
    retention_time_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    design_path: Path | None,
    entity_ids: tuple[str, ...],
    protein_refs: tuple[str, ...],
    min_observed_fraction: float,
    max_entities: int | None,
    z_score: bool,
    missing_value_policy: str,
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    row_metadata_tsv_out: Path | None,
    column_metadata_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Prepare one normalized matrix for heatmaps and clustering."""

    try:
        mapping = Ms1FeatureColumnMapping(
            sample_id=sample_column,
            feature_id=feature_id_column,
            peptide=peptide_column,
            intensity=intensity_column,
            protein_refs=protein_refs_column,
            charge=charge_column,
            mz=mz_column,
            retention_time_seconds=retention_time_column,
            missing_reason=missing_reason_column,
            protein_separator=protein_separator,
        )
        parse_report = parse_ms1_feature_table(input_table, mapping=mapping)
        design_entries: tuple[ExperimentalDesignEntry, ...] = ()
        if design_path is not None:
            design_report = parse_experimental_design_table(design_path)
            if design_report.rejected_rows:
                raise click.ClickException("design table contains rejected rows")
            design_entries = design_report.accepted_entries
        raw_table = build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel(entity_level),
            aggregation_method=QuantRollupMethod(aggregation),
            top_n=top_n,
        )
        report = build_heatmap_preparation_report(
            normalize_label_free_table(
                raw_table,
                method=NormalizationMethod(normalization),
            ),
            design_entries=design_entries,
            policy=HeatmapPreparationPolicy(
                entity_ids=tuple(dict.fromkeys(entity_ids)),
                protein_refs=tuple(dict.fromkeys(protein_refs)),
                min_observed_fraction=min_observed_fraction,
                max_entity_count=max_entities,
                z_score_rows=z_score,
                missing_value_policy=HeatmapMissingValuePolicy(
                    missing_value_policy.lower()
                ),
            ),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_heatmap_summary_tsv(report, summary_tsv_out)
    if matrix_tsv_out is not None:
        export_heatmap_matrix_tsv(report, matrix_tsv_out)
    if row_metadata_tsv_out is not None:
        export_heatmap_row_metadata_tsv(report, row_metadata_tsv_out)
    if column_metadata_tsv_out is not None:
        export_heatmap_column_metadata_tsv(report, column_metadata_tsv_out)

    _emit_json(
        {
            "accepted_features": len(parse_report.accepted_records),
            "rejected_features": len(parse_report.rejected_rows),
            "heatmap_report": report.to_dict(),
            "outputs": {
                "summary_tsv": (
                    None if summary_tsv_out is None else str(summary_tsv_out)
                ),
                "matrix_tsv": None if matrix_tsv_out is None else str(matrix_tsv_out),
                "row_metadata_tsv": (
                    None
                    if row_metadata_tsv_out is None
                    else str(row_metadata_tsv_out)
                ),
                "column_metadata_tsv": (
                    None
                    if column_metadata_tsv_out is None
                    else str(column_metadata_tsv_out)
                ),
            },
        },
        out_path=out_path,
    )


@cli.command("power-estimate")
@click.argument(
    "input_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--entity-level",
    type=_quant_entity_level_choice(),
    default=QuantEntityLevel.PROTEIN.value,
    show_default=True,
)
@click.option(
    "--aggregation",
    type=_quant_rollup_choice(),
    default=QuantRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=3, show_default=True)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--mz-column", default="mz", show_default=True)
@click.option(
    "--retention-time-column", default="retention_time_seconds", show_default=True
)
@click.option("--missing-reason-column", default="missing_reason", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--fdr-target", type=float, default=0.05, show_default=True)
@click.option("--target-power", type=float, default=0.8, show_default=True)
@click.option(
    "--replicates-per-condition",
    "replicate_counts",
    type=int,
    multiple=True,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--variance-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--effect-size-grid-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def power_estimate_command(
    input_table: Path,
    entity_level: str,
    aggregation: str,
    top_n: int,
    normalization: str,
    sample_column: str,
    feature_id_column: str,
    peptide_column: str,
    intensity_column: str,
    protein_refs_column: str | None,
    charge_column: str | None,
    mz_column: str | None,
    retention_time_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    design_path: Path | None,
    fdr_target: float,
    target_power: float,
    replicate_counts: tuple[int, ...],
    summary_tsv_out: Path | None,
    variance_tsv_out: Path | None,
    effect_size_grid_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Estimate pilot variance and detectable effect sizes across replicate counts."""

    try:
        mapping = Ms1FeatureColumnMapping(
            sample_id=sample_column,
            feature_id=feature_id_column,
            peptide=peptide_column,
            intensity=intensity_column,
            protein_refs=protein_refs_column,
            charge=charge_column,
            mz=mz_column,
            retention_time_seconds=retention_time_column,
            missing_reason=missing_reason_column,
            protein_separator=protein_separator,
        )
        parse_report = parse_ms1_feature_table(input_table, mapping=mapping)
        design_entries: tuple[ExperimentalDesignEntry, ...] = ()
        if design_path is not None:
            design_report = parse_experimental_design_table(design_path)
            if design_report.rejected_rows:
                raise click.ClickException("design table contains rejected rows")
            design_entries = design_report.accepted_entries
        raw_table = build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel(entity_level),
            aggregation_method=QuantRollupMethod(aggregation),
            top_n=top_n,
        )
        report = build_power_estimation_report(
            normalize_label_free_table(
                raw_table,
                method=NormalizationMethod(normalization),
            ),
            design_entries,
            policy=PowerEstimationPolicy(
                fdr_target=fdr_target,
                target_power=target_power,
                candidate_replicates_per_condition=replicate_counts,
            ),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_power_estimation_summary_tsv(report, summary_tsv_out)
    if variance_tsv_out is not None:
        export_power_variance_tsv(report, variance_tsv_out)
    if effect_size_grid_tsv_out is not None:
        export_power_effect_size_grid_tsv(report, effect_size_grid_tsv_out)

    _emit_json(
        {
            "accepted_features": len(parse_report.accepted_records),
            "rejected_features": len(parse_report.rejected_rows),
            "power_estimation_report": report.to_dict(),
            "outputs": {
                "summary_tsv": (
                    None if summary_tsv_out is None else str(summary_tsv_out)
                ),
                "variance_tsv": (
                    None if variance_tsv_out is None else str(variance_tsv_out)
                ),
                "effect_size_grid_tsv": (
                    None
                    if effect_size_grid_tsv_out is None
                    else str(effect_size_grid_tsv_out)
                ),
            },
        },
        out_path=out_path,
    )


@cli.command("sample-exploration")
@click.argument(
    "input_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--entity-level",
    type=_quant_entity_level_choice(),
    default=QuantEntityLevel.PROTEIN.value,
    show_default=True,
)
@click.option(
    "--aggregation",
    type=_quant_rollup_choice(),
    default=QuantRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=3, show_default=True)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option(
    "--retention-time-column", default="retention_time_seconds", show_default=True
)
@click.option("--mz-column", default="mz", show_default=True)
@click.option("--missing-reason-column", default="missing_reason", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--scores-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--explained-variance-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--distances-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--correlations-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--clusters-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--outliers-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def sample_exploration_command(
    input_table: Path,
    entity_level: str,
    aggregation: str,
    top_n: int,
    normalization: str,
    sample_column: str,
    feature_id_column: str,
    peptide_column: str,
    intensity_column: str,
    protein_refs_column: str | None,
    charge_column: str | None,
    retention_time_column: str | None,
    mz_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    design_path: Path | None,
    summary_tsv_out: Path | None,
    scores_tsv_out: Path | None,
    explained_variance_tsv_out: Path | None,
    distances_tsv_out: Path | None,
    correlations_tsv_out: Path | None,
    clusters_tsv_out: Path | None,
    outliers_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Prepare sample-level PCA, correlation, distance, clustering, and outlier outputs."""

    try:
        mapping = Ms1FeatureColumnMapping(
            sample_id=sample_column,
            feature_id=feature_id_column,
            peptide=peptide_column,
            intensity=intensity_column,
            protein_refs=protein_refs_column,
            charge=charge_column,
            mz=mz_column,
            retention_time_seconds=retention_time_column,
            missing_reason=missing_reason_column,
            protein_separator=protein_separator,
        )
        parse_report = parse_ms1_feature_table(input_table, mapping=mapping)
        design_entries: tuple[ExperimentalDesignEntry, ...] = ()
        if design_path is not None:
            design_report = parse_experimental_design_table(design_path)
            if design_report.rejected_rows:
                raise click.ClickException("design table contains rejected rows")
            design_entries = design_report.accepted_entries
        raw_table = build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel(entity_level),
            aggregation_method=QuantRollupMethod(aggregation),
            top_n=top_n,
        )
        report = build_sample_exploration_report(
            normalize_label_free_table(
                raw_table,
                method=NormalizationMethod(normalization),
            ),
            design_entries,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_sample_exploration_summary_tsv(report, summary_tsv_out)
    if scores_tsv_out is not None:
        export_sample_pca_scores_tsv(report, scores_tsv_out)
    if explained_variance_tsv_out is not None:
        export_sample_pca_variance_tsv(report, explained_variance_tsv_out)
    if distances_tsv_out is not None:
        export_sample_distance_tsv(report, distances_tsv_out)
    if correlations_tsv_out is not None:
        export_sample_correlation_tsv(report, correlations_tsv_out)
    if clusters_tsv_out is not None:
        export_sample_cluster_tsv(report, clusters_tsv_out)
    if outliers_tsv_out is not None:
        export_sample_outlier_tsv(report, outliers_tsv_out)

    _emit_json(
        {
            "accepted_features": len(parse_report.accepted_records),
            "rejected_features": len(parse_report.rejected_rows),
            "sample_exploration_report": report.to_dict(),
            "outputs": {
                "summary_tsv": (
                    None if summary_tsv_out is None else str(summary_tsv_out)
                ),
                "scores_tsv": None if scores_tsv_out is None else str(scores_tsv_out),
                "explained_variance_tsv": (
                    None
                    if explained_variance_tsv_out is None
                    else str(explained_variance_tsv_out)
                ),
                "distances_tsv": (
                    None if distances_tsv_out is None else str(distances_tsv_out)
                ),
                "correlations_tsv": (
                    None
                    if correlations_tsv_out is None
                    else str(correlations_tsv_out)
                ),
                "clusters_tsv": (
                    None if clusters_tsv_out is None else str(clusters_tsv_out)
                ),
                "outliers_tsv": (
                    None if outliers_tsv_out is None else str(outliers_tsv_out)
                ),
            },
        },
        out_path=out_path,
    )


@cli.command("biological-report")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--context-annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--go-annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--pathway-membership-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--complex-membership-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--aggregation",
    type=_quant_rollup_choice(),
    default=QuantRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=3, show_default=True)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--mz-column", default="mz", show_default=True)
@click.option(
    "--retention-time-column",
    default="retention_time_seconds",
    show_default=True,
)
@click.option("--missing-reason-column", default="missing_reason", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option(
    "--max-adjusted-p-value",
    type=float,
    default=0.1,
    show_default=True,
)
@click.option(
    "--min-absolute-log2-fold-change",
    type=float,
    default=1.0,
    show_default=True,
)
@click.option(
    "--heatmap-max-entities",
    type=int,
    default=50,
    show_default=True,
)
@click.option(
    "--heatmap-min-observed-fraction",
    type=float,
    default=0.5,
    show_default=True,
)
@click.option(
    "--volcano-top-label-count",
    type=int,
    default=10,
    show_default=True,
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path, file_okay=False),
    default=Path("biological_report"),
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def biological_report_command(
    input_tsv: Path,
    design_tsv: Path,
    proteins_fasta: Path,
    annotation_tsv: Path | None,
    context_annotation_tsv: Path | None,
    go_annotation_tsv: Path | None,
    pathway_membership_tsv: Path | None,
    complex_membership_tsv: Path | None,
    aggregation: str,
    top_n: int,
    normalization: str,
    sample_column: str,
    feature_id_column: str,
    peptide_column: str,
    intensity_column: str,
    protein_refs_column: str | None,
    charge_column: str | None,
    mz_column: str | None,
    retention_time_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    condition_a: str | None,
    condition_b: str | None,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
    heatmap_max_entities: int,
    heatmap_min_observed_fraction: float,
    volcano_top_label_count: int,
    output_dir: Path,
    out_path: Path | None,
) -> None:
    """Build one biological interpretation report bundle over governed LFQ results."""

    result = _run_orchestrated_workflow(
        LabelFreeWorkflowConfig(
            input_tsv_path=input_tsv,
            design_tsv_path=design_tsv,
            proteins_fasta_path=proteins_fasta,
            annotation_tsv_path=annotation_tsv,
            context_annotation_tsv_path=context_annotation_tsv,
            go_annotation_tsv_path=go_annotation_tsv,
            pathway_membership_tsv_path=pathway_membership_tsv,
            complex_membership_tsv_path=complex_membership_tsv,
            mapping=Ms1FeatureColumnMapping(
                sample_id=sample_column,
                feature_id=feature_id_column,
                peptide=peptide_column,
                intensity=intensity_column,
                protein_refs=protein_refs_column,
                charge=charge_column,
                mz=mz_column,
                retention_time_seconds=retention_time_column,
                missing_reason=missing_reason_column,
                protein_separator=protein_separator,
            ),
            aggregation_method=QuantRollupMethod(aggregation),
            top_n=top_n,
            normalization_method=NormalizationMethod(normalization),
            condition_a=condition_a,
            condition_b=condition_b,
            selection_policy=BiologicalResultSelectionPolicy(
                max_adjusted_p_value=max_adjusted_p_value,
                min_absolute_log2_fold_change=min_absolute_log2_fold_change,
                heatmap_max_entity_count=heatmap_max_entities,
                heatmap_min_observed_fraction=heatmap_min_observed_fraction,
            ),
            volcano_policy=_build_volcano_review_policy(
                adjusted_p_value_threshold=max_adjusted_p_value,
                absolute_log2_fold_change_threshold=min_absolute_log2_fold_change,
                top_label_count=volcano_top_label_count,
            ),
            output_dir=output_dir,
        )
    )
    report = result.report
    manifest = result.export_manifest
    if manifest is None:
        raise click.ClickException("workflow export manifest was not produced")

    _emit_json(
        {
            "design_rows": result.design_row_count,
            "report": report.to_dict(),
            "export_manifest": manifest.to_dict(),
            "outputs": result.outputs,
        },
        out_path=out_path,
    )


@cli.command("dda-biological-report")
@click.argument(
    "search_result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--adapter-kind",
    type=click.Choice(
        (
            SearchAdapterKind.COMET.value,
            SearchAdapterKind.MSFRAGGER.value,
            SearchAdapterKind.SAGE.value,
            SearchAdapterKind.MAXQUANT_EVIDENCE.value,
            SearchAdapterKind.GENERIC.value,
        )
    ),
    default=SearchAdapterKind.GENERIC.value,
    show_default=True,
)
@click.option("--dialect-id", default="default", show_default=True)
@click.option(
    "--mapping-path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--source-protein-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--go-annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--pathway-membership-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--complex-membership-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--psm-q-value-threshold",
    type=float,
    default=0.01,
    show_default=True,
)
@click.option(
    "--parsimony-variant",
    type=click.Choice([variant.value for variant in ParsimonyVariant]),
    default=ParsimonyVariant.GREEDY_COVERAGE.value,
    show_default=True,
)
@click.option(
    "--aggregation",
    type=_quant_rollup_choice(),
    default=QuantRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=3, show_default=True)
@click.option(
    "--minimum-shared-peptides",
    type=int,
    default=1,
    show_default=True,
)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option(
    "--max-adjusted-p-value",
    type=float,
    default=0.1,
    show_default=True,
)
@click.option(
    "--min-absolute-log2-fold-change",
    type=float,
    default=1.0,
    show_default=True,
)
@click.option(
    "--heatmap-max-entities",
    type=int,
    default=50,
    show_default=True,
)
@click.option(
    "--heatmap-min-observed-fraction",
    type=float,
    default=0.5,
    show_default=True,
)
@click.option(
    "--volcano-top-label-count",
    type=int,
    default=10,
    show_default=True,
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path, file_okay=False),
    default=Path("dda_biological_report"),
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def dda_biological_report_command(
    search_result_tsv: Path,
    design_tsv: Path,
    proteins_fasta: Path,
    adapter_kind: str,
    dialect_id: str,
    mapping_path: Path | None,
    source_protein_tsv: Path | None,
    annotation_tsv: Path | None,
    go_annotation_tsv: Path | None,
    pathway_membership_tsv: Path | None,
    complex_membership_tsv: Path | None,
    psm_q_value_threshold: float,
    parsimony_variant: str,
    aggregation: str,
    top_n: int,
    minimum_shared_peptides: int,
    normalization: str,
    condition_a: str | None,
    condition_b: str | None,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
    heatmap_max_entities: int,
    heatmap_min_observed_fraction: float,
    volcano_top_label_count: int,
    output_dir: Path,
    out_path: Path | None,
) -> None:
    """Build one DDA search-result-to-biology report bundle."""

    result = _run_orchestrated_workflow(
        DdaWorkflowConfig(
            mode=WorkflowMode.GENERIC_PSM,
            search_result_tsv_path=search_result_tsv,
            design_tsv_path=design_tsv,
            proteins_fasta_path=proteins_fasta,
            adapter_kind=SearchAdapterKind(adapter_kind),
            generic_mapping_path=mapping_path,
            dialect_id=dialect_id,
            source_protein_tsv_path=source_protein_tsv,
            annotation_tsv_path=annotation_tsv,
            go_annotation_tsv_path=go_annotation_tsv,
            pathway_membership_tsv_path=pathway_membership_tsv,
            complex_membership_tsv_path=complex_membership_tsv,
            psm_q_value_threshold=psm_q_value_threshold,
            parsimony_variant=ParsimonyVariant(parsimony_variant),
            aggregation_method=QuantRollupMethod(aggregation),
            top_n=top_n,
            minimum_shared_peptides=minimum_shared_peptides,
            normalization_method=NormalizationMethod(normalization),
            condition_a=condition_a,
            condition_b=condition_b,
            selection_policy=BiologicalResultSelectionPolicy(
                max_adjusted_p_value=max_adjusted_p_value,
                min_absolute_log2_fold_change=min_absolute_log2_fold_change,
                heatmap_max_entity_count=heatmap_max_entities,
                heatmap_min_observed_fraction=heatmap_min_observed_fraction,
            ),
            volcano_policy=_build_volcano_review_policy(
                adjusted_p_value_threshold=max_adjusted_p_value,
                absolute_log2_fold_change_threshold=min_absolute_log2_fold_change,
                top_label_count=volcano_top_label_count,
            ),
            output_dir=output_dir,
        )
    )
    report = result.report
    manifest = result.export_manifest
    if manifest is None:
        raise click.ClickException("workflow export manifest was not produced")

    _emit_json(
        {
            "design_rows": result.design_row_count,
            "report": report.to_dict(),
            "export_manifest": manifest.to_dict(),
            "outputs": result.outputs,
        },
        out_path=out_path,
    )


@cli.command("diann-biological-report")
@click.argument(
    "result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--config-path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--context-annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--go-annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--pathway-membership-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--complex-membership-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--max-q-value",
    type=float,
    default=0.01,
    show_default=True,
)
@click.option(
    "--peptide-rollup",
    type=click.Choice([method.value for method in DiaPeptideRollupMethod]),
    default=DiaPeptideRollupMethod.MAX.value,
    show_default=True,
)
@click.option(
    "--target-kind",
    type=click.Choice([kind.value for kind in DiaProteinMatrixTargetKind]),
    default=DiaProteinMatrixTargetKind.PROTEIN_GROUP.value,
    show_default=True,
)
@click.option(
    "--shared-peptide-policy",
    type=click.Choice([policy.value for policy in DiaSharedPeptidePolicy]),
    default=DiaSharedPeptidePolicy.INCLUDE.value,
    show_default=True,
)
@click.option(
    "--protein-rollup",
    type=click.Choice([method.value for method in DiaProteinRollupMethod]),
    default=DiaProteinRollupMethod.SUM.value,
    show_default=True,
)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option(
    "--max-adjusted-p-value",
    type=float,
    default=0.1,
    show_default=True,
)
@click.option(
    "--min-absolute-log2-fold-change",
    type=float,
    default=1.0,
    show_default=True,
)
@click.option(
    "--heatmap-max-entities",
    type=int,
    default=50,
    show_default=True,
)
@click.option(
    "--heatmap-min-observed-fraction",
    type=float,
    default=0.5,
    show_default=True,
)
@click.option(
    "--volcano-top-label-count",
    type=int,
    default=10,
    show_default=True,
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path, file_okay=False),
    default=Path("diann_biological_report"),
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def diann_biological_report_command(
    result_tsv: Path,
    design_tsv: Path,
    proteins_fasta: Path,
    config_path: Path | None,
    annotation_tsv: Path | None,
    context_annotation_tsv: Path | None,
    go_annotation_tsv: Path | None,
    pathway_membership_tsv: Path | None,
    complex_membership_tsv: Path | None,
    max_q_value: float,
    peptide_rollup: str,
    target_kind: str,
    shared_peptide_policy: str,
    protein_rollup: str,
    normalization: str,
    condition_a: str | None,
    condition_b: str | None,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
    heatmap_max_entities: int,
    heatmap_min_observed_fraction: float,
    volcano_top_label_count: int,
    output_dir: Path,
    out_path: Path | None,
) -> None:
    """Build one DIA-NN-to-biology report bundle."""

    result = _run_orchestrated_workflow(
        DiannWorkflowConfig(
            result_tsv_path=result_tsv,
            design_tsv_path=design_tsv,
            proteins_fasta_path=proteins_fasta,
            config_path=config_path,
            annotation_tsv_path=annotation_tsv,
            context_annotation_tsv_path=context_annotation_tsv,
            go_annotation_tsv_path=go_annotation_tsv,
            pathway_membership_tsv_path=pathway_membership_tsv,
            complex_membership_tsv_path=complex_membership_tsv,
            max_q_value=max_q_value,
            peptide_rollup_method=DiaPeptideRollupMethod(peptide_rollup),
            target_kind=DiaProteinMatrixTargetKind(target_kind),
            shared_peptide_policy=DiaSharedPeptidePolicy(shared_peptide_policy),
            protein_rollup_method=DiaProteinRollupMethod(protein_rollup),
            normalization_method=NormalizationMethod(normalization),
            condition_a=condition_a,
            condition_b=condition_b,
            selection_policy=BiologicalResultSelectionPolicy(
                max_adjusted_p_value=max_adjusted_p_value,
                min_absolute_log2_fold_change=min_absolute_log2_fold_change,
                heatmap_max_entity_count=heatmap_max_entities,
                heatmap_min_observed_fraction=heatmap_min_observed_fraction,
            ),
            volcano_policy=_build_volcano_review_policy(
                adjusted_p_value_threshold=max_adjusted_p_value,
                absolute_log2_fold_change_threshold=min_absolute_log2_fold_change,
                top_label_count=volcano_top_label_count,
            ),
            output_dir=output_dir,
        )
    )
    report = result.report
    manifest = result.export_manifest
    if manifest is None:
        raise click.ClickException("workflow export manifest was not produced")

    _emit_json(
        {
            "design_rows": result.design_row_count,
            "report": report.to_dict(),
            "export_manifest": manifest.to_dict(),
            "outputs": result.outputs,
        },
        out_path=out_path,
    )


@cli.command("maxquant-biological-report")
@click.argument(
    "evidence_txt", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "peptides_txt", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "protein_groups_txt",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "design_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--config-path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--context-annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--go-annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--pathway-membership-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--complex-membership-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--include-only-identified-by-site/--exclude-only-identified-by-site",
    default=False,
    show_default=True,
)
@click.option(
    "--allow-empty-lfq-signal/--require-lfq-signal",
    default=False,
    show_default=True,
)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option(
    "--max-adjusted-p-value",
    type=float,
    default=0.1,
    show_default=True,
)
@click.option(
    "--min-absolute-log2-fold-change",
    type=float,
    default=1.0,
    show_default=True,
)
@click.option(
    "--heatmap-max-entities",
    type=int,
    default=50,
    show_default=True,
)
@click.option(
    "--heatmap-min-observed-fraction",
    type=float,
    default=0.5,
    show_default=True,
)
@click.option(
    "--volcano-top-label-count",
    type=int,
    default=10,
    show_default=True,
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path, file_okay=False),
    default=Path("maxquant_biological_report"),
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def maxquant_biological_report_command(
    evidence_txt: Path,
    peptides_txt: Path,
    protein_groups_txt: Path,
    design_tsv: Path,
    proteins_fasta: Path,
    config_path: Path | None,
    annotation_tsv: Path | None,
    context_annotation_tsv: Path | None,
    go_annotation_tsv: Path | None,
    pathway_membership_tsv: Path | None,
    complex_membership_tsv: Path | None,
    include_only_identified_by_site: bool,
    allow_empty_lfq_signal: bool,
    normalization: str,
    condition_a: str | None,
    condition_b: str | None,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
    heatmap_max_entities: int,
    heatmap_min_observed_fraction: float,
    volcano_top_label_count: int,
    output_dir: Path,
    out_path: Path | None,
) -> None:
    """Build one MaxQuant-to-biology report bundle."""

    result = _run_orchestrated_workflow(
        MaxquantWorkflowConfig(
            evidence_txt_path=evidence_txt,
            peptides_txt_path=peptides_txt,
            protein_groups_txt_path=protein_groups_txt,
            design_tsv_path=design_tsv,
            proteins_fasta_path=proteins_fasta,
            config_path=config_path,
            annotation_tsv_path=annotation_tsv,
            context_annotation_tsv_path=context_annotation_tsv,
            go_annotation_tsv_path=go_annotation_tsv,
            pathway_membership_tsv_path=pathway_membership_tsv,
            complex_membership_tsv_path=complex_membership_tsv,
            include_only_identified_by_site=include_only_identified_by_site,
            allow_empty_lfq_signal=allow_empty_lfq_signal,
            normalization_method=NormalizationMethod(normalization),
            condition_a=condition_a,
            condition_b=condition_b,
            selection_policy=BiologicalResultSelectionPolicy(
                max_adjusted_p_value=max_adjusted_p_value,
                min_absolute_log2_fold_change=min_absolute_log2_fold_change,
                heatmap_max_entity_count=heatmap_max_entities,
                heatmap_min_observed_fraction=heatmap_min_observed_fraction,
            ),
            volcano_policy=_build_volcano_review_policy(
                adjusted_p_value_threshold=max_adjusted_p_value,
                absolute_log2_fold_change_threshold=min_absolute_log2_fold_change,
                top_label_count=volcano_top_label_count,
            ),
            output_dir=output_dir,
        )
    )
    report = result.report
    manifest = result.export_manifest
    if manifest is None:
        raise click.ClickException("workflow export manifest was not produced")

    _emit_json(
        {
            "design_rows": result.design_row_count,
            "report": report.to_dict(),
            "export_manifest": manifest.to_dict(),
            "outputs": result.outputs,
        },
        out_path=out_path,
    )


@cli.command("peptide-matrix")
@click.argument(
    "input_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--input-kind",
    type=_peptide_matrix_builder_input_kind_choice(),
    default="feature",
    show_default=True,
)
@click.option(
    "--grouping-mode",
    type=_peptide_matrix_grouping_choice(),
    default=PeptideMatrixGroupingMode.MODIFIED_PEPTIDE.value,
    show_default=True,
)
@click.option(
    "--separate-charge-states/--merge-charge-states",
    default=False,
    show_default=True,
)
@click.option(
    "--aggregation",
    type=_quant_rollup_choice(),
    default=QuantRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=3, show_default=True)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--precursor-id-column", default="precursor_id", show_default=True)
@click.option("--run-column", default="run_id", show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option(
    "--modified-peptide-column",
    default="modified_peptide",
    show_default=True,
)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--mz-column", default="mz", show_default=True)
@click.option(
    "--retention-time-column", default="retention_time_seconds", show_default=True
)
@click.option("--missing-reason-column", default="missing_reason", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option(
    "--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--matrix-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--missingness-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--missingness-mask-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--aggregation-table-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON peptide-matrix output path.",
)
def peptide_matrix_command(
    input_table: Path,
    input_kind: str,
    grouping_mode: str,
    separate_charge_states: bool,
    aggregation: str,
    top_n: int,
    sample_column: str,
    feature_id_column: str,
    precursor_id_column: str,
    run_column: str,
    spectrum_id_column: str,
    peptide_column: str,
    modified_peptide_column: str,
    intensity_column: str,
    protein_refs_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    mz_column: str | None,
    retention_time_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    missingness_tsv_out: Path | None,
    missingness_mask_tsv_out: Path | None,
    aggregation_table_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Build one peptide-by-sample intensity matrix from feature, precursor, or PSM evidence."""
    try:
        grouping = PeptideMatrixGroupingMode(grouping_mode)
        rollup_method = QuantRollupMethod(aggregation)
        if input_kind == "feature":
            feature_mapping = Ms1FeatureColumnMapping(
                sample_id=sample_column,
                feature_id=feature_id_column,
                peptide=peptide_column,
                intensity=intensity_column,
                protein_refs=protein_refs_column,
                charge=charge_column,
                mz=mz_column,
                retention_time_seconds=retention_time_column,
                missing_reason=missing_reason_column,
                protein_separator=protein_separator,
            )
            parse_report = parse_ms1_feature_table(input_table, mapping=feature_mapping)
            report = build_peptide_intensity_matrix_from_features(
                parse_report.accepted_records,
                grouping_mode=grouping,
                separate_charge_states=separate_charge_states,
                aggregation_method=rollup_method,
                top_n=top_n,
            )
            payload = {
                "input_kind": input_kind,
                "accepted_source_records": len(parse_report.accepted_records),
                "rejected_source_records": len(parse_report.rejected_rows),
                "report": report.to_dict(),
            }
        elif input_kind == "precursor":
            precursor_mapping = PrecursorIntensityColumnMapping(
                peptide=peptide_column,
                modified_peptide=modified_peptide_column,
                intensity=intensity_column,
                sample_id=sample_column,
                run_id=run_column,
                protein_refs=protein_refs_column,
                precursor_id=precursor_id_column,
                charge=charge_column,
                missing_reason=missing_reason_column,
                protein_separator=protein_separator,
            )
            precursor_parse_report = parse_precursor_intensity_table(
                input_table,
                mapping=precursor_mapping,
            )
            report = build_peptide_intensity_matrix_from_precursors(
                precursor_parse_report.accepted_records,
                grouping_mode=grouping,
                separate_charge_states=separate_charge_states,
                aggregation_method=rollup_method,
                top_n=top_n,
            )
            payload = {
                "input_kind": input_kind,
                "accepted_source_records": len(
                    precursor_parse_report.accepted_records
                ),
                "rejected_source_records": len(precursor_parse_report.rejected_rows),
                "report": report.to_dict(),
            }
        else:
            psm_mapping = _build_psm_mapping(
                run_id_column=run_column,
                spectrum_id_column=spectrum_id_column,
                peptide_column=peptide_column,
                modified_peptide_column=modified_peptide_column,
                charge_column=charge_column,
                score_column=score_column,
                q_value_column=q_value_column,
                protein_refs_column=protein_refs_column,
                decoy_label_column=decoy_label_column,
                contaminant_label_column=contaminant_label_column,
                protein_separator=protein_separator,
                intensity_column=intensity_column,
            )
            psm_parse_report = parse_psm_tsv(input_table, mapping=psm_mapping)
            report = build_peptide_intensity_matrix_from_psms(
                psm_parse_report.accepted_records,
                grouping_mode=grouping,
                separate_charge_states=separate_charge_states,
                aggregation_method=rollup_method,
                top_n=top_n,
            )
            payload = {
                "input_kind": input_kind,
                "accepted_source_records": len(psm_parse_report.accepted_records),
                "rejected_source_records": len(psm_parse_report.rejected_rows),
                "report": report.to_dict(),
            }
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_peptide_intensity_matrix_summary_tsv(report),
        )
    if matrix_tsv_out is not None:
        _write_text_output(matrix_tsv_out, render_peptide_intensity_matrix_tsv(report))
    if missingness_tsv_out is not None:
        _write_text_output(
            missingness_tsv_out,
            render_peptide_intensity_missingness_tsv(report),
        )
    if missingness_mask_tsv_out is not None:
        _write_text_output(
            missingness_mask_tsv_out,
            render_peptide_intensity_missingness_mask_tsv(report),
        )
    if aggregation_table_tsv_out is not None:
        _write_text_output(
            aggregation_table_tsv_out,
            render_peptide_intensity_aggregation_tsv(report),
        )
    payload["outputs"] = {
        "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
        "matrix_tsv": None if matrix_tsv_out is None else str(matrix_tsv_out),
        "missingness_tsv": (
            None if missingness_tsv_out is None else str(missingness_tsv_out)
        ),
        "missingness_mask_tsv": (
            None
            if missingness_mask_tsv_out is None
            else str(missingness_mask_tsv_out)
        ),
        "aggregation_table_tsv": (
            None
            if aggregation_table_tsv_out is None
            else str(aggregation_table_tsv_out)
        ),
    }
    _emit_json(payload, out_path=out_path)


@cli.command("protein-matrix")
@click.argument(
    "input_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--input-kind",
    type=_peptide_matrix_input_kind_choice(),
    default="feature",
    show_default=True,
)
@click.option(
    "--grouping-mode",
    type=_peptide_matrix_grouping_choice(),
    default=PeptideMatrixGroupingMode.MODIFIED_PEPTIDE.value,
    show_default=True,
)
@click.option(
    "--target-kind",
    type=_protein_matrix_target_choice(),
    default=ProteinMatrixTargetKind.PROTEIN.value,
    show_default=True,
)
@click.option(
    "--separate-charge-states/--merge-charge-states",
    default=False,
    show_default=True,
)
@click.option(
    "--aggregation",
    type=_quant_rollup_choice(),
    default=QuantRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=3, show_default=True)
@click.option(
    "--unique-peptide-only/--include-shared-peptides",
    default=False,
    show_default=True,
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--run-column", default="run_id", show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option(
    "--modified-peptide-column",
    default="modified_peptide",
    show_default=True,
)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--mz-column", default="mz", show_default=True)
@click.option(
    "--retention-time-column", default="retention_time_seconds", show_default=True
)
@click.option("--missing-reason-column", default="missing_reason", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option(
    "--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--matrix-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--missingness-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--contributions-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON protein-matrix output path.",
)
def protein_matrix_command(
    input_table: Path,
    input_kind: str,
    grouping_mode: str,
    target_kind: str,
    separate_charge_states: bool,
    aggregation: str,
    top_n: int,
    unique_peptide_only: bool,
    sample_column: str,
    feature_id_column: str,
    run_column: str,
    spectrum_id_column: str,
    peptide_column: str,
    modified_peptide_column: str,
    intensity_column: str,
    protein_refs_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    mz_column: str | None,
    retention_time_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    missingness_tsv_out: Path | None,
    contributions_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Build one protein-by-sample intensity matrix from feature or PSM evidence."""
    try:
        grouping = PeptideMatrixGroupingMode(grouping_mode)
        active_target_kind = ProteinMatrixTargetKind(target_kind)
        rollup_method = QuantRollupMethod(aggregation)
        if input_kind == "feature":
            feature_mapping = Ms1FeatureColumnMapping(
                sample_id=sample_column,
                feature_id=feature_id_column,
                peptide=peptide_column,
                intensity=intensity_column,
                protein_refs=protein_refs_column,
                charge=charge_column,
                mz=mz_column,
                retention_time_seconds=retention_time_column,
                missing_reason=missing_reason_column,
                protein_separator=protein_separator,
            )
            parse_report = parse_ms1_feature_table(input_table, mapping=feature_mapping)
            report = build_protein_intensity_matrix_from_features(
                parse_report.accepted_records,
                grouping_mode=grouping,
                separate_charge_states=separate_charge_states,
                target_kind=active_target_kind,
                aggregation_method=rollup_method,
                unique_only=unique_peptide_only,
                top_n=top_n,
            )
            payload = {
                "input_kind": input_kind,
                "accepted_source_records": len(parse_report.accepted_records),
                "rejected_source_records": len(parse_report.rejected_rows),
                "report": report.to_dict(),
            }
        else:
            psm_mapping = _build_psm_mapping(
                run_id_column=run_column,
                spectrum_id_column=spectrum_id_column,
                peptide_column=peptide_column,
                modified_peptide_column=modified_peptide_column,
                charge_column=charge_column,
                score_column=score_column,
                q_value_column=q_value_column,
                protein_refs_column=protein_refs_column,
                decoy_label_column=decoy_label_column,
                contaminant_label_column=contaminant_label_column,
                protein_separator=protein_separator,
                intensity_column=intensity_column,
            )
            psm_parse_report = parse_psm_tsv(input_table, mapping=psm_mapping)
            report = build_protein_intensity_matrix_from_psms(
                psm_parse_report.accepted_records,
                grouping_mode=grouping,
                separate_charge_states=separate_charge_states,
                target_kind=active_target_kind,
                aggregation_method=rollup_method,
                unique_only=unique_peptide_only,
                top_n=top_n,
            )
            payload = {
                "input_kind": input_kind,
                "accepted_source_records": len(psm_parse_report.accepted_records),
                "rejected_source_records": len(psm_parse_report.rejected_rows),
                "report": report.to_dict(),
            }
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_protein_intensity_matrix_summary_tsv(report),
        )
    if matrix_tsv_out is not None:
        _write_text_output(matrix_tsv_out, render_protein_intensity_matrix_tsv(report))
    if missingness_tsv_out is not None:
        _write_text_output(
            missingness_tsv_out,
            render_protein_intensity_missingness_tsv(report),
        )
    if contributions_tsv_out is not None:
        _write_text_output(
            contributions_tsv_out,
            render_protein_peptide_contribution_tsv(report),
        )
    payload["outputs"] = {
        "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
        "matrix_tsv": None if matrix_tsv_out is None else str(matrix_tsv_out),
        "missingness_tsv": (
            None if missingness_tsv_out is None else str(missingness_tsv_out)
        ),
        "contributions_tsv": (
            None if contributions_tsv_out is None else str(contributions_tsv_out)
        ),
    }
    _emit_json(payload, out_path=out_path)


@cli.command("protein-lfq")
@click.argument(
    "input_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--input-kind",
    type=_peptide_matrix_input_kind_choice(),
    default="feature",
    show_default=True,
)
@click.option(
    "--grouping-mode",
    type=_peptide_matrix_grouping_choice(),
    default=PeptideMatrixGroupingMode.MODIFIED_PEPTIDE.value,
    show_default=True,
)
@click.option(
    "--target-kind",
    type=_protein_matrix_target_choice(),
    default=ProteinMatrixTargetKind.PROTEIN.value,
    show_default=True,
)
@click.option(
    "--separate-charge-states/--merge-charge-states",
    default=False,
    show_default=True,
)
@click.option(
    "--aggregation",
    type=_quant_rollup_choice(),
    default=QuantRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=3, show_default=True)
@click.option(
    "--unique-peptide-only/--include-shared-peptides",
    default=False,
    show_default=True,
)
@click.option("--minimum-shared-peptides", type=int, default=1, show_default=True)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--run-column", default="run_id", show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option(
    "--modified-peptide-column",
    default="modified_peptide",
    show_default=True,
)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--mz-column", default="mz", show_default=True)
@click.option(
    "--retention-time-column", default="retention_time_seconds", show_default=True
)
@click.option("--missing-reason-column", default="missing_reason", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option(
    "--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--matrix-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--pairwise-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--missingness-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--disconnected-components-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON protein-lfq output path.",
)
def protein_lfq_command(
    input_table: Path,
    input_kind: str,
    grouping_mode: str,
    target_kind: str,
    separate_charge_states: bool,
    aggregation: str,
    top_n: int,
    unique_peptide_only: bool,
    minimum_shared_peptides: int,
    sample_column: str,
    feature_id_column: str,
    run_column: str,
    spectrum_id_column: str,
    peptide_column: str,
    modified_peptide_column: str,
    intensity_column: str,
    protein_refs_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    mz_column: str | None,
    retention_time_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    pairwise_tsv_out: Path | None,
    missingness_tsv_out: Path | None,
    disconnected_components_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Build one MaxLFQ-like protein abundance matrix from feature or PSM evidence."""
    try:
        grouping = PeptideMatrixGroupingMode(grouping_mode)
        active_target_kind = ProteinMatrixTargetKind(target_kind)
        rollup_method = QuantRollupMethod(aggregation)
        if input_kind == "feature":
            feature_mapping = Ms1FeatureColumnMapping(
                sample_id=sample_column,
                feature_id=feature_id_column,
                peptide=peptide_column,
                intensity=intensity_column,
                protein_refs=protein_refs_column,
                charge=charge_column,
                mz=mz_column,
                retention_time_seconds=retention_time_column,
                missing_reason=missing_reason_column,
                protein_separator=protein_separator,
            )
            parse_report = parse_ms1_feature_table(input_table, mapping=feature_mapping)
            report = build_protein_lfq_report_from_features(
                parse_report.accepted_records,
                grouping_mode=grouping,
                target_kind=active_target_kind,
                separate_charge_states=separate_charge_states,
                aggregation_method=rollup_method,
                unique_only=unique_peptide_only,
                minimum_shared_peptides=minimum_shared_peptides,
                top_n=top_n,
            )
            payload = {
                "input_kind": input_kind,
                "accepted_source_records": len(parse_report.accepted_records),
                "rejected_source_records": len(parse_report.rejected_rows),
                "report": report.to_dict(),
            }
        else:
            psm_mapping = _build_psm_mapping(
                run_id_column=run_column,
                spectrum_id_column=spectrum_id_column,
                peptide_column=peptide_column,
                modified_peptide_column=modified_peptide_column,
                charge_column=charge_column,
                score_column=score_column,
                q_value_column=q_value_column,
                protein_refs_column=protein_refs_column,
                decoy_label_column=decoy_label_column,
                contaminant_label_column=contaminant_label_column,
                protein_separator=protein_separator,
                intensity_column=intensity_column,
            )
            psm_parse_report = parse_psm_tsv(input_table, mapping=psm_mapping)
            report = build_protein_lfq_report_from_psms(
                psm_parse_report.accepted_records,
                grouping_mode=grouping,
                target_kind=active_target_kind,
                separate_charge_states=separate_charge_states,
                aggregation_method=rollup_method,
                unique_only=unique_peptide_only,
                minimum_shared_peptides=minimum_shared_peptides,
                top_n=top_n,
            )
            payload = {
                "input_kind": input_kind,
                "accepted_source_records": len(psm_parse_report.accepted_records),
                "rejected_source_records": len(psm_parse_report.rejected_rows),
                "report": report.to_dict(),
            }
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_protein_lfq_summary_tsv(report))
    if matrix_tsv_out is not None:
        _write_text_output(matrix_tsv_out, render_protein_lfq_matrix_tsv(report))
    if pairwise_tsv_out is not None:
        _write_text_output(
            pairwise_tsv_out,
            render_protein_lfq_pairwise_ratios_tsv(report),
        )
    if missingness_tsv_out is not None:
        _write_text_output(
            missingness_tsv_out,
            render_protein_lfq_missingness_tsv(report),
        )
    if disconnected_components_tsv_out is not None:
        _write_text_output(
            disconnected_components_tsv_out,
            render_protein_lfq_disconnected_components_tsv(report),
        )
    payload["outputs"] = {
        "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
        "matrix_tsv": None if matrix_tsv_out is None else str(matrix_tsv_out),
        "pairwise_tsv": None if pairwise_tsv_out is None else str(pairwise_tsv_out),
        "missingness_tsv": (
            None if missingness_tsv_out is None else str(missingness_tsv_out)
        ),
        "disconnected_components_tsv": (
            None
            if disconnected_components_tsv_out is None
            else str(disconnected_components_tsv_out)
        ),
    }
    _emit_json(payload, out_path=out_path)


@cli.command("spectrum-parse")
@click.argument(
    "input_mgf", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--chunk-size", type=int, default=500, show_default=True)
@click.option(
    "--accepted-jsonl-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-json-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def spectrum_parse_command(
    input_mgf: Path,
    chunk_size: int,
    accepted_jsonl_out: Path | None,
    rejected_json_out: Path | None,
    out_path: Path | None,
) -> None:
    """Parse one MGF file and report accepted spectra, rejections, and streaming facts."""
    report = parse_mgf(input_mgf)
    streaming_profile = build_streaming_parse_profile(
        input_mgf,
        format_name="mgf",
        chunk_size=chunk_size,
    )

    if accepted_jsonl_out is not None:
        accepted_jsonl_out.write_text(
            "".join(
                json.dumps(
                    spectrum.to_dict(),
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
                for spectrum in report.accepted_spectra
            ),
            encoding="utf-8",
        )
    if rejected_json_out is not None:
        rejected_json_out.write_text(
            json.dumps(
                [block.to_dict() for block in report.rejected_blocks],
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    payload = {
        "parse_report": report.to_dict(),
        "summary": build_spectrum_collection_summary(report).to_dict(),
        "streaming_profile": streaming_profile.to_dict(),
        "accepted_jsonl_out": str(accepted_jsonl_out) if accepted_jsonl_out else None,
        "rejected_json_out": str(rejected_json_out) if rejected_json_out else None,
    }
    _emit_json(payload, out_path=out_path)


@cli.command("spectrum-stats")
@click.argument(
    "input_mgf", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--provenance-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def spectrum_stats_command(
    input_mgf: Path,
    provenance_out: Path | None,
    out_path: Path | None,
) -> None:
    """Summarize one MGF collection."""
    report = parse_mgf(input_mgf)
    summary = build_spectrum_collection_summary(report)
    provenance = build_spectrum_provenance_manifest(
        source_path=input_mgf, parse_report=report
    )
    if provenance_out is not None:
        provenance_out.write_text(provenance.to_stable_json() + "\n")
    payload = {
        "summary": summary.to_dict(),
        "provenance": provenance.to_dict(),
        "metrics": [
            build_spectrum_metrics(spectrum).to_dict()
            for spectrum in report.accepted_spectra
        ],
    }
    _emit_json(payload, out_path=out_path)


@cli.command("spectrum-summary")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--kind",
    type=click.Choice(["auto", "mgf", "mzml"]),
    default="auto",
    show_default=True,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--charge-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--precursor-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--peak-count-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def spectrum_summary_command(
    input_path: Path,
    kind: str,
    summary_tsv_out: Path | None,
    charge_tsv_out: Path | None,
    precursor_tsv_out: Path | None,
    peak_count_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Build reviewable summary tables over one MGF or mzML spectra file."""
    resolved_kind = kind
    if resolved_kind == "auto":
        suffix = input_path.suffix.lower()
        if suffix == ".mgf":
            resolved_kind = "mgf"
        elif suffix == ".mzml":
            resolved_kind = "mzml"
        else:
            raise click.ClickException(
                "cannot infer spectrum summary kind; use --kind mgf or --kind mzml"
            )

    if resolved_kind == "mgf":
        mgf_parse_report = parse_mgf(input_path)
        report = build_spectrum_summary_table_report(
            mgf_parse_report.accepted_spectra,
            source_kind="mgf",
            rejected_count=len(mgf_parse_report.rejected_blocks),
        )
    elif resolved_kind == "mzml":
        mzml_parse_report = parse_mzml(input_path)
        report = build_spectrum_summary_table_report(
            mzml_parse_report.accepted_spectra,
            source_kind="mzml",
            rejected_count=len(mzml_parse_report.rejected_spectra),
        )
    else:
        raise click.ClickException("spectrum-summary supports only mgf and mzml")

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_spectrum_summary_tsv(report),
            encoding="utf-8",
        )
    if charge_tsv_out is not None:
        charge_tsv_out.write_text(
            render_spectrum_distribution_tsv(
                report.charge_distribution,
                distribution_name="charge",
            ),
            encoding="utf-8",
        )
    if precursor_tsv_out is not None:
        precursor_tsv_out.write_text(
            render_spectrum_distribution_tsv(
                report.precursor_mz_distribution,
                distribution_name="precursor_mz",
            ),
            encoding="utf-8",
        )
    if peak_count_tsv_out is not None:
        peak_count_tsv_out.write_text(
            render_spectrum_distribution_tsv(
                report.peak_count_distribution,
                distribution_name="peak_count",
            ),
            encoding="utf-8",
        )

    payload = report.to_dict()
    payload["summary_tsv_out"] = str(summary_tsv_out) if summary_tsv_out else None
    payload["charge_tsv_out"] = str(charge_tsv_out) if charge_tsv_out else None
    payload["precursor_tsv_out"] = str(precursor_tsv_out) if precursor_tsv_out else None
    payload["peak_count_tsv_out"] = (
        str(peak_count_tsv_out) if peak_count_tsv_out else None
    )
    _emit_json(payload, out_path=out_path)


@cli.command("spectrum-qc")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--kind",
    type=click.Choice(["auto", "mgf", "mzml"]),
    default="auto",
    show_default=True,
)
@click.option(
    "--time-bin-seconds",
    type=float,
    default=60.0,
    show_default=True,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--msms-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--tic-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--bpc-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--charge-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--precursor-intensity-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--flagged-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--spectrum-qc-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--plot-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON run-QC output path.",
)
def spectrum_qc_command(
    input_path: Path,
    kind: str,
    time_bin_seconds: float,
    summary_tsv_out: Path | None,
    msms_tsv_out: Path | None,
    tic_tsv_out: Path | None,
    bpc_tsv_out: Path | None,
    charge_tsv_out: Path | None,
    precursor_intensity_tsv_out: Path | None,
    flagged_tsv_out: Path | None,
    spectrum_qc_tsv_out: Path | None,
    plot_out: Path | None,
    out_path: Path | None,
) -> None:
    """Build run-level QC directly from one MGF or mzML spectra file."""
    resolved_kind = kind
    if resolved_kind == "auto":
        suffix = input_path.suffix.lower()
        if suffix == ".mgf":
            resolved_kind = "mgf"
        elif suffix == ".mzml":
            resolved_kind = "mzml"
        else:
            raise click.ClickException(
                "cannot infer spectrum QC kind; use --kind mgf or --kind mzml"
            )

    if resolved_kind == "mgf":
        mgf_parse_report = parse_mgf(input_path)
        report = build_spectrum_run_qc_report(
            mgf_parse_report.accepted_spectra,
            source_kind="mgf",
            rejected_count=len(mgf_parse_report.rejected_blocks),
            time_bin_seconds=time_bin_seconds,
        )
    elif resolved_kind == "mzml":
        mzml_parse_report = parse_mzml(input_path)
        report = build_spectrum_run_qc_report(
            mzml_parse_report.accepted_spectra,
            source_kind="mzml",
            rejected_count=len(mzml_parse_report.rejected_spectra),
            chromatograms=extract_mzml_chromatograms(input_path),
            time_bin_seconds=time_bin_seconds,
        )
    else:
        raise click.ClickException("spectrum-qc supports only mgf and mzml")

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_spectrum_run_qc_summary_tsv(report))
    if msms_tsv_out is not None:
        _write_text_output(msms_tsv_out, render_spectrum_run_qc_time_bins_tsv(report))
    if tic_tsv_out is not None:
        _write_text_output(
            tic_tsv_out,
            render_spectrum_run_qc_trace_tsv(report.tic_trace, trace_name="tic"),
        )
    if bpc_tsv_out is not None:
        _write_text_output(
            bpc_tsv_out,
            render_spectrum_run_qc_trace_tsv(report.bpc_trace, trace_name="bpc"),
        )
    if charge_tsv_out is not None:
        _write_text_output(
            charge_tsv_out,
            render_spectrum_run_qc_distribution_tsv(
                report.charge_distribution,
                distribution_name="charge",
            ),
        )
    if precursor_intensity_tsv_out is not None:
        _write_text_output(
            precursor_intensity_tsv_out,
            render_spectrum_run_qc_distribution_tsv(
                report.precursor_intensity_distribution,
                distribution_name="precursor_intensity",
            ),
        )
    if flagged_tsv_out is not None:
        _write_text_output(
            flagged_tsv_out,
            render_spectrum_run_qc_flagged_spectra_tsv(report),
        )
    if spectrum_qc_tsv_out is not None:
        _write_text_output(
            spectrum_qc_tsv_out,
            render_spectrum_run_qc_spectra_tsv(report),
        )
    plot_payload = build_spectrum_run_qc_plot_payload(report)
    if plot_out is not None:
        plot_out.write_text(plot_payload.to_stable_json() + "\n", encoding="utf-8")

    payload = report.to_dict()
    payload["summary_tsv_out"] = str(summary_tsv_out) if summary_tsv_out else None
    payload["msms_tsv_out"] = str(msms_tsv_out) if msms_tsv_out else None
    payload["tic_tsv_out"] = str(tic_tsv_out) if tic_tsv_out else None
    payload["bpc_tsv_out"] = str(bpc_tsv_out) if bpc_tsv_out else None
    payload["charge_tsv_out"] = str(charge_tsv_out) if charge_tsv_out else None
    payload["precursor_intensity_tsv_out"] = (
        str(precursor_intensity_tsv_out) if precursor_intensity_tsv_out else None
    )
    payload["flagged_tsv_out"] = str(flagged_tsv_out) if flagged_tsv_out else None
    payload["spectrum_qc_tsv_out"] = (
        str(spectrum_qc_tsv_out) if spectrum_qc_tsv_out else None
    )
    payload["plot_out"] = str(plot_out) if plot_out else None
    _emit_json(payload, out_path=out_path)


@cli.command("mzml-inspect")
@click.argument(
    "input_mzml", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--spectra-jsonl-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--chromatograms-json-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def mzml_inspect_command(
    input_mzml: Path,
    spectra_jsonl_out: Path | None,
    chromatograms_json_out: Path | None,
    out_path: Path | None,
) -> None:
    """Inspect one mzML run with practical spectra, decoding, and chromatogram review."""
    review = build_mzml_practical_review_report(input_mzml)
    parse_report = parse_mzml(input_mzml)

    if spectra_jsonl_out is not None:
        export_spectra_jsonl(parse_report.accepted_spectra, spectra_jsonl_out)
    if chromatograms_json_out is not None:
        chromatograms_json_out.write_text(
            review.chromatograms.to_stable_json() + "\n",
            encoding="utf-8",
        )

    payload = review.to_dict()
    payload["spectra_jsonl_out"] = (
        str(spectra_jsonl_out) if spectra_jsonl_out is not None else None
    )
    payload["chromatograms_json_out"] = (
        str(chromatograms_json_out) if chromatograms_json_out is not None else None
    )
    _emit_json(payload, out_path=out_path)


@cli.command("spectrum-annotate")
@click.argument(
    "input_mgf", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--peptide", required=True)
@click.option(
    "--spectrum-id",
    default=None,
    help="Optional target spectrum id; defaults to the first accepted spectrum.",
)
@click.option("--tolerance-da", type=float, default=None)
@click.option("--tolerance-ppm", type=float, default=None)
@click.option(
    "--tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--plot-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--unmatched-peak-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON annotation output path.",
)
def spectrum_annotate_command(
    input_mgf: Path,
    peptide: str,
    spectrum_id: str | None,
    tolerance_da: float | None,
    tolerance_ppm: float | None,
    tsv_out: Path | None,
    plot_out: Path | None,
    unmatched_peak_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Annotate one spectrum against a peptide sequence."""
    effective_tolerance_da = (
        0.02 if tolerance_da is None and tolerance_ppm is None else tolerance_da
    )
    report = parse_mgf(input_mgf)
    if not report.accepted_spectra:
        raise click.ClickException(
            "MGF input does not contain an accepted spectrum to annotate"
        )
    if spectrum_id is None:
        spectrum = report.accepted_spectra[0]
    else:
        try:
            spectrum = next(
                item
                for item in report.accepted_spectra
                if item.spectrum_id == spectrum_id
            )
        except StopIteration as exc:
            raise click.ClickException(f"unknown spectrum id {spectrum_id!r}") from exc
    try:
        peak_matching_report = build_spectrum_peak_match_report(
            spectrum,
            peptide=peptide,
            tolerance_da=effective_tolerance_da,
            tolerance_ppm=tolerance_ppm,
        )
        annotation = annotate_spectrum_fragments(
            spectrum,
            peptide=peptide,
            tolerance_da=effective_tolerance_da,
            tolerance_ppm=tolerance_ppm,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    plot_payload = build_spectrum_plot_payload(spectrum, annotation=annotation)
    if tsv_out is not None:
        export_spectrum_peak_match_tsv(peak_matching_report, tsv_out)
    if plot_out is not None:
        plot_out.write_text(plot_payload.to_stable_json() + "\n")
    if unmatched_peak_tsv_out is not None:
        export_spectrum_unmatched_peak_tsv(
            peak_matching_report,
            unmatched_peak_tsv_out,
        )
    payload = {
        "annotation": annotation.to_dict(),
        "peak_matching_report": peak_matching_report.to_dict(),
        "plot_payload": plot_payload.to_dict(),
    }
    _emit_json(payload, out_path=out_path)


@cli.command("spectrum-similarity")
@click.argument(
    "query_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "reference_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--query-kind",
    type=click.Choice(["auto", "mgf", "mzml"]),
    default="auto",
    show_default=True,
)
@click.option(
    "--reference-kind",
    type=click.Choice(["auto", "mgf", "mzml"]),
    default="auto",
    show_default=True,
)
@click.option("--query-spectrum-id", default=None)
@click.option("--reference-spectrum-id", default=None)
@click.option(
    "--method",
    type=click.Choice([item.value for item in SpectralSimilarityMethod]),
    default=SpectralSimilarityMethod.COSINE.value,
    show_default=True,
)
@click.option(
    "--mode",
    type=click.Choice([item.value for item in SpectrumSimilarityMode]),
    default=SpectrumSimilarityMode.NORMALIZED.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=None)
@click.option("--tolerance-da", type=float, default=None)
@click.option("--bin-width-da", type=float, default=None)
@click.option("--max-matches", type=int, default=None)
@click.option(
    "--tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON similarity output path.",
)
def spectrum_similarity_command(
    query_path: Path,
    reference_path: Path,
    query_kind: str,
    reference_kind: str,
    query_spectrum_id: str | None,
    reference_spectrum_id: str | None,
    method: str,
    mode: str,
    top_n: int | None,
    tolerance_da: float | None,
    bin_width_da: float | None,
    max_matches: int | None,
    tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Compare one query spectrum against one spectrum or a reference library."""
    try:
        query_spectra = _load_similarity_spectra(query_path, kind=query_kind)
        reference_spectra = _load_similarity_spectra(
            reference_path,
            kind=reference_kind,
        )
        query_spectrum = _select_similarity_spectrum(
            query_spectra,
            input_path=query_path,
            spectrum_id=query_spectrum_id,
        )
        active_method = SpectralSimilarityMethod(method)
        active_mode = SpectrumSimilarityMode(mode)
        if top_n is not None and top_n <= 0:
            raise ValueError("top_n must be greater than zero when provided")
        if max_matches is not None and max_matches <= 0:
            raise ValueError("max_matches must be greater than zero when provided")

        payload: dict[str, Any]
        if reference_spectrum_id is not None:
            reference_spectrum = _select_similarity_spectrum(
                reference_spectra,
                input_path=reference_path,
                spectrum_id=reference_spectrum_id,
            )
            comparison = build_spectrum_similarity_comparison_report(
                reference_spectrum,
                query_spectrum,
                tolerance_da=tolerance_da,
                bin_width_da=bin_width_da,
                method=active_method,
                mode=active_mode,
                top_n=top_n,
            )
            library_report = build_spectrum_library_similarity_report(
                query_spectrum,
                (reference_spectrum,),
                tolerance_da=tolerance_da,
                bin_width_da=bin_width_da,
                method=active_method,
                mode=active_mode,
                top_n=top_n,
                max_matches=1,
            )
            payload = {
                "comparison": comparison.to_dict(),
                "library_report": library_report.to_dict(),
            }
        else:
            library_report = build_spectrum_library_similarity_report(
                query_spectrum,
                reference_spectra,
                tolerance_da=tolerance_da,
                bin_width_da=bin_width_da,
                method=active_method,
                mode=active_mode,
                top_n=top_n,
                max_matches=max_matches,
            )
            payload = {
                "comparison": None,
                "library_report": library_report.to_dict(),
            }
        if tsv_out is not None:
            _write_text_output(tsv_out, render_spectrum_similarity_tsv(library_report))
        payload["tsv_out"] = str(tsv_out) if tsv_out is not None else None
        _emit_json(payload, out_path=out_path)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@cli.command("spectral-library-import")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--kind",
    type=click.Choice(["auto", "msp", "mgf"]),
    default="auto",
    show_default=True,
)
@click.option("--precursor-mz", type=float, default=None)
@click.option("--tolerance-da", type=float, default=0.5, show_default=True)
@click.option("--peptide", default=None)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--candidates-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON library import output path.",
)
def spectral_library_import_command(
    input_path: Path,
    kind: str,
    precursor_mz: float | None,
    tolerance_da: float,
    peptide: str | None,
    summary_tsv_out: Path | None,
    candidates_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Import one practical spectral library and optionally retrieve candidates."""
    try:
        active_kind = None if kind == "auto" else kind
        report = import_spectral_library(input_path, library_format=active_kind)
        summary = build_spectral_library_summary(report)
        index = build_spectral_library_index(report.entries)
        candidates = (
            find_spectral_library_candidates(
                index,
                precursor_mz=precursor_mz,
                tolerance_da=tolerance_da,
                peptide_query=peptide,
            )
            if precursor_mz is not None
            else None
        )
        if summary_tsv_out is not None:
            _write_text_output(
                summary_tsv_out,
                render_spectral_library_summary_tsv(summary),
            )
        if candidates_tsv_out is not None:
            if candidates is None:
                raise ValueError(
                    "candidates-tsv-out requires --precursor-mz candidate lookup input"
                )
            _write_text_output(
                candidates_tsv_out,
                render_spectral_library_candidates_tsv(candidates),
            )
        payload = {
            "import_report": report.to_dict(),
            "summary": summary.to_dict(),
            "index": {
                "entry_count": len(index.entries),
                "peptide_index": index.peptide_index,
                "precursor_centimass_index_size": len(index.precursor_centimass_index),
            },
            "candidates": candidates.to_dict() if candidates is not None else None,
            "summary_tsv_out": str(summary_tsv_out) if summary_tsv_out else None,
            "candidates_tsv_out": (
                str(candidates_tsv_out) if candidates_tsv_out else None
            ),
        }
        _emit_json(payload, out_path=out_path)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@cli.command("spectral-library-search")
@click.argument(
    "query_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "library_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--query-kind",
    type=click.Choice(["auto", "mgf", "mzml"]),
    default="auto",
    show_default=True,
)
@click.option(
    "--library-kind",
    type=click.Choice(["auto", "msp", "mgf"]),
    default="auto",
    show_default=True,
)
@click.option("--query-spectrum-id", default=None)
@click.option(
    "--precursor-tolerance-da",
    type=float,
    default=0.5,
    show_default=True,
)
@click.option(
    "--tolerance-da",
    type=float,
    default=0.02,
    show_default=True,
    help="Fragment matching tolerance in Daltons for spectrum similarity.",
)
@click.option("--bin-width-da", type=float, default=None)
@click.option(
    "--method",
    type=click.Choice([item.value for item in SpectralSimilarityMethod]),
    default=SpectralSimilarityMethod.COSINE.value,
    show_default=True,
)
@click.option(
    "--mode",
    type=click.Choice([item.value for item in SpectrumSimilarityMode]),
    default=SpectrumSimilarityMode.NORMALIZED.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=None)
@click.option("--max-matches", type=int, default=10, show_default=True)
@click.option(
    "--tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON spectral-library search output path.",
)
def spectral_library_search_command(
    query_path: Path,
    library_path: Path,
    query_kind: str,
    library_kind: str,
    query_spectrum_id: str | None,
    precursor_tolerance_da: float,
    tolerance_da: float,
    bin_width_da: float | None,
    method: str,
    mode: str,
    top_n: int | None,
    max_matches: int,
    tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Search one query spectrum against a practical MSP or MGF library."""
    try:
        query_spectra = _load_similarity_spectra(query_path, kind=query_kind)
        query_spectrum = _select_similarity_spectrum(
            query_spectra,
            input_path=query_path,
            spectrum_id=query_spectrum_id,
        )
        active_library_kind = None if library_kind == "auto" else library_kind
        import_report = import_spectral_library(
            library_path,
            library_format=active_library_kind,
        )
        summary = build_spectral_library_summary(import_report)
        index = build_spectral_library_index(import_report.entries)
        search_report = search_spectral_library(
            query_spectrum,
            index,
            precursor_tolerance_da=precursor_tolerance_da,
            similarity_tolerance_da=tolerance_da,
            similarity_bin_width_da=bin_width_da,
            method=SpectralSimilarityMethod(method),
            mode=SpectrumSimilarityMode(mode),
            top_n=top_n,
            max_matches=max_matches,
        )
        if tsv_out is not None:
            _write_text_output(
                tsv_out, render_spectral_library_search_tsv(search_report)
            )
        payload = {
            "import_report": import_report.to_dict(),
            "library_summary": summary.to_dict(),
            "search_report": search_report.to_dict(),
            "warnings": (
                []
                if search_report.advisory_warning is None
                else [search_report.advisory_warning]
            ),
            "tsv_out": str(tsv_out) if tsv_out else None,
        }
        _emit_json(payload, out_path=out_path)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@cli.command("validate")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--kind",
    "input_kind",
    type=_validate_kind_choice(),
    default="auto",
    show_default=True,
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON validation output path.",
)
def validate_command(
    input_path: Path,
    input_kind: str,
    mode: str,
    out_path: Path | None,
) -> None:
    """Validate one FASTA, PSM TSV, MGF, mzML, design table, or modification registry input."""
    resolved_kind = _infer_input_kind(input_path, input_kind)
    try:
        report = validate_proteomics_input(
            input_path,
            input_kind=ProteomicsFormatKind(resolved_kind),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(report, out_path=out_path)


@cli.command("summarize")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--kind",
    "input_kind",
    type=_validate_kind_choice(),
    default="auto",
    show_default=True,
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON summary output path.",
)
def summarize_command(
    input_path: Path,
    input_kind: str,
    mode: str,
    out_path: Path | None,
) -> None:
    """Summarize one FASTA, PSM TSV, MGF, mzML, or design-table input."""
    resolved_kind = _infer_input_kind(input_path, input_kind)
    if resolved_kind == "fasta":
        fasta_report = parse_fasta_document(
            input_path.read_text(), mode=FastaParseMode(mode)
        )
        payload = {
            "input_kind": resolved_kind,
            "summary": build_fasta_stats(
                fasta_report.accepted_records,
                rejected_records=fasta_report.rejected_records,
            ).to_dict(),
            "profile": build_fasta_database_profile(
                fasta_report.accepted_records,
                rejected_records=fasta_report.rejected_records,
            ).to_dict(),
            "database_composition": fasta_report.database_composition.to_dict(),
            "rejected_records": len(fasta_report.rejected_records),
            "duplicate_accessions": list(fasta_report.duplicate_accessions),
        }
    elif resolved_kind == "psm":
        psm_report = parse_psm_tsv(input_path, mapping=_default_psm_mapping())
        normalized = apply_q_values(psm_report.accepted_records)
        payload = {
            "input_kind": resolved_kind,
            "inspection": build_psm_evidence_inspection_report(psm_report).to_dict(),
            "psm_summary": build_psm_summary_report(normalized).to_dict(),
            "peptide_summary": build_peptide_summary_report(normalized).to_dict(),
            "protein_summary": build_protein_summary_report(normalized).to_dict(),
            "contaminant_report": build_contaminant_peptide_match_report(
                normalized
            ).to_dict(),
            "rejected_rows": len(psm_report.rejected_rows),
        }
    elif resolved_kind == "mgf":
        mgf_report = parse_mgf(input_path)
        payload = {
            "input_kind": resolved_kind,
            "summary": build_spectrum_collection_summary(mgf_report).to_dict(),
            "metrics": [
                build_spectrum_metrics(spectrum).to_dict()
                for spectrum in mgf_report.accepted_spectra
            ],
        }
    elif resolved_kind == "mzml":
        mzml_report = parse_mzml(input_path)
        payload = {
            "input_kind": resolved_kind,
            "metadata": mzml_report.metadata.to_dict(),
            "summary": build_mzml_collection_summary(mzml_report).to_dict(),
            "metrics": [
                build_spectrum_metrics(spectrum).to_dict()
                for spectrum in mzml_report.accepted_spectra
            ],
        }
    elif resolved_kind == "design-table":
        design_report = parse_experimental_design_table(input_path)
        payload = {
            "input_kind": resolved_kind,
            "accepted_entries": len(design_report.accepted_entries),
            "rejected_rows": len(design_report.rejected_rows),
            "instruments": sorted(
                {
                    entry.instrument
                    for entry in design_report.accepted_entries
                    if entry.instrument is not None
                }
            ),
            "search_engines": sorted(
                {
                    entry.search_engine
                    for entry in design_report.accepted_entries
                    if entry.search_engine is not None
                }
            ),
        }
    else:
        raise click.ClickException(
            "summarize currently supports fasta, psm, mgf, mzml, and design-table inputs"
        )
    _emit_json(payload, out_path=out_path)


@cli.command("format-convert")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--kind",
    "input_kind",
    type=_validate_kind_choice(),
    default="auto",
    show_default=True,
)
@click.option("--to", "target_format", type=_conversion_target_choice(), required=True)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Where to write the converted normalized output.",
)
def format_convert_command(
    input_path: Path,
    input_kind: str,
    target_format: str,
    out_path: Path,
) -> None:
    """Convert one supported input into a normalized Bijux output surface."""
    resolved_kind = _infer_input_kind(input_path, input_kind)
    try:
        report = convert_proteomics_format(
            input_path=input_path,
            output_path=out_path,
            input_kind=ProteomicsFormatKind(resolved_kind),
            target_format=FormatConversionTarget(target_format),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(report)


@cli.command("bundle-run")
@click.option(
    "--spectra",
    "spectra_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--identifications",
    "identifications_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--out-dir",
    "out_dir",
    type=click.Path(path_type=Path, file_okay=False),
    required=True,
    help="Directory where the normalized run bundle should be written.",
)
def bundle_run_command(
    spectra_path: Path,
    identifications_path: Path | None,
    design_path: Path | None,
    out_dir: Path,
) -> None:
    """Build one normalized run bundle from spectra, IDs, and optional design metadata."""
    try:
        manifest = build_normalized_run_bundle(
            bundle_dir=out_dir,
            spectra_path=spectra_path,
            identifications_path=identifications_path,
            design_path=design_path,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(manifest)


@cli.command("run")
@click.option(
    "--engine",
    type=click.Choice([engine.value for engine in ProteomicsRunEngine]),
    required=True,
)
@click.option(
    "--report",
    "report_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Primary engine result table: DIA-NN report.tsv, MaxQuant evidence.txt, or FragPipe psm.tsv.",
)
@click.option(
    "--peptides",
    "peptides_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="MaxQuant-only peptides.txt input.",
)
@click.option(
    "--protein-groups",
    "protein_groups_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="MaxQuant-only proteinGroups.txt input.",
)
@click.option(
    "--source-protein-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional FragPipe or DDA source protein table for discrepancy review.",
)
@click.option(
    "--metadata",
    "metadata_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--proteins-fasta",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option("--contrast", required=True)
@click.option(
    "--config-path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--go-annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--pathway-membership-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--complex-membership-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--max-q-value", type=float, default=0.01, show_default=True)
@click.option(
    "--psm-q-value-threshold",
    type=float,
    default=0.01,
    show_default=True,
)
@click.option(
    "--max-adjusted-p-value",
    type=float,
    default=0.1,
    show_default=True,
)
@click.option(
    "--min-absolute-log2-fold-change",
    type=float,
    default=1.0,
    show_default=True,
)
@click.option(
    "--heatmap-max-entities",
    type=int,
    default=50,
    show_default=True,
)
@click.option(
    "--heatmap-min-observed-fraction",
    type=float,
    default=0.5,
    show_default=True,
)
@click.option(
    "--volcano-top-label-count",
    type=int,
    default=10,
    show_default=True,
)
@click.option(
    "--out",
    "output_dir",
    type=click.Path(path_type=Path, file_okay=False),
    required=True,
    help="Directory where the final flagship result package should be written.",
)
@click.option(
    "--json-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON summary output path.",
)
def proteomics_run_command(
    engine: str,
    report_path: Path | None,
    peptides_path: Path | None,
    protein_groups_path: Path | None,
    source_protein_tsv: Path | None,
    metadata_path: Path,
    proteins_fasta: Path,
    contrast: str,
    config_path: Path | None,
    annotation_tsv: Path | None,
    go_annotation_tsv: Path | None,
    pathway_membership_tsv: Path | None,
    complex_membership_tsv: Path | None,
    normalization: str,
    max_q_value: float,
    psm_q_value_threshold: float,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
    heatmap_max_entities: int,
    heatmap_min_observed_fraction: float,
    volcano_top_label_count: int,
    output_dir: Path,
    json_out: Path | None,
) -> None:
    """Run one flagship proteomics workflow from engine output to final biology report."""

    try:
        resolved_engine = ProteomicsRunEngine(engine)
        _validate_proteomics_run_inputs(
            engine=resolved_engine,
            report_path=report_path,
            peptides_path=peptides_path,
            protein_groups_path=protein_groups_path,
            source_protein_tsv=source_protein_tsv,
            config_path=config_path,
        )
        metadata_report = parse_experimental_design_table(metadata_path)
        if metadata_report.rejected_rows:
            raise click.ClickException("metadata table contains rejected rows")
        report = build_proteomics_run_bundle(
            engine=resolved_engine,
            metadata_entries=tuple(metadata_report.accepted_entries),
            proteins_fasta_path=proteins_fasta,
            report_tsv_path=report_path,
            contrast=contrast,
            peptides_tsv_path=peptides_path,
            protein_groups_tsv_path=protein_groups_path,
            source_protein_tsv_path=source_protein_tsv,
            config_path=config_path,
            annotation_tsv_path=annotation_tsv,
            go_annotation_tsv_path=go_annotation_tsv,
            pathway_membership_tsv_path=pathway_membership_tsv,
            complex_membership_tsv_path=complex_membership_tsv,
            normalization_method=NormalizationMethod(normalization),
            max_q_value=max_q_value,
            psm_q_value_threshold=psm_q_value_threshold,
            selection_policy=BiologicalResultSelectionPolicy(
                max_adjusted_p_value=max_adjusted_p_value,
                min_absolute_log2_fold_change=min_absolute_log2_fold_change,
                heatmap_max_entity_count=heatmap_max_entities,
                heatmap_min_observed_fraction=heatmap_min_observed_fraction,
            ),
            volcano_policy=_build_volcano_review_policy(
                adjusted_p_value_threshold=max_adjusted_p_value,
                absolute_log2_fold_change_threshold=min_absolute_log2_fold_change,
                top_label_count=volcano_top_label_count,
            ),
        )
        manifest = export_proteomics_run_bundle(report, output_dir)
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    manifest_path = output_dir / "proteomics_run_manifest.json"
    manifest_path.write_text(manifest.to_stable_json() + "\n", encoding="utf-8")

    _emit_json(
        {
            "metadata_rows": len(metadata_report.accepted_entries),
            "summary_tsv": render_proteomics_run_summary_tsv(report),
            "run": report.to_dict(),
            "export_manifest": manifest.to_dict(),
            "outputs": {
                "output_dir": str(output_dir),
                "manifest_json": str(manifest_path),
            },
        },
        out_path=json_out,
    )


@cli.command("workflow-plan")
@click.option(
    "--proteins",
    "proteins_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--spectra",
    "spectra_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--identifications",
    "identifications_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--features",
    "features_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--sample-id", default=None)
@click.option(
    "--search-adapter",
    type=_search_adapter_choice(),
    default=SearchAdapterKind.GENERIC.value,
    show_default=True,
)
@click.option(
    "--scheduler",
    type=_workflow_scheduler_choice(),
    default=WorkflowSchedulerKind.SLURM.value,
    show_default=True,
)
@click.option(
    "--container-image",
    default="ghcr.io/bijux/proteomics-runtime:stable",
    show_default=True,
)
@click.option(
    "--artifacts-dir", type=click.Path(path_type=Path, file_okay=False), default=None
)
@click.option("--completed-step", "completed_steps", multiple=True)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--dag-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--job-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--checkpoint-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def workflow_plan_command(
    proteins_path: Path,
    spectra_path: Path,
    identifications_path: Path | None,
    features_path: Path | None,
    design_path: Path | None,
    sample_id: str | None,
    search_adapter: str,
    scheduler: str,
    container_image: str,
    artifacts_dir: Path | None,
    completed_steps: tuple[str, ...],
    out_path: Path | None,
    dag_out: Path | None,
    job_out: Path | None,
    checkpoint_out: Path | None,
) -> None:
    """Build a workflow-runtime bundle for digest/search/FDR/quant/QC execution."""
    try:
        bundle = build_proteomics_workflow_runtime_bundle(
            proteins_path=proteins_path,
            spectra_path=spectra_path,
            identifications_path=identifications_path,
            features_path=features_path,
            design_path=design_path,
            sample_id=sample_id,
            search_adapter_kind=SearchAdapterKind(search_adapter),
            scheduler=WorkflowSchedulerKind(scheduler),
            default_container_image=container_image,
            artifacts_dir=artifacts_dir,
            completed_step_ids=tuple(completed_steps),
        )
        if dag_out is not None:
            dag_out.write_text(
                bundle.dag_plan.to_stable_json() + "\n", encoding="utf-8"
            )
        if job_out is not None:
            job_out.write_text(bundle.hpc_job.script_text, encoding="utf-8")
        if checkpoint_out is not None:
            checkpoint_out.write_text(
                bundle.checkpoint.to_stable_json() + "\n", encoding="utf-8"
            )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(bundle, out_path=out_path)


@cli.command("workflow-validate")
@click.option(
    "--proteins",
    "proteins_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--spectra",
    "spectra_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--identifications",
    "identifications_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--features",
    "features_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--sample-id", default=None)
@click.option(
    "--search-adapter",
    type=_search_adapter_choice(),
    default=SearchAdapterKind.GENERIC.value,
    show_default=True,
)
@click.option(
    "--scheduler",
    type=_workflow_scheduler_choice(),
    default=WorkflowSchedulerKind.SLURM.value,
    show_default=True,
)
@click.option(
    "--container-image",
    default="ghcr.io/bijux/proteomics-runtime:stable",
    show_default=True,
)
@click.option(
    "--artifacts-dir", type=click.Path(path_type=Path, file_okay=False), default=None
)
@click.option("--completed-step", "completed_steps", multiple=True)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def workflow_validate_command(
    proteins_path: Path,
    spectra_path: Path,
    identifications_path: Path | None,
    features_path: Path | None,
    design_path: Path | None,
    sample_id: str | None,
    search_adapter: str,
    scheduler: str,
    container_image: str,
    artifacts_dir: Path | None,
    completed_steps: tuple[str, ...],
    out_path: Path | None,
) -> None:
    """Validate workflow runtime integrity without executing the workflow."""
    try:
        bundle = build_proteomics_workflow_runtime_bundle(
            proteins_path=proteins_path,
            spectra_path=spectra_path,
            identifications_path=identifications_path,
            features_path=features_path,
            design_path=design_path,
            sample_id=sample_id,
            search_adapter_kind=SearchAdapterKind(search_adapter),
            scheduler=WorkflowSchedulerKind(scheduler),
            default_container_image=container_image,
            artifacts_dir=artifacts_dir,
            completed_step_ids=tuple(completed_steps),
        )
        report = build_workflow_runtime_validation_report(bundle)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(report, out_path=out_path)


@cli.group("qc")
def qc_group() -> None:
    """Build operator-facing LC-MS QC reports and artifacts."""


@cli.group("isotope-labeling")
def isotope_labeling_group() -> None:
    """Build stable-isotope labeling review outputs and quantification ledgers."""


@cli.group("interpretation")
def interpretation_group() -> None:
    """Map protein tables onto governed biological annotation surfaces."""


@cli.group("multiplex")
def multiplex_group() -> None:
    """Build multiplex reporter-ion import and matrix review outputs."""


@interpretation_group.command("annotate-proteins")
@click.argument(
    "protein_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--protein-ref-column", default="protein_ref", show_default=True)
@click.option("--row-id-column", default="row_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option(
    "--annotation-protein-ref-column",
    default="protein_ref",
    show_default=True,
)
@click.option(
    "--annotation-gene-symbol-column",
    default="gene_symbol",
    show_default=True,
)
@click.option(
    "--annotation-description-column",
    default="description",
    show_default=True,
)
@click.option(
    "--annotation-organism-column",
    default="organism",
    show_default=True,
)
@click.option(
    "--annotation-identifier-column",
    default="annotation_identifier",
    show_default=True,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--annotated-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unmapped-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-input-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-annotation-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def annotate_proteins_command(
    protein_tsv: Path,
    proteins_fasta: Path,
    annotation_tsv: Path | None,
    protein_ref_column: str,
    row_id_column: str,
    protein_separator: str,
    annotation_protein_ref_column: str,
    annotation_gene_symbol_column: str,
    annotation_description_column: str,
    annotation_organism_column: str,
    annotation_identifier_column: str,
    summary_tsv_out: Path | None,
    annotated_tsv_out: Path | None,
    unmapped_tsv_out: Path | None,
    rejected_input_tsv_out: Path | None,
    rejected_annotation_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Map protein tables onto FASTA and optional custom biological annotations."""
    try:
        protein_table = parse_protein_reference_table(
            protein_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        fasta_report = parse_fasta_document(
            proteins_fasta.read_text(encoding="utf-8"),
            mode=FastaParseMode.STRICT,
        )
        if fasta_report.rejected_records:
            rejected = ", ".join(
                record.source_identifier for record in fasta_report.rejected_records
            )
            raise click.ClickException(
                f"FASTA input contains rejected records under strict mode: {rejected}"
            )
        annotation_report = (
            None
            if annotation_tsv is None
            else parse_protein_annotation_table(
                annotation_tsv,
                mapping=ProteinAnnotationColumnMapping(
                    protein_ref=annotation_protein_ref_column,
                    gene_symbol=annotation_gene_symbol_column,
                    description=annotation_description_column,
                    organism=annotation_organism_column,
                    annotation_identifier=annotation_identifier_column,
                ),
            )
        )
        mapping_report = build_protein_annotation_mapping_report(
            protein_table.accepted_entries,
            fasta_report.accepted_records,
            custom_annotations=()
            if annotation_report is None
            else annotation_report.accepted_records,
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_protein_annotation_summary_tsv(mapping_report),
            encoding="utf-8",
        )
    if annotated_tsv_out is not None:
        annotated_tsv_out.write_text(
            render_protein_annotation_tsv(mapping_report),
            encoding="utf-8",
        )
    if unmapped_tsv_out is not None:
        unmapped_tsv_out.write_text(
            render_unmapped_protein_annotation_tsv(mapping_report),
            encoding="utf-8",
        )
    if rejected_input_tsv_out is not None:
        rejected_input_tsv_out.write_text(
            render_rejected_protein_reference_tsv(protein_table),
            encoding="utf-8",
        )
    if rejected_annotation_tsv_out is not None and annotation_report is not None:
        rejected_annotation_tsv_out.write_text(
            render_rejected_protein_annotation_tsv(annotation_report),
            encoding="utf-8",
        )

    payload = {
        "protein_table": protein_table.to_dict(),
        "annotation_table": (
            None if annotation_report is None else annotation_report.to_dict()
        ),
        "mapping_report": mapping_report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "annotated_tsv": (
                None if annotated_tsv_out is None else str(annotated_tsv_out)
            ),
            "unmapped_tsv": None if unmapped_tsv_out is None else str(unmapped_tsv_out),
            "rejected_input_tsv": (
                None
                if rejected_input_tsv_out is None
                else str(rejected_input_tsv_out)
            ),
            "rejected_annotation_tsv": (
                None
                if rejected_annotation_tsv_out is None or annotation_report is None
                else str(rejected_annotation_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@interpretation_group.command("map-context")
@click.argument(
    "protein_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "context_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--protein-ref-column", default="protein_ref", show_default=True)
@click.option("--row-id-column", default="row_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option(
    "--context-protein-ref-column",
    default="protein_ref",
    show_default=True,
)
@click.option("--context-id-column", default="context_id", show_default=True)
@click.option("--context-kind-column", default="context_kind", show_default=True)
@click.option("--context-name-column", default="context_name", show_default=True)
@click.option("--source-name-column", default="source_name", show_default=True)
@click.option(
    "--source-accession-column",
    default="source_accession",
    show_default=True,
)
@click.option("--evidence-column", default="evidence", show_default=True)
@click.option(
    "--fixed-context-kind",
    type=click.Choice([kind.value for kind in BiologicalContextKind]),
    default=None,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--mapped-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--term-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unmapped-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-input-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-context-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def map_context_command(
    protein_tsv: Path,
    context_tsv: Path,
    protein_ref_column: str,
    row_id_column: str,
    protein_separator: str,
    context_protein_ref_column: str,
    context_id_column: str,
    context_kind_column: str,
    context_name_column: str,
    source_name_column: str,
    source_accession_column: str,
    evidence_column: str,
    fixed_context_kind: str | None,
    summary_tsv_out: Path | None,
    mapped_tsv_out: Path | None,
    term_tsv_out: Path | None,
    unmapped_tsv_out: Path | None,
    rejected_input_tsv_out: Path | None,
    rejected_context_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Map protein tables onto user-supplied drug, disease, phenotype, or compartment context."""
    try:
        protein_table = parse_protein_reference_table(
            protein_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        context_table = parse_biological_context_table(
            context_tsv,
            mapping=BiologicalContextColumnMapping(
                protein_ref=context_protein_ref_column,
                context_id=context_id_column,
                context_kind=context_kind_column,
                context_name=context_name_column,
                source_name=source_name_column,
                source_accession=source_accession_column,
                evidence=evidence_column,
            ),
            fixed_context_kind=(
                None
                if fixed_context_kind is None
                else BiologicalContextKind(fixed_context_kind)
            ),
        )
        mapping_report = build_biological_context_mapping_report(
            protein_table.accepted_entries,
            context_table.accepted_records,
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_biological_context_mapping_summary_tsv(mapping_report),
            encoding="utf-8",
        )
    if mapped_tsv_out is not None:
        mapped_tsv_out.write_text(
            render_biological_context_mapping_tsv(mapping_report),
            encoding="utf-8",
        )
    if term_tsv_out is not None:
        term_tsv_out.write_text(
            render_biological_context_term_tsv(mapping_report),
            encoding="utf-8",
        )
    if unmapped_tsv_out is not None:
        unmapped_tsv_out.write_text(
            render_unmapped_biological_context_tsv(mapping_report),
            encoding="utf-8",
        )
    if rejected_input_tsv_out is not None:
        rejected_input_tsv_out.write_text(
            render_rejected_protein_reference_tsv(protein_table),
            encoding="utf-8",
        )
    if rejected_context_tsv_out is not None:
        rejected_context_tsv_out.write_text(
            render_rejected_biological_context_tsv(context_table),
            encoding="utf-8",
        )

    payload = {
        "protein_table": protein_table.to_dict(),
        "context_table": context_table.to_dict(),
        "mapping_report": mapping_report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "mapped_tsv": None if mapped_tsv_out is None else str(mapped_tsv_out),
            "term_tsv": None if term_tsv_out is None else str(term_tsv_out),
            "unmapped_tsv": None if unmapped_tsv_out is None else str(unmapped_tsv_out),
            "rejected_input_tsv": (
                None
                if rejected_input_tsv_out is None
                else str(rejected_input_tsv_out)
            ),
            "rejected_context_tsv": (
                None
                if rejected_context_tsv_out is None
                else str(rejected_context_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@interpretation_group.command("map-orthologs")
@click.argument(
    "protein_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "ortholog_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--source-species", required=True)
@click.option("--target-species", required=True)
@click.option("--protein-ref-column", default="protein_ref", show_default=True)
@click.option("--row-id-column", default="row_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option(
    "--ortholog-source-species-column",
    default="source_species",
    show_default=True,
)
@click.option(
    "--ortholog-source-protein-ref-column",
    default="source_protein_ref",
    show_default=True,
)
@click.option(
    "--ortholog-target-species-column",
    default="target_species",
    show_default=True,
)
@click.option(
    "--ortholog-target-protein-ref-column",
    default="target_protein_ref",
    show_default=True,
)
@click.option(
    "--ortholog-source-gene-symbol-column",
    default="source_gene_symbol",
    show_default=True,
)
@click.option(
    "--ortholog-target-gene-symbol-column",
    default="target_gene_symbol",
    show_default=True,
)
@click.option(
    "--ortholog-evidence-column",
    default="evidence",
    show_default=True,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--mapped-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unmapped-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-input-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-ortholog-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def map_orthologs_command(
    protein_tsv: Path,
    ortholog_tsv: Path,
    source_species: str,
    target_species: str,
    protein_ref_column: str,
    row_id_column: str,
    protein_separator: str,
    ortholog_source_species_column: str,
    ortholog_source_protein_ref_column: str,
    ortholog_target_species_column: str,
    ortholog_target_protein_ref_column: str,
    ortholog_source_gene_symbol_column: str,
    ortholog_target_gene_symbol_column: str,
    ortholog_evidence_column: str,
    summary_tsv_out: Path | None,
    mapped_tsv_out: Path | None,
    unmapped_tsv_out: Path | None,
    rejected_input_tsv_out: Path | None,
    rejected_ortholog_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Map input proteins onto a selected ortholog species pair."""

    try:
        protein_table = parse_protein_reference_table(
            protein_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        ortholog_table = parse_ortholog_table(
            ortholog_tsv,
            mapping=OrthologColumnMapping(
                source_species=ortholog_source_species_column,
                source_protein_ref=ortholog_source_protein_ref_column,
                target_species=ortholog_target_species_column,
                target_protein_ref=ortholog_target_protein_ref_column,
                source_gene_symbol=ortholog_source_gene_symbol_column,
                target_gene_symbol=ortholog_target_gene_symbol_column,
                evidence=ortholog_evidence_column,
            ),
        )
        mapping_report = build_ortholog_mapping_report(
            protein_table.accepted_entries,
            ortholog_table.accepted_records,
            source_species=source_species,
            target_species=target_species,
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_ortholog_mapping_summary_tsv(mapping_report),
            encoding="utf-8",
        )
    if mapped_tsv_out is not None:
        mapped_tsv_out.write_text(
            render_mapped_ortholog_tsv(mapping_report),
            encoding="utf-8",
        )
    if unmapped_tsv_out is not None:
        unmapped_tsv_out.write_text(
            render_unmapped_ortholog_tsv(mapping_report),
            encoding="utf-8",
        )
    if rejected_input_tsv_out is not None:
        rejected_input_tsv_out.write_text(
            render_rejected_protein_reference_tsv(protein_table),
            encoding="utf-8",
        )
    if rejected_ortholog_tsv_out is not None:
        rejected_ortholog_tsv_out.write_text(
            render_rejected_ortholog_tsv(ortholog_table),
            encoding="utf-8",
        )

    payload = {
        "protein_table": protein_table.to_dict(),
        "ortholog_table": ortholog_table.to_dict(),
        "mapping_report": mapping_report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "mapped_tsv": None if mapped_tsv_out is None else str(mapped_tsv_out),
            "unmapped_tsv": None if unmapped_tsv_out is None else str(unmapped_tsv_out),
            "rejected_input_tsv": (
                None
                if rejected_input_tsv_out is None
                else str(rejected_input_tsv_out)
            ),
            "rejected_ortholog_tsv": (
                None
                if rejected_ortholog_tsv_out is None
                else str(rejected_ortholog_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@interpretation_group.command("protein-set-score")
@click.argument(
    "input_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "protein_set_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--aggregation",
    type=_quant_rollup_choice(),
    default=QuantRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=3, show_default=True)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--mz-column", default="mz", show_default=True)
@click.option(
    "--retention-time-column", default="retention_time_seconds", show_default=True
)
@click.option("--missing-reason-column", default="missing_reason", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--set-id-column", default="set_id", show_default=True)
@click.option("--set-name-column", default="set_name", show_default=True)
@click.option("--set-category-column", default="set_category", show_default=True)
@click.option("--source-name-column", default="source_name", show_default=True)
@click.option(
    "--source-accession-column",
    default="source_accession",
    show_default=True,
)
@click.option("--set-protein-ref-column", default="protein_ref", show_default=True)
@click.option(
    "--minimum-observed-member-count",
    type=int,
    default=2,
    show_default=True,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--sample-score-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--condition-score-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--condition-comparison-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unresolved-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-set-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def protein_set_score_command(
    input_table: Path,
    protein_set_tsv: Path,
    design_path: Path | None,
    aggregation: str,
    top_n: int,
    normalization: str,
    sample_column: str,
    feature_id_column: str,
    peptide_column: str,
    intensity_column: str,
    protein_refs_column: str | None,
    charge_column: str | None,
    mz_column: str | None,
    retention_time_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    set_id_column: str,
    set_name_column: str,
    set_category_column: str,
    source_name_column: str,
    source_accession_column: str,
    set_protein_ref_column: str,
    minimum_observed_member_count: int,
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    sample_score_tsv_out: Path | None,
    condition_score_tsv_out: Path | None,
    condition_comparison_tsv_out: Path | None,
    unresolved_tsv_out: Path | None,
    rejected_set_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Score user-defined protein sets across normalized study samples."""

    try:
        mapping = Ms1FeatureColumnMapping(
            sample_id=sample_column,
            feature_id=feature_id_column,
            peptide=peptide_column,
            intensity=intensity_column,
            protein_refs=protein_refs_column,
            charge=charge_column,
            mz=mz_column,
            retention_time_seconds=retention_time_column,
            missing_reason=missing_reason_column,
            protein_separator=protein_separator,
        )
        parse_report = parse_ms1_feature_table(input_table, mapping=mapping)
        design_entries: tuple[ExperimentalDesignEntry, ...] = ()
        if design_path is not None:
            design_report = parse_experimental_design_table(design_path)
            if design_report.rejected_rows:
                raise click.ClickException("design table contains rejected rows")
            design_entries = design_report.accepted_entries
        raw_table = build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod(aggregation),
            top_n=top_n,
        )
        protein_sets = parse_protein_set_table(
            protein_set_tsv,
            mapping=ProteinSetColumnMapping(
                set_id=set_id_column,
                protein_ref=set_protein_ref_column,
                set_name=set_name_column,
                set_category=set_category_column,
                source_name=source_name_column,
                source_accession=source_accession_column,
            ),
        )
        report = build_protein_set_scoring_report(
            normalize_label_free_table(
                raw_table,
                method=NormalizationMethod(normalization),
            ),
            protein_sets.accepted_records,
            design_entries=design_entries,
            policy=ProteinSetScoringPolicy(
                minimum_observed_member_count=minimum_observed_member_count,
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_protein_set_scoring_summary_tsv(report),
            encoding="utf-8",
        )
    if matrix_tsv_out is not None:
        matrix_tsv_out.write_text(
            render_protein_set_score_matrix_tsv(report),
            encoding="utf-8",
        )
    if sample_score_tsv_out is not None:
        sample_score_tsv_out.write_text(
            render_protein_set_sample_score_tsv(report),
            encoding="utf-8",
        )
    if condition_score_tsv_out is not None:
        condition_score_tsv_out.write_text(
            render_protein_set_condition_score_tsv(report),
            encoding="utf-8",
        )
    if condition_comparison_tsv_out is not None:
        condition_comparison_tsv_out.write_text(
            render_protein_set_condition_comparison_tsv(report),
            encoding="utf-8",
        )
    if unresolved_tsv_out is not None:
        unresolved_tsv_out.write_text(
            render_protein_set_unresolved_member_tsv(report),
            encoding="utf-8",
        )
    if rejected_set_tsv_out is not None:
        rejected_set_tsv_out.write_text(
            render_rejected_protein_set_tsv(protein_sets),
            encoding="utf-8",
        )

    payload = {
        "accepted_features": len(parse_report.accepted_records),
        "rejected_features": len(parse_report.rejected_rows),
        "protein_sets": protein_sets.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "matrix_tsv": None if matrix_tsv_out is None else str(matrix_tsv_out),
            "sample_score_tsv": (
                None if sample_score_tsv_out is None else str(sample_score_tsv_out)
            ),
            "condition_score_tsv": (
                None
                if condition_score_tsv_out is None
                else str(condition_score_tsv_out)
            ),
            "condition_comparison_tsv": (
                None
                if condition_comparison_tsv_out is None
                else str(condition_comparison_tsv_out)
            ),
            "unresolved_tsv": (
                None if unresolved_tsv_out is None else str(unresolved_tsv_out)
            ),
            "rejected_set_tsv": (
                None
                if rejected_set_tsv_out is None
                else str(rejected_set_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@interpretation_group.command("ppi-modules")
@click.argument(
    "significant_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "ppi_edge_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--protein-set-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--protein-ref-column", default="protein_ref", show_default=True)
@click.option("--row-id-column", default="row_id", show_default=True)
@click.option("--edge-protein-ref-a-column", default="protein_ref_a", show_default=True)
@click.option("--edge-protein-ref-b-column", default="protein_ref_b", show_default=True)
@click.option("--edge-source-name-column", default="source_name", show_default=True)
@click.option(
    "--edge-source-accession-column",
    default="source_accession",
    show_default=True,
)
@click.option("--edge-score-column", default="interaction_score", show_default=True)
@click.option("--set-id-column", default="set_id", show_default=True)
@click.option("--set-name-column", default="set_name", show_default=True)
@click.option("--set-category-column", default="set_category", show_default=True)
@click.option("--source-name-column", default="source_name", show_default=True)
@click.option(
    "--source-accession-column",
    default="source_accession",
    show_default=True,
)
@click.option("--set-protein-ref-column", default="protein_ref", show_default=True)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--edge-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--module-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--isolated-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--module-enrichment-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-edge-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def ppi_modules_command(
    significant_tsv: Path,
    ppi_edge_tsv: Path,
    protein_set_tsv: Path | None,
    protein_ref_column: str,
    row_id_column: str,
    edge_protein_ref_a_column: str,
    edge_protein_ref_b_column: str,
    edge_source_name_column: str,
    edge_source_accession_column: str,
    edge_score_column: str,
    set_id_column: str,
    set_name_column: str,
    set_category_column: str,
    source_name_column: str,
    source_accession_column: str,
    set_protein_ref_column: str,
    summary_tsv_out: Path | None,
    edge_tsv_out: Path | None,
    module_tsv_out: Path | None,
    isolated_tsv_out: Path | None,
    module_enrichment_tsv_out: Path | None,
    rejected_edge_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Build a significant-protein PPI subnetwork and connected modules."""

    try:
        significant = parse_protein_reference_table(
            significant_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
        )
        edge_report = parse_ppi_edge_table(
            ppi_edge_tsv,
            mapping=PpiEdgeColumnMapping(
                protein_ref_a=edge_protein_ref_a_column,
                protein_ref_b=edge_protein_ref_b_column,
                source_name=edge_source_name_column,
                source_accession=edge_source_accession_column,
                interaction_score=edge_score_column,
            ),
        )
        protein_sets = (
            None
            if protein_set_tsv is None
            else parse_protein_set_table(
                protein_set_tsv,
                mapping=ProteinSetColumnMapping(
                    set_id=set_id_column,
                    protein_ref=set_protein_ref_column,
                    set_name=set_name_column,
                    set_category=set_category_column,
                    source_name=source_name_column,
                    source_accession=source_accession_column,
                ),
            )
        )
        report = build_ppi_network_module_report(
            significant.accepted_entries,
            edge_report.accepted_records,
            protein_set_records=(
                () if protein_sets is None else protein_sets.accepted_records
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_ppi_network_module_summary_tsv(report),
            encoding="utf-8",
        )
    if edge_tsv_out is not None:
        edge_tsv_out.write_text(
            render_ppi_network_edge_tsv(report),
            encoding="utf-8",
        )
    if module_tsv_out is not None:
        module_tsv_out.write_text(
            render_ppi_module_tsv(report),
            encoding="utf-8",
        )
    if isolated_tsv_out is not None:
        isolated_tsv_out.write_text(
            render_ppi_isolated_protein_tsv(report),
            encoding="utf-8",
        )
    if module_enrichment_tsv_out is not None:
        module_enrichment_tsv_out.write_text(
            render_ppi_module_enrichment_tsv(report),
            encoding="utf-8",
        )
    if rejected_edge_tsv_out is not None:
        rejected_edge_tsv_out.write_text(
            render_rejected_ppi_edge_tsv(edge_report),
            encoding="utf-8",
        )

    payload = {
        "significant": significant.to_dict(),
        "ppi_edges": edge_report.to_dict(),
        "protein_sets": None if protein_sets is None else protein_sets.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "edge_tsv": None if edge_tsv_out is None else str(edge_tsv_out),
            "module_tsv": None if module_tsv_out is None else str(module_tsv_out),
            "isolated_tsv": None if isolated_tsv_out is None else str(isolated_tsv_out),
            "module_enrichment_tsv": (
                None
                if module_enrichment_tsv_out is None
                else str(module_enrichment_tsv_out)
            ),
            "rejected_edge_tsv": (
                None
                if rejected_edge_tsv_out is None
                else str(rejected_edge_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@interpretation_group.command("protein-set-enrichment")
@click.argument(
    "foreground_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "protein_set_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--background-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--protein-ref-column", default="protein_ref", show_default=True)
@click.option("--row-id-column", default="row_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--set-id-column", default="set_id", show_default=True)
@click.option("--set-name-column", default="set_name", show_default=True)
@click.option("--set-category-column", default="set_category", show_default=True)
@click.option("--source-name-column", default="source_name", show_default=True)
@click.option(
    "--source-accession-column",
    default="source_accession",
    show_default=True,
)
@click.option("--set-protein-ref-column", default="protein_ref", show_default=True)
@click.option(
    "--missing-background-policy",
    type=click.Choice(
        [policy.value for policy in ProteinSetEnrichmentMissingBackgroundPolicy]
    ),
    default=ProteinSetEnrichmentMissingBackgroundPolicy.REJECT.value,
    show_default=True,
)
@click.option(
    "--max-adjusted-p-value",
    default=0.1,
    show_default=True,
    type=float,
)
@click.option(
    "--min-enrichment-ratio",
    default=1.0,
    show_default=True,
    type=float,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--result-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--universe-gap-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-set-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def protein_set_enrichment_command(
    foreground_tsv: Path,
    protein_set_tsv: Path,
    background_tsv: Path | None,
    protein_ref_column: str,
    row_id_column: str,
    protein_separator: str,
    set_id_column: str,
    set_name_column: str,
    set_category_column: str,
    source_name_column: str,
    source_accession_column: str,
    set_protein_ref_column: str,
    missing_background_policy: str,
    max_adjusted_p_value: float,
    min_enrichment_ratio: float,
    summary_tsv_out: Path | None,
    result_tsv_out: Path | None,
    universe_gap_tsv_out: Path | None,
    rejected_set_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Run generic enrichment over compartment and custom protein-set definitions."""
    try:
        foreground = parse_protein_reference_table(
            foreground_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        background = (
            None
            if background_tsv is None
            else parse_protein_reference_table(
                background_tsv,
                mapping=ProteinReferenceColumnMapping(
                    protein_ref=protein_ref_column,
                    row_id=row_id_column,
                ),
                protein_separator=protein_separator,
            )
        )
        protein_sets = parse_protein_set_table(
            protein_set_tsv,
            mapping=ProteinSetColumnMapping(
                set_id=set_id_column,
                protein_ref=set_protein_ref_column,
                set_name=set_name_column,
                set_category=set_category_column,
                source_name=source_name_column,
                source_accession=source_accession_column,
            ),
        )
        report = build_protein_set_enrichment_report(
            foreground.accepted_entries,
            protein_sets.accepted_records,
            background_entries=(
                None if background is None else background.accepted_entries
            ),
            policy=ProteinSetEnrichmentPolicy(
                missing_background_policy=ProteinSetEnrichmentMissingBackgroundPolicy(
                    missing_background_policy
                ),
                max_adjusted_p_value=max_adjusted_p_value,
                min_enrichment_ratio=min_enrichment_ratio,
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_protein_set_enrichment_summary_tsv(report),
            encoding="utf-8",
        )
    if result_tsv_out is not None:
        result_tsv_out.write_text(
            render_protein_set_enrichment_tsv(report),
            encoding="utf-8",
        )
    if universe_gap_tsv_out is not None:
        universe_gap_tsv_out.write_text(
            render_protein_set_universe_gap_tsv(report),
            encoding="utf-8",
        )
    if rejected_set_tsv_out is not None:
        rejected_set_tsv_out.write_text(
            render_rejected_protein_set_membership_tsv(protein_sets),
            encoding="utf-8",
        )

    payload = {
        "foreground": foreground.to_dict(),
        "background": None if background is None else background.to_dict(),
        "protein_sets": protein_sets.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "result_tsv": None if result_tsv_out is None else str(result_tsv_out),
            "universe_gap_tsv": (
                None
                if universe_gap_tsv_out is None
                else str(universe_gap_tsv_out)
            ),
            "rejected_set_tsv": (
                None
                if rejected_set_tsv_out is None
                else str(rejected_set_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@interpretation_group.command("go-enrichment")
@click.argument(
    "foreground_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "background_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "go_annotation_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--protein-ref-column", default="protein_ref", show_default=True)
@click.option("--row-id-column", default="row_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--go-protein-ref-column", default="protein_ref", show_default=True)
@click.option("--go-term-id-column", default="go_term_id", show_default=True)
@click.option("--go-term-name-column", default="go_term_name", show_default=True)
@click.option("--go-aspect-column", default="go_aspect", show_default=True)
@click.option("--evidence-code-column", default="evidence_code", show_default=True)
@click.option(
    "--max-adjusted-p-value",
    default=0.1,
    show_default=True,
    type=float,
)
@click.option(
    "--min-enrichment-ratio",
    default=1.0,
    show_default=True,
    type=float,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--term-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unannotated-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-annotation-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def go_enrichment_command(
    foreground_tsv: Path,
    background_tsv: Path,
    go_annotation_tsv: Path,
    protein_ref_column: str,
    row_id_column: str,
    protein_separator: str,
    go_protein_ref_column: str,
    go_term_id_column: str,
    go_term_name_column: str,
    go_aspect_column: str,
    evidence_code_column: str,
    max_adjusted_p_value: float,
    min_enrichment_ratio: float,
    summary_tsv_out: Path | None,
    term_tsv_out: Path | None,
    unannotated_tsv_out: Path | None,
    rejected_annotation_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Run GO term enrichment over foreground and background protein sets."""
    try:
        foreground = parse_protein_reference_table(
            foreground_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        background = parse_protein_reference_table(
            background_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        annotations = parse_go_annotation_table(
            go_annotation_tsv,
            mapping=GoAnnotationColumnMapping(
                protein_ref=go_protein_ref_column,
                go_term_id=go_term_id_column,
                go_term_name=go_term_name_column,
                go_aspect=go_aspect_column,
                evidence_code=evidence_code_column,
            ),
        )
        report = apply_go_enrichment_multiple_testing(
            build_go_enrichment_report(
                foreground.accepted_entries,
                background.accepted_entries,
                annotations.accepted_records,
            ),
            policy=GoEnrichmentCorrectionPolicy(
                max_adjusted_p_value=max_adjusted_p_value,
                min_enrichment_ratio=min_enrichment_ratio,
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_go_enrichment_summary_tsv(report),
            encoding="utf-8",
        )
    if term_tsv_out is not None:
        term_tsv_out.write_text(
            render_go_enrichment_term_tsv(report),
            encoding="utf-8",
        )
    if unannotated_tsv_out is not None:
        unannotated_tsv_out.write_text(
            render_go_enrichment_unannotated_tsv(report),
            encoding="utf-8",
        )
    if rejected_annotation_tsv_out is not None:
        rejected_annotation_tsv_out.write_text(
            render_rejected_go_annotation_tsv(annotations),
            encoding="utf-8",
        )

    payload = {
        "foreground": foreground.to_dict(),
        "background": background.to_dict(),
        "go_annotations": annotations.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "term_tsv": None if term_tsv_out is None else str(term_tsv_out),
            "unannotated_tsv": (
                None if unannotated_tsv_out is None else str(unannotated_tsv_out)
            ),
            "rejected_annotation_tsv": (
                None
                if rejected_annotation_tsv_out is None
                else str(rejected_annotation_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@interpretation_group.command("pathway-enrichment")
@click.argument(
    "foreground_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "background_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "pathway_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--fasta",
    "proteins_fasta",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--protein-ref-column", default="protein_ref", show_default=True)
@click.option("--row-id-column", default="row_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--pathway-id-column", default="pathway_id", show_default=True)
@click.option("--pathway-name-column", default="pathway_name", show_default=True)
@click.option("--source-name-column", default="source_name", show_default=True)
@click.option(
    "--source-accession-column",
    default="source_accession",
    show_default=True,
)
@click.option("--pathway-protein-ref-column", default="protein_ref", show_default=True)
@click.option("--gene-symbol-column", default="gene_symbol", show_default=True)
@click.option(
    "--annotation-protein-ref-column",
    default="protein_ref",
    show_default=True,
)
@click.option(
    "--annotation-gene-symbol-column",
    default="gene_symbol",
    show_default=True,
)
@click.option(
    "--annotation-description-column",
    default="description",
    show_default=True,
)
@click.option(
    "--annotation-organism-column",
    default="organism",
    show_default=True,
)
@click.option(
    "--annotation-identifier-column",
    default="annotation_identifier",
    show_default=True,
)
@click.option(
    "--max-adjusted-p-value",
    default=0.1,
    show_default=True,
    type=float,
)
@click.option(
    "--min-enrichment-ratio",
    default=1.0,
    show_default=True,
    type=float,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--pathway-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unresolved-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-pathway-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def pathway_enrichment_command(
    foreground_tsv: Path,
    background_tsv: Path,
    pathway_tsv: Path,
    proteins_fasta: Path | None,
    annotation_tsv: Path | None,
    protein_ref_column: str,
    row_id_column: str,
    protein_separator: str,
    pathway_id_column: str,
    pathway_name_column: str,
    source_name_column: str,
    source_accession_column: str,
    pathway_protein_ref_column: str,
    gene_symbol_column: str,
    annotation_protein_ref_column: str,
    annotation_gene_symbol_column: str,
    annotation_description_column: str,
    annotation_organism_column: str,
    annotation_identifier_column: str,
    max_adjusted_p_value: float,
    min_enrichment_ratio: float,
    summary_tsv_out: Path | None,
    pathway_tsv_out: Path | None,
    unresolved_tsv_out: Path | None,
    rejected_pathway_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Run pathway enrichment over foreground and background protein sets."""
    try:
        foreground = parse_protein_reference_table(
            foreground_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        background = parse_protein_reference_table(
            background_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        pathway_memberships = parse_pathway_membership_table(
            pathway_tsv,
            mapping=PathwayMembershipColumnMapping(
                pathway_id=pathway_id_column,
                pathway_name=pathway_name_column,
                source_name=source_name_column,
                source_accession=source_accession_column,
                protein_ref=pathway_protein_ref_column,
                gene_symbol=gene_symbol_column,
            ),
        )
        fasta_report = (
            None
            if proteins_fasta is None
            else parse_fasta_document(
                proteins_fasta.read_text(encoding="utf-8"),
                mode=FastaParseMode.STRICT,
            )
        )
        if fasta_report is not None and fasta_report.rejected_records:
            rejected = ", ".join(
                record.source_identifier for record in fasta_report.rejected_records
            )
            raise click.ClickException(
                f"FASTA input contains rejected records under strict mode: {rejected}"
            )
        annotation_report = (
            None
            if annotation_tsv is None
            else parse_protein_annotation_table(
                annotation_tsv,
                mapping=ProteinAnnotationColumnMapping(
                    protein_ref=annotation_protein_ref_column,
                    gene_symbol=annotation_gene_symbol_column,
                    description=annotation_description_column,
                    organism=annotation_organism_column,
                    annotation_identifier=annotation_identifier_column,
                ),
            )
        )
        report = apply_pathway_enrichment_multiple_testing(
            build_pathway_enrichment_report(
                foreground.accepted_entries,
                background.accepted_entries,
                pathway_memberships.accepted_records,
                fasta_records=()
                if fasta_report is None
                else fasta_report.accepted_records,
                custom_annotations=()
                if annotation_report is None
                else annotation_report.accepted_records,
            ),
            policy=PathwayEnrichmentCorrectionPolicy(
                max_adjusted_p_value=max_adjusted_p_value,
                min_enrichment_ratio=min_enrichment_ratio,
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_pathway_enrichment_summary_tsv(report),
            encoding="utf-8",
        )
    if pathway_tsv_out is not None:
        pathway_tsv_out.write_text(
            render_pathway_enrichment_entry_tsv(report),
            encoding="utf-8",
        )
    if unresolved_tsv_out is not None:
        unresolved_tsv_out.write_text(
            render_pathway_unresolved_member_tsv(report),
            encoding="utf-8",
        )
    if rejected_pathway_tsv_out is not None:
        rejected_pathway_tsv_out.write_text(
            render_rejected_pathway_membership_tsv(pathway_memberships),
            encoding="utf-8",
        )

    payload = {
        "foreground": foreground.to_dict(),
        "background": background.to_dict(),
        "pathway_memberships": pathway_memberships.to_dict(),
        "annotation_table": (
            None if annotation_report is None else annotation_report.to_dict()
        ),
        "fasta_report": None if fasta_report is None else fasta_report.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "pathway_tsv": None if pathway_tsv_out is None else str(pathway_tsv_out),
            "unresolved_tsv": (
                None if unresolved_tsv_out is None else str(unresolved_tsv_out)
            ),
            "rejected_pathway_tsv": (
                None
                if rejected_pathway_tsv_out is None
                else str(rejected_pathway_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@interpretation_group.command("complex-enrichment")
@click.argument(
    "foreground_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "background_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "complex_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--fasta",
    "proteins_fasta",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--protein-ref-column", default="protein_ref", show_default=True)
@click.option("--row-id-column", default="row_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--complex-id-column", default="complex_id", show_default=True)
@click.option("--complex-name-column", default="complex_name", show_default=True)
@click.option("--source-name-column", default="source_name", show_default=True)
@click.option(
    "--source-accession-column",
    default="source_accession",
    show_default=True,
)
@click.option("--complex-protein-ref-column", default="protein_ref", show_default=True)
@click.option("--gene-symbol-column", default="gene_symbol", show_default=True)
@click.option(
    "--annotation-protein-ref-column",
    default="protein_ref",
    show_default=True,
)
@click.option(
    "--annotation-gene-symbol-column",
    default="gene_symbol",
    show_default=True,
)
@click.option(
    "--annotation-description-column",
    default="description",
    show_default=True,
)
@click.option(
    "--annotation-organism-column",
    default="organism",
    show_default=True,
)
@click.option(
    "--annotation-identifier-column",
    default="annotation_identifier",
    show_default=True,
)
@click.option(
    "--max-adjusted-p-value",
    default=0.1,
    show_default=True,
    type=float,
)
@click.option(
    "--min-enrichment-ratio",
    default=1.0,
    show_default=True,
    type=float,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--complex-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unresolved-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-complex-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def complex_enrichment_command(
    foreground_tsv: Path,
    background_tsv: Path,
    complex_tsv: Path,
    proteins_fasta: Path | None,
    annotation_tsv: Path | None,
    protein_ref_column: str,
    row_id_column: str,
    protein_separator: str,
    complex_id_column: str,
    complex_name_column: str,
    source_name_column: str,
    source_accession_column: str,
    complex_protein_ref_column: str,
    gene_symbol_column: str,
    annotation_protein_ref_column: str,
    annotation_gene_symbol_column: str,
    annotation_description_column: str,
    annotation_organism_column: str,
    annotation_identifier_column: str,
    max_adjusted_p_value: float,
    min_enrichment_ratio: float,
    summary_tsv_out: Path | None,
    complex_tsv_out: Path | None,
    unresolved_tsv_out: Path | None,
    rejected_complex_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Run protein complex enrichment over foreground and background protein sets."""
    try:
        foreground = parse_protein_reference_table(
            foreground_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        background = parse_protein_reference_table(
            background_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        complex_memberships = parse_complex_membership_table(
            complex_tsv,
            mapping=ComplexMembershipColumnMapping(
                complex_id=complex_id_column,
                complex_name=complex_name_column,
                source_name=source_name_column,
                source_accession=source_accession_column,
                protein_ref=complex_protein_ref_column,
                gene_symbol=gene_symbol_column,
            ),
        )
        fasta_report = (
            None
            if proteins_fasta is None
            else parse_fasta_document(
                proteins_fasta.read_text(encoding="utf-8"),
                mode=FastaParseMode.STRICT,
            )
        )
        if fasta_report is not None and fasta_report.rejected_records:
            rejected = ", ".join(
                record.source_identifier for record in fasta_report.rejected_records
            )
            raise click.ClickException(
                f"FASTA input contains rejected records under strict mode: {rejected}"
            )
        annotation_report = (
            None
            if annotation_tsv is None
            else parse_protein_annotation_table(
                annotation_tsv,
                mapping=ProteinAnnotationColumnMapping(
                    protein_ref=annotation_protein_ref_column,
                    gene_symbol=annotation_gene_symbol_column,
                    description=annotation_description_column,
                    organism=annotation_organism_column,
                    annotation_identifier=annotation_identifier_column,
                ),
            )
        )
        report = apply_complex_enrichment_multiple_testing(
            build_complex_enrichment_report(
                foreground.accepted_entries,
                background.accepted_entries,
                complex_memberships.accepted_records,
                fasta_records=()
                if fasta_report is None
                else fasta_report.accepted_records,
                custom_annotations=()
                if annotation_report is None
                else annotation_report.accepted_records,
            ),
            policy=ComplexEnrichmentCorrectionPolicy(
                max_adjusted_p_value=max_adjusted_p_value,
                min_enrichment_ratio=min_enrichment_ratio,
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_complex_enrichment_summary_tsv(report),
            encoding="utf-8",
        )
    if complex_tsv_out is not None:
        complex_tsv_out.write_text(
            render_complex_enrichment_entry_tsv(report),
            encoding="utf-8",
        )
    if unresolved_tsv_out is not None:
        unresolved_tsv_out.write_text(
            render_complex_unresolved_member_tsv(report),
            encoding="utf-8",
        )
    if rejected_complex_tsv_out is not None:
        rejected_complex_tsv_out.write_text(
            render_rejected_complex_membership_tsv(complex_memberships),
            encoding="utf-8",
        )

    payload = {
        "foreground": foreground.to_dict(),
        "background": background.to_dict(),
        "complex_memberships": complex_memberships.to_dict(),
        "annotation_table": (
            None if annotation_report is None else annotation_report.to_dict()
        ),
        "fasta_report": None if fasta_report is None else fasta_report.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "complex_tsv": None if complex_tsv_out is None else str(complex_tsv_out),
            "unresolved_tsv": (
                None if unresolved_tsv_out is None else str(unresolved_tsv_out)
            ),
            "rejected_complex_tsv": (
                None
                if rejected_complex_tsv_out is None
                else str(rejected_complex_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@isotope_labeling_group.command("silac-quantify")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--sample-id-column", default="sample_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--protein-refs-column", default="protein_refs", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--label-column", default="label", show_default=True)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--labels", default="light,heavy", show_default=True)
@click.option(
    "--reference-label",
    type=_silac_label_choice(),
    default=SilacLabel.LIGHT.value,
    show_default=True,
)
@click.option("--collapse-charge-states", is_flag=True)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--peptide-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--protein-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def silac_quantify_command(
    input_tsv: Path,
    sample_id_column: str,
    peptide_column: str,
    protein_refs_column: str,
    charge_column: str,
    label_column: str,
    intensity_column: str,
    feature_id_column: str,
    protein_separator: str,
    labels: str,
    reference_label: str,
    collapse_charge_states: bool,
    summary_tsv_out: Path | None,
    peptide_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Quantify SILAC pair or triplet evidence from labeled feature tables."""
    try:
        import_report = parse_silac_feature_table(
            input_tsv,
            mapping=SilacColumnMapping(
                sample_id=sample_id_column,
                peptide=peptide_column,
                protein_refs=protein_refs_column,
                charge=charge_column,
                label=label_column,
                intensity=intensity_column,
                feature_id=feature_id_column,
                protein_separator=protein_separator,
            ),
        )
        report = build_silac_ratio_report(
            import_report,
            policy=SilacQuantificationPolicy(
                expected_labels=_parse_silac_label_spec(labels),
                reference_label=SilacLabel(reference_label),
                separate_charge_states=not collapse_charge_states,
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_silac_ratio_summary_tsv(report, summary_tsv_out)
    if peptide_tsv_out is not None:
        export_silac_peptide_ratio_tsv(report, peptide_tsv_out)
    if protein_tsv_out is not None:
        export_silac_protein_ratio_tsv(report, protein_tsv_out)

    payload = {
        "import_report": import_report.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "peptide_tsv": None if peptide_tsv_out is None else str(peptide_tsv_out),
            "protein_tsv": None if protein_tsv_out is None else str(protein_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


@isotope_labeling_group.command("silac-differential")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--sample-id-column", default="sample_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--protein-refs-column", default="protein_refs", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--label-column", default="label", show_default=True)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--labels", default="light,heavy", show_default=True)
@click.option(
    "--reference-label",
    type=_silac_label_choice(),
    default=SilacLabel.LIGHT.value,
    show_default=True,
)
@click.option("--collapse-charge-states", is_flag=True)
@click.option(
    "--normalization-method",
    type=_label_based_differential_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option("--batch-field", default="batch", show_default=True)
@click.option("--covariate-field", "covariate_fields", multiple=True)
@click.option("--pairing-field", default=None)
@click.option(
    "--raw-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--normalized-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--results-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--balance-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--volcano-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--volcano-json-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--volcano-svg-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--volcano-html-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--volcano-adjusted-p-value-threshold",
    type=float,
    default=0.1,
    show_default=True,
)
@click.option(
    "--volcano-absolute-log2-fold-change-threshold",
    type=float,
    default=1.0,
    show_default=True,
)
@click.option(
    "--volcano-top-label-count",
    type=int,
    default=10,
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def silac_differential_command(
    input_tsv: Path,
    design_path: Path,
    sample_id_column: str,
    peptide_column: str,
    protein_refs_column: str,
    charge_column: str,
    label_column: str,
    intensity_column: str,
    feature_id_column: str,
    protein_separator: str,
    labels: str,
    reference_label: str,
    collapse_charge_states: bool,
    normalization_method: str,
    condition_a: str | None,
    condition_b: str | None,
    batch_field: str,
    covariate_fields: tuple[str, ...],
    pairing_field: str | None,
    raw_matrix_tsv_out: Path | None,
    normalized_matrix_tsv_out: Path | None,
    results_tsv_out: Path | None,
    balance_tsv_out: Path | None,
    volcano_tsv_out: Path | None,
    volcano_json_out: Path | None,
    volcano_svg_out: Path | None,
    volcano_html_out: Path | None,
    volcano_adjusted_p_value_threshold: float,
    volcano_absolute_log2_fold_change_threshold: float,
    volcano_top_label_count: int,
    out_path: Path | None,
) -> None:
    """Run differential analysis over governed SILAC protein ratios."""
    try:
        design_report = parse_experimental_design_table(design_path)
        if design_report.rejected_rows:
            raise click.ClickException("design table contains rejected rows")
        report = build_silac_differential_analysis_report(
            input_tsv,
            tuple(design_report.accepted_entries),
            mapping=SilacColumnMapping(
                sample_id=sample_id_column,
                peptide=peptide_column,
                protein_refs=protein_refs_column,
                charge=charge_column,
                label=label_column,
                intensity=intensity_column,
                feature_id=feature_id_column,
                protein_separator=protein_separator,
            ),
            quantification_policy=SilacQuantificationPolicy(
                expected_labels=_parse_silac_label_spec(labels),
                reference_label=SilacLabel(reference_label),
                separate_charge_states=not collapse_charge_states,
            ),
            normalization_method=NormalizationMethod(normalization_method),
            condition_a=condition_a,
            condition_b=condition_b,
            batch_field=batch_field,
            covariate_fields=tuple(dict.fromkeys(covariate_fields)),
            pairing_field=pairing_field,
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    volcano_plot = report.volcano_plot
    volcano_review = None
    if (
        volcano_tsv_out is not None
        or volcano_json_out is not None
        or volcano_svg_out is not None
        or volcano_html_out is not None
    ):
        if report.differential_abundance_report is None:
            raise click.ClickException(
                "volcano export requires a resolvable contrast or exactly two conditions"
            )
        volcano_plot = build_label_based_differential_volcano_plot(
            report.differential_abundance_report,
            protein_refs_by_entity={
                row.entity_id: row.protein_refs for row in report.normalized_matrix.rows
            },
            adjusted_p_value_threshold=volcano_adjusted_p_value_threshold,
            absolute_log2_fold_change_threshold=(
                volcano_absolute_log2_fold_change_threshold
            ),
        )
        volcano_review = build_label_based_volcano_review(
            volcano_plot,
            policy=_build_volcano_review_policy(
                adjusted_p_value_threshold=volcano_adjusted_p_value_threshold,
                absolute_log2_fold_change_threshold=(
                    volcano_absolute_log2_fold_change_threshold
                ),
                top_label_count=volcano_top_label_count,
            ),
        )

    if raw_matrix_tsv_out is not None:
        export_label_based_differential_matrix_tsv(
            report.input_report,
            raw_matrix_tsv_out,
        )
    if normalized_matrix_tsv_out is not None:
        export_label_based_differential_matrix_tsv(
            report.normalized_matrix,
            normalized_matrix_tsv_out,
        )
    if results_tsv_out is not None:
        export_label_based_differential_results_tsv(report, results_tsv_out)
    if balance_tsv_out is not None:
        export_label_based_normalization_balance_plot_tsv(
            report.normalization_balance_plot,
            balance_tsv_out,
        )
    if volcano_tsv_out is not None and volcano_plot is not None:
        export_label_based_differential_volcano_plot_tsv(
            volcano_plot,
            volcano_tsv_out,
        )
    if volcano_review is not None:
        _export_volcano_review_assets(
            review_report=volcano_review,
            json_out=volcano_json_out,
            svg_out=volcano_svg_out,
            html_out=volcano_html_out,
        )

    payload = {
        "report": report.to_dict(),
        "volcano_review": None if volcano_review is None else volcano_review.to_dict(),
        "outputs": {
            "raw_matrix_tsv": (
                None if raw_matrix_tsv_out is None else str(raw_matrix_tsv_out)
            ),
            "normalized_matrix_tsv": (
                None
                if normalized_matrix_tsv_out is None
                else str(normalized_matrix_tsv_out)
            ),
            "results_tsv": (
                None if results_tsv_out is None else str(results_tsv_out)
            ),
            "balance_tsv": (
                None if balance_tsv_out is None else str(balance_tsv_out)
            ),
            "volcano_tsv": (
                None
                if volcano_tsv_out is None or volcano_plot is None
                else str(volcano_tsv_out)
            ),
            "volcano_json": (
                None if volcano_json_out is None else str(volcano_json_out)
            ),
            "volcano_svg": None if volcano_svg_out is None else str(volcano_svg_out),
            "volcano_html": (
                None if volcano_html_out is None else str(volcano_html_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@isotope_labeling_group.command("silac-report")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--sample-id-column", default="sample_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--protein-refs-column", default="protein_refs", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--label-column", default="label", show_default=True)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--labels", default="light,heavy", show_default=True)
@click.option(
    "--reference-label",
    type=_silac_label_choice(),
    default=SilacLabel.LIGHT.value,
    show_default=True,
)
@click.option("--collapse-charge-states", is_flag=True)
@click.option(
    "--differential-normalization-method",
    type=_label_based_differential_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option("--batch-field", default="batch", show_default=True)
@click.option("--covariate-field", "covariate_fields", multiple=True)
@click.option("--pairing-field", default=None)
@click.option(
    "--output-dir",
    required=True,
    type=click.Path(path_type=Path, file_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def silac_report_command(
    input_tsv: Path,
    design_path: Path,
    sample_id_column: str,
    peptide_column: str,
    protein_refs_column: str,
    charge_column: str,
    label_column: str,
    intensity_column: str,
    feature_id_column: str,
    protein_separator: str,
    labels: str,
    reference_label: str,
    collapse_charge_states: bool,
    differential_normalization_method: str,
    condition_a: str | None,
    condition_b: str | None,
    batch_field: str,
    covariate_fields: tuple[str, ...],
    pairing_field: str | None,
    output_dir: Path,
    out_path: Path | None,
) -> None:
    """Build a governed SILAC report directory with ratios, QC, and differential results."""
    result = _run_orchestrated_workflow(
        SilacWorkflowConfig(
            input_tsv_path=input_tsv,
            design_tsv_path=design_path,
            mapping=SilacColumnMapping(
                sample_id=sample_id_column,
                peptide=peptide_column,
                protein_refs=protein_refs_column,
                charge=charge_column,
                label=label_column,
                intensity=intensity_column,
                feature_id=feature_id_column,
                protein_separator=protein_separator,
            ),
            quantification_policy=SilacQuantificationPolicy(
                expected_labels=_parse_silac_label_spec(labels),
                reference_label=SilacLabel(reference_label),
                separate_charge_states=not collapse_charge_states,
            ),
            differential_normalization_method=NormalizationMethod(
                differential_normalization_method
            ),
            condition_a=condition_a,
            condition_b=condition_b,
            batch_field=batch_field,
            covariate_fields=tuple(dict.fromkeys(covariate_fields)),
            pairing_field=pairing_field,
            output_dir=output_dir,
        )
    )
    report = result.report
    manifest = result.export_manifest
    if manifest is None:
        raise click.ClickException("workflow export manifest was not produced")

    _emit_json(
        {
            "report": report.to_dict(),
            "export_manifest": manifest.to_dict(),
            "outputs": result.outputs,
        },
        out_path=out_path,
    )


@isotope_labeling_group.command("silac-validate")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--sample-id-column", default="sample_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--protein-refs-column", default="protein_refs", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--label-column", default="label", show_default=True)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--labels", default="light,heavy", show_default=True)
@click.option("--collapse-charge-states", is_flag=True)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--label-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--distribution-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option("--weak-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def silac_validate_command(
    input_tsv: Path,
    sample_id_column: str,
    peptide_column: str,
    protein_refs_column: str,
    charge_column: str,
    label_column: str,
    intensity_column: str,
    feature_id_column: str,
    protein_separator: str,
    labels: str,
    collapse_charge_states: bool,
    summary_tsv_out: Path | None,
    label_tsv_out: Path | None,
    distribution_tsv_out: Path | None,
    weak_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Validate expected SILAC labels and weak labeling evidence."""
    try:
        import_report = parse_silac_feature_table(
            input_tsv,
            mapping=SilacColumnMapping(
                sample_id=sample_id_column,
                peptide=peptide_column,
                protein_refs=protein_refs_column,
                charge=charge_column,
                label=label_column,
                intensity=intensity_column,
                feature_id=feature_id_column,
                protein_separator=protein_separator,
            ),
        )
        report = build_silac_validation_report(
            import_report,
            policy=SilacValidationPolicy(
                expected_labels=_parse_silac_label_spec(labels),
                separate_charge_states=not collapse_charge_states,
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_silac_validation_summary_tsv(report, summary_tsv_out)
    if label_tsv_out is not None:
        export_silac_validation_label_tsv(report, label_tsv_out)
    if distribution_tsv_out is not None:
        export_silac_validation_distribution_tsv(report, distribution_tsv_out)
    if weak_tsv_out is not None:
        export_silac_validation_weak_tsv(report, weak_tsv_out)

    payload = {
        "import_report": import_report.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "label_tsv": None if label_tsv_out is None else str(label_tsv_out),
            "distribution_tsv": (
                None if distribution_tsv_out is None else str(distribution_tsv_out)
            ),
            "weak_tsv": None if weak_tsv_out is None else str(weak_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


@isotope_labeling_group.command("tmt-validate")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--source-kind",
    type=_tmt_source_kind_choice(),
    default=TmtSearchResultSourceKind.MAXQUANT.value,
    show_default=True,
)
@click.option("--row-id-column", default=None)
@click.option("--peptide-column", default=None)
@click.option("--protein-refs-column", default=None)
@click.option("--multiplex-group-column", default=None)
@click.option("--default-multiplex-group", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--channel-column", "channel_columns", multiple=True)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--channel-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--distribution-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option("--weak-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def tmt_validate_command(
    input_tsv: Path,
    design_path: Path,
    source_kind: str,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    summary_tsv_out: Path | None,
    channel_tsv_out: Path | None,
    distribution_tsv_out: Path | None,
    weak_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Validate expected TMT channels and weak reporter evidence."""
    try:
        explicit_channels = _parse_tmt_channel_column_specs(channel_columns)
        import_report = parse_tmt_reporter_table(
            input_tsv,
            source_kind=TmtSearchResultSourceKind(source_kind),
            mapping=TmtReporterColumnMapping(
                source_row_id=row_id_column,
                peptide=peptide_column,
                protein_refs=protein_refs_column,
                multiplex_group=multiplex_group_column,
                default_multiplex_group=default_multiplex_group,
                protein_separator=protein_separator,
            ),
            channel_columns=explicit_channels,
        )
        design_report = parse_experimental_design_table(design_path)
        if design_report.rejected_rows:
            raise click.ClickException("design table contains rejected rows")
        feature_bundle = build_tmt_reporter_feature_bundle(
            import_report,
            design_entries=tuple(design_report.accepted_entries),
        )
        report = build_tmt_validation_report(
            feature_bundle,
            policy=TmtValidationPolicy(),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_tmt_validation_summary_tsv(report, summary_tsv_out)
    if channel_tsv_out is not None:
        export_tmt_validation_channel_tsv(report, channel_tsv_out)
    if distribution_tsv_out is not None:
        export_tmt_validation_distribution_tsv(report, distribution_tsv_out)
    if weak_tsv_out is not None:
        export_tmt_validation_weak_tsv(report, weak_tsv_out)

    payload = {
        "source_kind": import_report.source_kind.value,
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "channel_tsv": None if channel_tsv_out is None else str(channel_tsv_out),
            "distribution_tsv": (
                None if distribution_tsv_out is None else str(distribution_tsv_out)
            ),
            "weak_tsv": None if weak_tsv_out is None else str(weak_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


@multiplex_group.command("validate-metadata")
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--channel-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--duplicate-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option(
    "--missing-condition-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def multiplex_validate_metadata_command(
    design_path: Path,
    summary_tsv_out: Path | None,
    channel_tsv_out: Path | None,
    duplicate_tsv_out: Path | None,
    missing_condition_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Validate multiplex sample metadata mappings from the design table."""
    try:
        design_report = parse_experimental_design_table(design_path)
        if design_report.rejected_rows:
            raise click.ClickException("design table contains rejected rows")
        report = build_multiplex_metadata_validation_report(design_report)
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_multiplex_metadata_summary_tsv(report, summary_tsv_out)
    if channel_tsv_out is not None:
        export_multiplex_channel_assignment_tsv(report, channel_tsv_out)
    if duplicate_tsv_out is not None:
        export_multiplex_duplicate_assignment_tsv(report, duplicate_tsv_out)
    if missing_condition_tsv_out is not None:
        export_multiplex_missing_condition_tsv(report, missing_condition_tsv_out)

    payload = {
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "channel_tsv": None if channel_tsv_out is None else str(channel_tsv_out),
            "duplicate_tsv": (
                None if duplicate_tsv_out is None else str(duplicate_tsv_out)
            ),
            "missing_condition_tsv": (
                None
                if missing_condition_tsv_out is None
                else str(missing_condition_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@multiplex_group.command("tmt-reporter-matrix")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--source-kind",
    type=_tmt_source_kind_choice(),
    default=TmtSearchResultSourceKind.MAXQUANT.value,
    show_default=True,
)
@click.option("--row-id-column", default=None)
@click.option("--peptide-column", default=None)
@click.option("--protein-refs-column", default=None)
@click.option("--multiplex-group-column", default=None)
@click.option("--default-multiplex-group", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--channel-column", "channel_columns", multiple=True)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--channel-mapping-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--channel-totals-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--peptide-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--protein-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def tmt_reporter_matrix_command(
    input_tsv: Path,
    design_path: Path,
    source_kind: str,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    summary_tsv_out: Path | None,
    channel_mapping_tsv_out: Path | None,
    channel_totals_tsv_out: Path | None,
    peptide_matrix_tsv_out: Path | None,
    protein_matrix_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Import TMT reporter-ion search results and build sample-channel matrices."""
    try:
        explicit_channels = _parse_tmt_channel_column_specs(channel_columns)
        import_report = parse_tmt_reporter_table(
            input_tsv,
            source_kind=TmtSearchResultSourceKind(source_kind),
            mapping=TmtReporterColumnMapping(
                source_row_id=row_id_column,
                peptide=peptide_column,
                protein_refs=protein_refs_column,
                multiplex_group=multiplex_group_column,
                default_multiplex_group=default_multiplex_group,
                protein_separator=protein_separator,
            ),
            channel_columns=explicit_channels,
        )
        design_report = parse_experimental_design_table(design_path)
        if design_report.rejected_rows:
            raise click.ClickException("design table contains rejected rows")
        feature_bundle = build_tmt_reporter_feature_bundle(
            import_report,
            design_entries=tuple(design_report.accepted_entries),
        )
        report = build_tmt_reporter_matrix_report(feature_bundle)
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_tmt_report_summary_tsv(report, summary_tsv_out)
    if channel_mapping_tsv_out is not None:
        export_tmt_channel_mapping_tsv(report, channel_mapping_tsv_out)
    if channel_totals_tsv_out is not None:
        export_tmt_channel_totals_tsv(report, channel_totals_tsv_out)
    if peptide_matrix_tsv_out is not None:
        export_tmt_peptide_matrix_tsv(report, peptide_matrix_tsv_out)
    if protein_matrix_tsv_out is not None:
        export_tmt_protein_matrix_tsv(report, protein_matrix_tsv_out)

    payload = {
        "source_kind": import_report.source_kind.value,
        "source_report": import_report.to_dict(),
        "feature_bundle": feature_bundle.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "channel_mapping_tsv": (
                None
                if channel_mapping_tsv_out is None
                else str(channel_mapping_tsv_out)
            ),
            "channel_totals_tsv": (
                None
                if channel_totals_tsv_out is None
                else str(channel_totals_tsv_out)
            ),
            "peptide_matrix_tsv": (
                None if peptide_matrix_tsv_out is None else str(peptide_matrix_tsv_out)
            ),
            "protein_matrix_tsv": (
                None if protein_matrix_tsv_out is None else str(protein_matrix_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@multiplex_group.command("tmt-interference")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--source-kind",
    type=_tmt_source_kind_choice(),
    default=TmtSearchResultSourceKind.MAXQUANT.value,
    show_default=True,
)
@click.option(
    "--interference-threshold",
    default=0.3,
    show_default=True,
    type=float,
)
@click.option("--row-id-column", default=None)
@click.option("--peptide-column", default=None)
@click.option("--protein-refs-column", default=None)
@click.option("--multiplex-group-column", default=None)
@click.option("--default-multiplex-group", default=None)
@click.option("--interference-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--channel-column", "channel_columns", multiple=True)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--observation-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--filtered-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--channel-summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def tmt_interference_command(
    input_tsv: Path,
    design_path: Path,
    source_kind: str,
    interference_threshold: float,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    interference_column: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    summary_tsv_out: Path | None,
    observation_tsv_out: Path | None,
    filtered_tsv_out: Path | None,
    channel_summary_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Review TMT reporter-ion isolation interference and export filter ledgers."""
    try:
        explicit_channels = _parse_tmt_channel_column_specs(channel_columns)
        import_report = parse_tmt_reporter_table(
            input_tsv,
            source_kind=TmtSearchResultSourceKind(source_kind),
            mapping=TmtReporterColumnMapping(
                source_row_id=row_id_column,
                peptide=peptide_column,
                protein_refs=protein_refs_column,
                multiplex_group=multiplex_group_column,
                default_multiplex_group=default_multiplex_group,
                isolation_interference=interference_column,
                protein_separator=protein_separator,
            ),
            channel_columns=explicit_channels,
        )
        design_report = parse_experimental_design_table(design_path)
        if design_report.rejected_rows:
            raise click.ClickException("design table contains rejected rows")
        report = build_tmt_interference_report(
            import_report,
            design_entries=tuple(design_report.accepted_entries),
            policy=TmtInterferencePolicy(
                interference_fraction_threshold=interference_threshold
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_tmt_interference_summary_tsv(report, summary_tsv_out)
    if observation_tsv_out is not None:
        export_tmt_interference_observation_tsv(report, observation_tsv_out)
    if filtered_tsv_out is not None:
        export_tmt_filtered_interference_tsv(report, filtered_tsv_out)
    if channel_summary_tsv_out is not None:
        export_tmt_interference_channel_summary_tsv(report, channel_summary_tsv_out)

    payload = {
        "source_kind": import_report.source_kind.value,
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "observation_tsv": (
                None if observation_tsv_out is None else str(observation_tsv_out)
            ),
            "filtered_tsv": (
                None if filtered_tsv_out is None else str(filtered_tsv_out)
            ),
            "channel_summary_tsv": (
                None
                if channel_summary_tsv_out is None
                else str(channel_summary_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@multiplex_group.command("tmt-normalize")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--source-kind",
    type=_tmt_source_kind_choice(),
    default=TmtSearchResultSourceKind.MAXQUANT.value,
    show_default=True,
)
@click.option(
    "--method",
    type=_tmt_normalization_method_choice(),
    default=TmtNormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--row-id-column", default=None)
@click.option("--peptide-column", default=None)
@click.option("--protein-refs-column", default=None)
@click.option("--multiplex-group-column", default=None)
@click.option("--default-multiplex-group", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--channel-column", "channel_columns", multiple=True)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--transform-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--distribution-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--peptide-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--protein-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def tmt_normalize_command(
    input_tsv: Path,
    design_path: Path,
    source_kind: str,
    method: str,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    summary_tsv_out: Path | None,
    transform_tsv_out: Path | None,
    distribution_tsv_out: Path | None,
    peptide_matrix_tsv_out: Path | None,
    protein_matrix_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Normalize TMT reporter-channel evidence and export before/after review ledgers."""
    try:
        explicit_channels = _parse_tmt_channel_column_specs(channel_columns)
        import_report = parse_tmt_reporter_table(
            input_tsv,
            source_kind=TmtSearchResultSourceKind(source_kind),
            mapping=TmtReporterColumnMapping(
                source_row_id=row_id_column,
                peptide=peptide_column,
                protein_refs=protein_refs_column,
                multiplex_group=multiplex_group_column,
                default_multiplex_group=default_multiplex_group,
                protein_separator=protein_separator,
            ),
            channel_columns=explicit_channels,
        )
        design_report = parse_experimental_design_table(design_path)
        if design_report.rejected_rows:
            raise click.ClickException("design table contains rejected rows")
        feature_bundle = build_tmt_reporter_feature_bundle(
            import_report,
            design_entries=tuple(design_report.accepted_entries),
        )
        report = build_tmt_normalization_report(
            feature_bundle,
            policy=TmtNormalizationPolicy(
                method=TmtNormalizationMethod(method),
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_tmt_normalization_summary_tsv(report, summary_tsv_out)
    if transform_tsv_out is not None:
        export_tmt_normalization_transform_tsv(report, transform_tsv_out)
    if distribution_tsv_out is not None:
        export_tmt_channel_distribution_tsv(report, distribution_tsv_out)
    if peptide_matrix_tsv_out is not None:
        export_tmt_normalized_peptide_matrix_tsv(report, peptide_matrix_tsv_out)
    if protein_matrix_tsv_out is not None:
        export_tmt_normalized_protein_matrix_tsv(report, protein_matrix_tsv_out)

    payload = {
        "source_kind": import_report.source_kind.value,
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "transform_tsv": (
                None if transform_tsv_out is None else str(transform_tsv_out)
            ),
            "distribution_tsv": (
                None
                if distribution_tsv_out is None
                else str(distribution_tsv_out)
            ),
            "peptide_matrix_tsv": (
                None if peptide_matrix_tsv_out is None else str(peptide_matrix_tsv_out)
            ),
            "protein_matrix_tsv": (
                None if protein_matrix_tsv_out is None else str(protein_matrix_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@multiplex_group.command("tmt-ratios")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--control-channel",
    required=True,
)
@click.option(
    "--source-kind",
    type=_tmt_source_kind_choice(),
    default=TmtSearchResultSourceKind.MAXQUANT.value,
    show_default=True,
)
@click.option(
    "--normalization-method",
    type=_tmt_ratio_normalization_choice(),
    default="none",
    show_default=True,
)
@click.option("--row-id-column", default=None)
@click.option("--peptide-column", default=None)
@click.option("--protein-refs-column", default=None)
@click.option("--multiplex-group-column", default=None)
@click.option("--default-multiplex-group", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--channel-column", "channel_columns", multiple=True)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--peptide-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--protein-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def tmt_ratio_command(
    input_tsv: Path,
    design_path: Path,
    control_channel: str,
    source_kind: str,
    normalization_method: str,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    summary_tsv_out: Path | None,
    peptide_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Compute governed TMT sample/control ratios across multiplex channels."""
    try:
        explicit_channels = _parse_tmt_channel_column_specs(channel_columns)
        import_report = parse_tmt_reporter_table(
            input_tsv,
            source_kind=TmtSearchResultSourceKind(source_kind),
            mapping=TmtReporterColumnMapping(
                source_row_id=row_id_column,
                peptide=peptide_column,
                protein_refs=protein_refs_column,
                multiplex_group=multiplex_group_column,
                default_multiplex_group=default_multiplex_group,
                protein_separator=protein_separator,
            ),
            channel_columns=explicit_channels,
        )
        design_report = parse_experimental_design_table(design_path)
        if design_report.rejected_rows:
            raise click.ClickException("design table contains rejected rows")
        feature_bundle = build_tmt_reporter_feature_bundle(
            import_report,
            design_entries=tuple(design_report.accepted_entries),
        )
        normalization_policy = (
            None
            if normalization_method == "none"
            else TmtNormalizationPolicy(
                method=TmtNormalizationMethod(normalization_method),
            )
        )
        report = build_tmt_ratio_report(
            feature_bundle,
            control_channel=control_channel,
            normalization_policy=normalization_policy,
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_tmt_ratio_summary_tsv(report, summary_tsv_out)
    if peptide_tsv_out is not None:
        export_tmt_peptide_ratio_tsv(report, peptide_tsv_out)
    if protein_tsv_out is not None:
        export_tmt_protein_ratio_tsv(report, protein_tsv_out)

    payload = {
        "source_kind": import_report.source_kind.value,
        "control_channel": control_channel,
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "peptide_tsv": None if peptide_tsv_out is None else str(peptide_tsv_out),
            "protein_tsv": None if protein_tsv_out is None else str(protein_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


@multiplex_group.command("tmt-integrate-plexes")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--source-kind",
    type=_tmt_source_kind_choice(),
    default=TmtSearchResultSourceKind.MAXQUANT.value,
    show_default=True,
)
@click.option(
    "--plex-effect-ratio-threshold",
    default=1.25,
    show_default=True,
    type=float,
)
@click.option("--row-id-column", default=None)
@click.option("--peptide-column", default=None)
@click.option("--protein-refs-column", default=None)
@click.option("--multiplex-group-column", default=None)
@click.option("--default-multiplex-group", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--channel-column", "channel_columns", multiple=True)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--alignment-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--plex-effect-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--protein-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def tmt_integrate_plexes_command(
    input_tsv: Path,
    design_path: Path,
    source_kind: str,
    plex_effect_ratio_threshold: float,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    summary_tsv_out: Path | None,
    alignment_tsv_out: Path | None,
    plex_effect_tsv_out: Path | None,
    protein_matrix_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Integrate multiple TMT plexes through bridge-normalized protein matrices."""
    try:
        explicit_channels = _parse_tmt_channel_column_specs(channel_columns)
        import_report = parse_tmt_reporter_table(
            input_tsv,
            source_kind=TmtSearchResultSourceKind(source_kind),
            mapping=TmtReporterColumnMapping(
                source_row_id=row_id_column,
                peptide=peptide_column,
                protein_refs=protein_refs_column,
                multiplex_group=multiplex_group_column,
                default_multiplex_group=default_multiplex_group,
                protein_separator=protein_separator,
            ),
            channel_columns=explicit_channels,
        )
        design_report = parse_experimental_design_table(design_path)
        if design_report.rejected_rows:
            raise click.ClickException("design table contains rejected rows")
        feature_bundle = build_tmt_reporter_feature_bundle(
            import_report,
            design_entries=tuple(design_report.accepted_entries),
        )
        report = build_tmt_plex_integration_report(
            feature_bundle,
            policy=TmtPlexIntegrationPolicy(
                plex_effect_ratio_threshold=plex_effect_ratio_threshold,
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_tmt_plex_integration_summary_tsv(report, summary_tsv_out)
    if alignment_tsv_out is not None:
        export_tmt_plex_alignment_tsv(report, alignment_tsv_out)
    if plex_effect_tsv_out is not None:
        export_tmt_plex_effect_tsv(report, plex_effect_tsv_out)
    if protein_matrix_tsv_out is not None:
        export_tmt_integrated_protein_matrix_tsv(report, protein_matrix_tsv_out)

    payload = {
        "source_kind": import_report.source_kind.value,
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "alignment_tsv": (
                None if alignment_tsv_out is None else str(alignment_tsv_out)
            ),
            "plex_effect_tsv": (
                None if plex_effect_tsv_out is None else str(plex_effect_tsv_out)
            ),
            "protein_matrix_tsv": (
                None
                if protein_matrix_tsv_out is None
                else str(protein_matrix_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@multiplex_group.command("tmt-differential")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--source-kind",
    type=_tmt_source_kind_choice(),
    default=TmtSearchResultSourceKind.MAXQUANT.value,
    show_default=True,
)
@click.option(
    "--normalization-method",
    type=_label_based_differential_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option("--batch-field", default="batch", show_default=True)
@click.option("--covariate-field", "covariate_fields", multiple=True)
@click.option("--pairing-field", default=None)
@click.option("--row-id-column", default=None)
@click.option("--peptide-column", default=None)
@click.option("--protein-refs-column", default=None)
@click.option("--multiplex-group-column", default=None)
@click.option("--default-multiplex-group", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--channel-column", "channel_columns", multiple=True)
@click.option(
    "--raw-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--normalized-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--results-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--balance-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--volcano-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--volcano-json-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--volcano-svg-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--volcano-html-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--volcano-adjusted-p-value-threshold",
    type=float,
    default=0.1,
    show_default=True,
)
@click.option(
    "--volcano-absolute-log2-fold-change-threshold",
    type=float,
    default=1.0,
    show_default=True,
)
@click.option(
    "--volcano-top-label-count",
    type=int,
    default=10,
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def tmt_differential_command(
    input_tsv: Path,
    design_path: Path,
    source_kind: str,
    normalization_method: str,
    condition_a: str | None,
    condition_b: str | None,
    batch_field: str,
    covariate_fields: tuple[str, ...],
    pairing_field: str | None,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    raw_matrix_tsv_out: Path | None,
    normalized_matrix_tsv_out: Path | None,
    results_tsv_out: Path | None,
    balance_tsv_out: Path | None,
    volcano_tsv_out: Path | None,
    volcano_json_out: Path | None,
    volcano_svg_out: Path | None,
    volcano_html_out: Path | None,
    volcano_adjusted_p_value_threshold: float,
    volcano_absolute_log2_fold_change_threshold: float,
    volcano_top_label_count: int,
    out_path: Path | None,
) -> None:
    """Run differential analysis over governed TMT protein matrices."""
    try:
        explicit_channels = _parse_tmt_channel_column_specs(channel_columns)
        design_report = parse_experimental_design_table(design_path)
        if design_report.rejected_rows:
            raise click.ClickException("design table contains rejected rows")
        report = build_tmt_differential_analysis_report(
            input_tsv,
            tuple(design_report.accepted_entries),
            source_kind=TmtSearchResultSourceKind(source_kind),
            mapping=TmtReporterColumnMapping(
                source_row_id=row_id_column,
                peptide=peptide_column,
                protein_refs=protein_refs_column,
                multiplex_group=multiplex_group_column,
                default_multiplex_group=default_multiplex_group,
                protein_separator=protein_separator,
            ),
            channel_columns=explicit_channels,
            normalization_method=NormalizationMethod(normalization_method),
            condition_a=condition_a,
            condition_b=condition_b,
            batch_field=batch_field,
            covariate_fields=tuple(dict.fromkeys(covariate_fields)),
            pairing_field=pairing_field,
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    volcano_plot = report.volcano_plot
    volcano_review = None
    if (
        volcano_tsv_out is not None
        or volcano_json_out is not None
        or volcano_svg_out is not None
        or volcano_html_out is not None
    ):
        if report.differential_abundance_report is None:
            raise click.ClickException(
                "volcano export requires a resolvable contrast or exactly two conditions"
            )
        volcano_plot = build_label_based_differential_volcano_plot(
            report.differential_abundance_report,
            protein_refs_by_entity={
                row.entity_id: row.protein_refs for row in report.normalized_matrix.rows
            },
            adjusted_p_value_threshold=volcano_adjusted_p_value_threshold,
            absolute_log2_fold_change_threshold=(
                volcano_absolute_log2_fold_change_threshold
            ),
        )
        volcano_review = build_label_based_volcano_review(
            volcano_plot,
            policy=_build_volcano_review_policy(
                adjusted_p_value_threshold=volcano_adjusted_p_value_threshold,
                absolute_log2_fold_change_threshold=(
                    volcano_absolute_log2_fold_change_threshold
                ),
                top_label_count=volcano_top_label_count,
            ),
        )

    if raw_matrix_tsv_out is not None:
        export_label_based_differential_matrix_tsv(
            report.input_report,
            raw_matrix_tsv_out,
        )
    if normalized_matrix_tsv_out is not None:
        export_label_based_differential_matrix_tsv(
            report.normalized_matrix,
            normalized_matrix_tsv_out,
        )
    if results_tsv_out is not None:
        export_label_based_differential_results_tsv(report, results_tsv_out)
    if balance_tsv_out is not None:
        export_label_based_normalization_balance_plot_tsv(
            report.normalization_balance_plot,
            balance_tsv_out,
        )
    if volcano_tsv_out is not None and volcano_plot is not None:
        export_label_based_differential_volcano_plot_tsv(
            volcano_plot,
            volcano_tsv_out,
        )
    if volcano_review is not None:
        _export_volcano_review_assets(
            review_report=volcano_review,
            json_out=volcano_json_out,
            svg_out=volcano_svg_out,
            html_out=volcano_html_out,
        )

    payload = {
        "source_kind": source_kind,
        "report": report.to_dict(),
        "volcano_review": None if volcano_review is None else volcano_review.to_dict(),
        "outputs": {
            "raw_matrix_tsv": (
                None if raw_matrix_tsv_out is None else str(raw_matrix_tsv_out)
            ),
            "normalized_matrix_tsv": (
                None
                if normalized_matrix_tsv_out is None
                else str(normalized_matrix_tsv_out)
            ),
            "results_tsv": (
                None if results_tsv_out is None else str(results_tsv_out)
            ),
            "balance_tsv": (
                None if balance_tsv_out is None else str(balance_tsv_out)
            ),
            "volcano_tsv": (
                None
                if volcano_tsv_out is None or volcano_plot is None
                else str(volcano_tsv_out)
            ),
            "volcano_json": (
                None if volcano_json_out is None else str(volcano_json_out)
            ),
            "volcano_svg": None if volcano_svg_out is None else str(volcano_svg_out),
            "volcano_html": (
                None if volcano_html_out is None else str(volcano_html_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


@multiplex_group.command("tmt-report")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--control-channel",
    required=True,
)
@click.option(
    "--source-kind",
    type=_tmt_source_kind_choice(),
    default=TmtSearchResultSourceKind.MAXQUANT.value,
    show_default=True,
)
@click.option(
    "--channel-normalization-method",
    type=_tmt_normalization_method_choice(),
    default=TmtNormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option(
    "--differential-normalization-method",
    type=_label_based_differential_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option("--batch-field", default="batch", show_default=True)
@click.option("--covariate-field", "covariate_fields", multiple=True)
@click.option("--pairing-field", default=None)
@click.option("--row-id-column", default=None)
@click.option("--peptide-column", default=None)
@click.option("--protein-refs-column", default=None)
@click.option("--multiplex-group-column", default=None)
@click.option("--default-multiplex-group", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--channel-column", "channel_columns", multiple=True)
@click.option(
    "--output-dir",
    required=True,
    type=click.Path(path_type=Path, file_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def tmt_report_command(
    input_tsv: Path,
    design_path: Path,
    control_channel: str,
    source_kind: str,
    channel_normalization_method: str,
    differential_normalization_method: str,
    condition_a: str | None,
    condition_b: str | None,
    batch_field: str,
    covariate_fields: tuple[str, ...],
    pairing_field: str | None,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    output_dir: Path,
    out_path: Path | None,
) -> None:
    """Build a governed TMT report directory with channel quality, ratios, and protein changes."""
    result = _run_orchestrated_workflow(
        TmtWorkflowConfig(
            result_tsv_path=input_tsv,
            design_tsv_path=design_path,
            control_channel=control_channel,
            source_kind=TmtSearchResultSourceKind(source_kind),
            mapping=TmtReporterColumnMapping(
                source_row_id=row_id_column,
                peptide=peptide_column,
                protein_refs=protein_refs_column,
                multiplex_group=multiplex_group_column,
                default_multiplex_group=default_multiplex_group,
                protein_separator=protein_separator,
            ),
            channel_columns=_parse_tmt_channel_column_specs(channel_columns),
            channel_normalization_method=TmtNormalizationMethod(
                channel_normalization_method
            ),
            differential_normalization_method=NormalizationMethod(
                differential_normalization_method
            ),
            condition_a=condition_a,
            condition_b=condition_b,
            batch_field=batch_field,
            covariate_fields=tuple(dict.fromkeys(covariate_fields)),
            pairing_field=pairing_field,
            output_dir=output_dir,
        )
    )
    workflow_report = result.report
    workflow_manifest = result.export_manifest
    if workflow_manifest is None:
        raise click.ClickException("workflow export manifest was not produced")

    _emit_json(
        {
            "source_kind": source_kind,
            "control_channel": control_channel,
            "workflow_report": workflow_report.to_dict(),
            "report": workflow_report.report.to_dict(),
            "workflow_export_manifest": workflow_manifest.to_dict(),
            "export_manifest": workflow_manifest.label_based_report_manifest.to_dict(),
            "outputs": result.outputs,
        },
        out_path=out_path,
    )


@qc_group.command("report")
@click.argument(
    "spectra_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "psm_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--sample-id", default=None)
@click.option("--run-id", default=None)
@click.option(
    "--policy",
    "policy_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--html-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--manifest-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--benchmark-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def qc_report_command(
    spectra_path: Path,
    psm_path: Path,
    proteins_fasta: Path,
    design_path: Path | None,
    sample_id: str | None,
    run_id: str | None,
    policy_path: Path | None,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    protein_refs_column: str,
    q_value_column: str | None,
    out_path: Path | None,
    tsv_out: Path | None,
    html_out: Path | None,
    manifest_out: Path | None,
    benchmark_out: Path | None,
) -> None:
    """Build QC summaries, threshold assessments, evidence manifests, and benchmark artifacts."""
    timings: dict[str, tuple[float, int | None]] = {}
    try:
        policy = default_qc_threshold_policy()
        if policy_path is not None:
            try:
                policy = load_qc_threshold_policy(policy_path)
            except Exception as exc:  # noqa: BLE001
                raise ProteomicsOperatorError(
                    ProteomicsOperatorErrorCode.QC_POLICY_INVALID,
                    str(exc),
                ) from exc

        started = time.perf_counter()
        design_entry = _select_design_entry(
            design_path, sample_id=sample_id, spectra_path=spectra_path
        )
        timings["parse_design"] = (
            time.perf_counter() - started,
            0 if design_entry is None else 1,
        )

        started = time.perf_counter()
        fasta_report = parse_fasta_document(
            proteins_fasta.read_text(), mode=FastaParseMode.STRICT
        )
        if fasta_report.rejected_records:
            rejected = ", ".join(
                record.source_identifier for record in fasta_report.rejected_records
            )
            raise ProteomicsOperatorError(
                ProteomicsOperatorErrorCode.INPUT_FASTA_REJECTED,
                f"FASTA input contains rejected records under strict mode: {rejected}",
            )
        protein_sequences = {
            record.canonical_accession: record.residues
            for record in fasta_report.accepted_records
        }
        timings["parse_fasta"] = (
            time.perf_counter() - started,
            len(fasta_report.accepted_records),
        )

        started = time.perf_counter()
        spectrum_report = parse_mgf(spectra_path)
        timings["parse_spectra"] = (
            time.perf_counter() - started,
            len(spectrum_report.accepted_spectra),
        )

        started = time.perf_counter()
        psm_report = parse_psm_tsv(
            psm_path,
            mapping=SearchResultColumnMapping(
                spectrum_id=spectrum_id_column,
                peptide=peptide_column,
                charge=charge_column,
                score=score_column,
                protein_refs=protein_refs_column,
                q_value=q_value_column,
            ),
        )
        timings["parse_psms"] = (
            time.perf_counter() - started,
            len(psm_report.accepted_records),
        )

        started = time.perf_counter()
        run_report = build_lcms_run_qc_report(
            spectrum_report.accepted_spectra,
            psm_report.accepted_records,
            design_entry=design_entry,
            protein_sequences=protein_sequences,
            run_id=run_id,
        )
        run_assessment = build_run_qc_assessment(run_report, policy=policy)
        timings["build_run_qc"] = (
            time.perf_counter() - started,
            len(run_assessment.metric_assessments),
        )

        started = time.perf_counter()
        batch_report = None
        batch_assessment = None
        if design_entry and design_entry.batch:
            batch_report = build_instrument_batch_qc_report((run_report,))
            batch_assessment = build_batch_qc_assessment(batch_report, policy=policy)
        timings["build_batch_qc"] = (
            time.perf_counter() - started,
            0 if batch_assessment is None else len(batch_assessment.metric_assessments),
        )

        benchmark = build_performance_snapshot(run_report.run_id, operations=timings)
        input_files = [
            QcEvidenceInputFile(
                path=str(spectra_path),
                sha256=_file_sha256(spectra_path),
                role="spectra",
            ),
            QcEvidenceInputFile(
                path=str(psm_path),
                sha256=_file_sha256(psm_path),
                role="identifications",
            ),
            QcEvidenceInputFile(
                path=str(proteins_fasta),
                sha256=_file_sha256(proteins_fasta),
                role="proteins",
            ),
        ]
        if design_path is not None:
            input_files.append(
                QcEvidenceInputFile(
                    path=str(design_path),
                    sha256=_file_sha256(design_path),
                    role="design",
                )
            )
        if policy_path is not None:
            input_files.append(
                QcEvidenceInputFile(
                    path=str(policy_path),
                    sha256=_file_sha256(policy_path),
                    role="qc_policy",
                )
            )
        manifest = build_qc_evidence_manifest(
            run_report=run_report,
            run_assessment=run_assessment,
            policy=policy,
            input_files=tuple(input_files),
            batch_report=batch_report,
            batch_assessment=batch_assessment,
            benchmark=benchmark,
        )
    except ProteomicsOperatorError as exc:
        raise click.ClickException(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(
            str(
                ProteomicsOperatorError(
                    ProteomicsOperatorErrorCode.QC_BUILD_FAILED, str(exc)
                )
            )
        ) from exc

    try:
        if tsv_out is not None:
            _write_text_output(
                tsv_out,
                render_qc_assessment_tsv(
                    run_assessment, batch_assessment=batch_assessment
                ),
            )
        if html_out is not None:
            _write_text_output(
                html_out,
                render_qc_assessment_html(
                    run_report,
                    run_assessment,
                    batch_report=batch_report,
                    batch_assessment=batch_assessment,
                ),
            )
        if manifest_out is not None:
            manifest_out.write_text(manifest.to_stable_json() + "\n", encoding="utf-8")
        if benchmark_out is not None:
            benchmark_out.write_text(
                benchmark.to_stable_json() + "\n", encoding="utf-8"
            )
    except OSError as exc:
        raise click.ClickException(
            str(
                ProteomicsOperatorError(
                    ProteomicsOperatorErrorCode.QC_OUTPUT_WRITE_FAILED, str(exc)
                )
            )
        ) from exc

    payload = {
        "run_report": run_report.to_dict(),
        "run_assessment": run_assessment.to_dict(),
        "batch_report": None if batch_report is None else batch_report.to_dict(),
        "batch_assessment": None
        if batch_assessment is None
        else batch_assessment.to_dict(),
        "evidence_manifest": manifest.to_dict(),
        "performance_snapshot": benchmark.to_dict(),
    }
    _emit_json(payload, out_path=out_path)


@cli.group("ptm")
def ptm_group() -> None:
    """Summarize PTM evidence, mapped sites, and occupancy outputs."""


@ptm_group.command("parse-peptide")
@click.argument("modified_peptide")
@click.option("--protein-ref", default=None)
@click.option("--peptide-start-position", type=int, default=None)
@click.option("--sample-id", default=None)
@click.option("--spectrum-id", default=None)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_parse_peptide_command(
    modified_peptide: str,
    protein_ref: str | None,
    peptide_start_position: int | None,
    sample_id: str | None,
    spectrum_id: str | None,
    out_path: Path | None,
) -> None:
    """Parse one PTM peptide into explicit site-local records."""
    try:
        record = parse_ptm_peptide(
            modified_peptide,
            protein_ref=protein_ref,
            peptide_start_position=peptide_start_position,
            sample_id=sample_id,
            spectrum_id=spectrum_id,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    _emit_json(record.to_dict(), out_path=out_path)


@ptm_group.command("parse-peptides")
@click.argument(
    "peptide_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--protein-ref-column", default="protein_ref", show_default=True)
@click.option(
    "--peptide-start-position-column",
    default="peptide_start_position",
    show_default=True,
)
@click.option("--sample-id-column", default="sample_id", show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--record-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--site-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_parse_peptides_command(
    peptide_tsv: Path,
    peptide_column: str,
    protein_ref_column: str | None,
    peptide_start_position_column: str | None,
    sample_id_column: str | None,
    spectrum_id_column: str | None,
    summary_tsv_out: Path | None,
    record_tsv_out: Path | None,
    site_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Parse a PTM peptide table into peptide and site review ledgers."""
    try:
        report = parse_ptm_peptide_tsv(
            peptide_tsv,
            mapping=PtmPeptideColumnMapping(
                peptide=peptide_column,
                protein_ref=protein_ref_column,
                peptide_start_position=peptide_start_position_column,
                sample_id=sample_id_column,
                spectrum_id=spectrum_id_column,
            ),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_ptm_peptide_summary_tsv(report),
            encoding="utf-8",
        )
    if record_tsv_out is not None:
        record_tsv_out.write_text(
            render_ptm_peptide_record_tsv(report),
            encoding="utf-8",
        )
    if site_tsv_out is not None:
        site_tsv_out.write_text(
            render_ptm_peptide_site_tsv(report),
            encoding="utf-8",
        )
    if rejected_tsv_out is not None:
        rejected_tsv_out.write_text(
            render_ptm_peptide_rejected_tsv(report),
            encoding="utf-8",
        )

    _emit_json(report.to_dict(), out_path=out_path)


@ptm_group.command("map-sites")
@click.argument(
    "evidence_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option(
    "--localization-score-column", default="localization_score", show_default=True
)
@click.option(
    "--localization-probability-column",
    default="localization_probability",
    show_default=True,
)
@click.option("--candidate-sites-column", default="candidate_sites", show_default=True)
@click.option("--decoy-label-column", default="decoy_label", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--site-separator", default=";", show_default=True)
@click.option(
    "--mapping-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--exact-mapping-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--ambiguous-mapping-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unmapped-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--candidate-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--site-table-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--ambiguity-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--coverage-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--validation-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_map_sites_command(
    evidence_tsv: Path,
    proteins_fasta: Path,
    sample_column: str,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    protein_refs_column: str,
    q_value_column: str | None,
    localization_score_column: str,
    localization_probability_column: str | None,
    candidate_sites_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
    site_separator: str,
    mapping_tsv_out: Path | None,
    exact_mapping_tsv_out: Path | None,
    ambiguous_mapping_tsv_out: Path | None,
    unmapped_tsv_out: Path | None,
    candidate_tsv_out: Path | None,
    site_table_tsv_out: Path | None,
    ambiguity_tsv_out: Path | None,
    coverage_tsv_out: Path | None,
    validation_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Map localized PTM peptides onto protein coordinates and export site tables."""
    try:
        mapping = PtmLocalizationColumnMapping(
            sample_id=sample_column,
            spectrum_id=spectrum_id_column,
            peptide=peptide_column,
            charge=charge_column,
            score=score_column,
            protein_refs=protein_refs_column,
            q_value=q_value_column,
            localization_score=localization_score_column,
            localization_probability=localization_probability_column,
            candidate_sites=candidate_sites_column,
            decoy_label=decoy_label_column,
            protein_separator=protein_separator,
            site_separator=site_separator,
        )
        evidence = parse_ptm_localization_tsv(evidence_tsv, mapping=mapping)
        fasta_report = parse_fasta_document(
            proteins_fasta.read_text(),
            mode=FastaParseMode.STRICT,
        )
        if fasta_report.rejected_records:
            rejected = ", ".join(
                record.source_identifier for record in fasta_report.rejected_records
            )
            raise click.ClickException(
                f"FASTA input contains rejected records under strict mode: {rejected}"
            )
        protein_sequences = {
            record.canonical_accession: record.residues
            for record in fasta_report.accepted_records
        }
        mapping_report = build_ptm_protein_site_mapping_report(
            evidence.accepted_records,
            protein_sequences=protein_sequences,
        )
        mappings = mapping_report.mappings
        site_table = build_ptm_site_table(mappings)
        localization = build_ptm_localization_scoring_report(
            evidence.accepted_records
        )
        ambiguity_review = build_ptm_ambiguity_review_report(
            site_table,
            localization_scoring_report=localization,
            protein_sequences=protein_sequences,
        )
        coverage = build_ptm_site_coverage_report(mappings)
        validation = validate_ptm_site_coordinates(
            mappings,
            protein_sequences=protein_sequences,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if mapping_tsv_out is not None:
        mapping_tsv_out.write_text(
            render_ptm_protein_site_mapping_tsv(mappings),
            encoding="utf-8",
        )
    if exact_mapping_tsv_out is not None:
        exact_mapping_tsv_out.write_text(
            render_ptm_protein_site_mapping_tsv(mapping_report.exact_mappings),
            encoding="utf-8",
        )
    if ambiguous_mapping_tsv_out is not None:
        ambiguous_mapping_tsv_out.write_text(
            render_ptm_protein_site_mapping_tsv(mapping_report.ambiguous_mappings),
            encoding="utf-8",
        )
    if unmapped_tsv_out is not None:
        unmapped_tsv_out.write_text(
            render_ptm_unmapped_peptide_tsv(mapping_report.unmapped_peptides),
            encoding="utf-8",
        )
    if candidate_tsv_out is not None:
        candidate_tsv_out.write_text(
            render_ptm_evidence_site_candidate_tsv(evidence),
            encoding="utf-8",
        )
    if site_table_tsv_out is not None:
        site_table_tsv_out.write_text(
            render_ptm_site_table_tsv(site_table),
            encoding="utf-8",
        )
    if ambiguity_tsv_out is not None:
        ambiguity_tsv_out.write_text(
            render_ptm_unlocalized_group_review_tsv(ambiguity_review),
            encoding="utf-8",
        )
    if coverage_tsv_out is not None:
        coverage_tsv_out.write_text(
            render_ptm_site_coverage_tsv(coverage),
            encoding="utf-8",
        )
    if validation_tsv_out is not None:
        validation_tsv_out.write_text(
            render_ptm_coordinate_validation_tsv(validation),
            encoding="utf-8",
        )

    _emit_json(
        {
            "accepted_rows": len(evidence.accepted_records),
            "site_candidate_count": sum(
                len(record.site_candidates) for record in evidence.accepted_records
            ),
            "mapping_count": len(mappings),
            "exact_mapping_count": len(mapping_report.exact_mappings),
            "ambiguous_mapping_count": len(mapping_report.ambiguous_mappings),
            "unmapped_peptide_count": len(mapping_report.unmapped_peptides),
            "site_count": len(site_table),
            "ambiguity_count": len(ambiguity_review.unlocalized_groups),
            "ambiguity_review": ambiguity_review.to_dict(),
            "coverage_count": len(coverage),
            "coordinate_validation": validation.to_dict(),
        },
        out_path=out_path,
    )


@ptm_group.command("score-localization")
@click.argument(
    "evidence_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option(
    "--localization-score-column", default="localization_score", show_default=True
)
@click.option(
    "--localization-probability-column",
    default="localization_probability",
    show_default=True,
)
@click.option("--candidate-sites-column", default="candidate_sites", show_default=True)
@click.option("--decoy-label-column", default="decoy_label", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--site-separator", default=";", show_default=True)
@click.option(
    "--fragment-support-json",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--entry-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_score_localization_command(
    evidence_tsv: Path,
    sample_column: str,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    protein_refs_column: str,
    q_value_column: str | None,
    localization_score_column: str,
    localization_probability_column: str | None,
    candidate_sites_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
    site_separator: str,
    fragment_support_json: Path | None,
    summary_tsv_out: Path | None,
    entry_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Score PTM localization confidence and export probability review ledgers."""
    try:
        fragment_ion_support_by_spectrum: dict[str, tuple[str, ...]] | None = None
        if fragment_support_json is not None:
            raw_fragment_support = json.loads(
                fragment_support_json.read_text(encoding="utf-8")
            )
            if not isinstance(raw_fragment_support, dict):
                raise ValueError("fragment support JSON must be an object keyed by spectrum id")
            fragment_ion_support_by_spectrum = {
                str(spectrum_id): tuple(str(ion) for ion in ions)
                for spectrum_id, ions in raw_fragment_support.items()
            }
        evidence = parse_ptm_localization_tsv(
            evidence_tsv,
            mapping=PtmLocalizationColumnMapping(
                sample_id=sample_column,
                spectrum_id=spectrum_id_column,
                peptide=peptide_column,
                charge=charge_column,
                score=score_column,
                protein_refs=protein_refs_column,
                q_value=q_value_column,
                localization_score=localization_score_column,
                localization_probability=localization_probability_column,
                candidate_sites=candidate_sites_column,
                decoy_label=decoy_label_column,
                protein_separator=protein_separator,
                site_separator=site_separator,
            ),
        )
        report = build_ptm_localization_scoring_report(
            evidence.accepted_records,
            fragment_ion_support_by_spectrum=fragment_ion_support_by_spectrum,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_ptm_localization_scoring_summary_tsv(report),
            encoding="utf-8",
        )
    if entry_tsv_out is not None:
        entry_tsv_out.write_text(
            render_ptm_localization_scoring_entry_tsv(report),
            encoding="utf-8",
        )

    _emit_json(
        {
            "accepted_rows": len(evidence.accepted_records),
            "rejected_rows": len(evidence.rejected_rows),
            "localization_scoring": report.to_dict(),
        },
        out_path=out_path,
    )


@ptm_group.command("ambiguity-review")
@click.argument(
    "evidence_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--features",
    "feature_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option(
    "--localization-score-column", default="localization_score", show_default=True
)
@click.option(
    "--localization-probability-column",
    default="localization_probability",
    show_default=True,
)
@click.option("--candidate-sites-column", default="candidate_sites", show_default=True)
@click.option("--decoy-label-column", default="decoy_label", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--site-separator", default=";", show_default=True)
@click.option(
    "--fragment-support-json",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--localized-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unlocalized-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--group-quant-summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--group-quant-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--group-quant-missingness-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_ambiguity_review_command(
    evidence_tsv: Path,
    proteins_fasta: Path,
    feature_path: Path | None,
    sample_column: str,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    protein_refs_column: str,
    q_value_column: str | None,
    localization_score_column: str,
    localization_probability_column: str | None,
    candidate_sites_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
    site_separator: str,
    fragment_support_json: Path | None,
    summary_tsv_out: Path | None,
    localized_tsv_out: Path | None,
    unlocalized_tsv_out: Path | None,
    group_quant_summary_tsv_out: Path | None,
    group_quant_matrix_tsv_out: Path | None,
    group_quant_missingness_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Review PTM localization ambiguity and optional ambiguity-group quantification."""
    try:
        if feature_path is None and any(
            output is not None
            for output in (
                group_quant_summary_tsv_out,
                group_quant_matrix_tsv_out,
                group_quant_missingness_tsv_out,
            )
        ):
            raise click.ClickException(
                "group quantification TSV outputs require --features because unresolved-site quantification depends on feature intensities"
            )
        fragment_ion_support_by_spectrum: dict[str, tuple[str, ...]] | None = None
        if fragment_support_json is not None:
            raw_fragment_support = json.loads(
                fragment_support_json.read_text(encoding="utf-8")
            )
            if not isinstance(raw_fragment_support, dict):
                raise ValueError("fragment support JSON must be an object keyed by spectrum id")
            fragment_ion_support_by_spectrum = {
                str(spectrum_id): tuple(str(ion) for ion in ions)
                for spectrum_id, ions in raw_fragment_support.items()
            }
        evidence = parse_ptm_localization_tsv(
            evidence_tsv,
            mapping=PtmLocalizationColumnMapping(
                sample_id=sample_column,
                spectrum_id=spectrum_id_column,
                peptide=peptide_column,
                charge=charge_column,
                score=score_column,
                protein_refs=protein_refs_column,
                q_value=q_value_column,
                localization_score=localization_score_column,
                localization_probability=localization_probability_column,
                candidate_sites=candidate_sites_column,
                decoy_label=decoy_label_column,
                protein_separator=protein_separator,
                site_separator=site_separator,
            ),
        )
        fasta_report = parse_fasta_document(
            proteins_fasta.read_text(),
            mode=FastaParseMode.STRICT,
        )
        if fasta_report.rejected_records:
            rejected = ", ".join(
                record.source_identifier for record in fasta_report.rejected_records
            )
            raise click.ClickException(
                f"FASTA input contains rejected records under strict mode: {rejected}"
            )
        protein_sequences = {
            record.canonical_accession: record.residues
            for record in fasta_report.accepted_records
        }
        mappings = map_ptm_evidence_to_protein_sites(
            evidence.accepted_records,
            protein_sequences=protein_sequences,
        )
        site_table = build_ptm_site_table(mappings)
        localization = build_ptm_localization_scoring_report(
            evidence.accepted_records,
            fragment_ion_support_by_spectrum=fragment_ion_support_by_spectrum,
        )
        ambiguity_review = build_ptm_ambiguity_review_report(
            site_table,
            localization_scoring_report=localization,
            protein_sequences=protein_sequences,
        )
        site_group_quantification = None
        if feature_path is not None:
            feature_report = parse_ms1_feature_table(feature_path)
            site_group_quantification = build_ptm_site_group_quantification_report(
                site_table,
                feature_records=feature_report.accepted_records,
                localization_scoring_report=localization,
                protein_sequences=protein_sequences,
            )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_ptm_ambiguity_review_summary_tsv(ambiguity_review),
            encoding="utf-8",
        )
    if localized_tsv_out is not None:
        localized_tsv_out.write_text(
            render_ptm_localized_site_review_tsv(ambiguity_review),
            encoding="utf-8",
        )
    if unlocalized_tsv_out is not None:
        unlocalized_tsv_out.write_text(
            render_ptm_unlocalized_group_review_tsv(ambiguity_review),
            encoding="utf-8",
        )
    if (
        group_quant_summary_tsv_out is not None
        and site_group_quantification is not None
    ):
        group_quant_summary_tsv_out.write_text(
            render_ptm_site_group_quant_summary_tsv(site_group_quantification),
            encoding="utf-8",
        )
    if (
        group_quant_matrix_tsv_out is not None
        and site_group_quantification is not None
    ):
        group_quant_matrix_tsv_out.write_text(
            render_ptm_site_group_quant_matrix_tsv(site_group_quantification),
            encoding="utf-8",
        )
    if (
        group_quant_missingness_tsv_out is not None
        and site_group_quantification is not None
    ):
        group_quant_missingness_tsv_out.write_text(
            render_ptm_site_group_quant_missingness_tsv(site_group_quantification),
            encoding="utf-8",
        )

    _emit_json(
        {
            "accepted_rows": len(evidence.accepted_records),
            "rejected_rows": len(evidence.rejected_rows),
            "ambiguity_review": ambiguity_review.to_dict(),
            "site_group_quantification": None
            if site_group_quantification is None
            else site_group_quantification.to_dict(),
        },
        out_path=out_path,
    )


@ptm_group.command("quantify-sites")
@click.argument(
    "evidence_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "feature_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option(
    "--localization-score-column", default="localization_score", show_default=True
)
@click.option(
    "--localization-probability-column",
    default="localization_probability",
    show_default=True,
)
@click.option("--candidate-sites-column", default="candidate_sites", show_default=True)
@click.option("--decoy-label-column", default="decoy_label", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--site-separator", default=";", show_default=True)
@click.option(
    "--ambiguity-policy",
    type=click.Choice(
        [policy.value for policy in PtmSiteQuantAmbiguityPolicy], case_sensitive=False
    ),
    default=PtmSiteQuantAmbiguityPolicy.PRESERVE.value,
    show_default=True,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--missingness-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--ambiguous-group-summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--ambiguous-group-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--ambiguous-group-missingness-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--excluded-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_quantify_sites_command(
    evidence_tsv: Path,
    proteins_fasta: Path,
    feature_tsv: Path,
    sample_column: str,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    protein_refs_column: str,
    q_value_column: str | None,
    localization_score_column: str,
    localization_probability_column: str | None,
    candidate_sites_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
    site_separator: str,
    ambiguity_policy: str,
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    missingness_tsv_out: Path | None,
    ambiguous_group_summary_tsv_out: Path | None,
    ambiguous_group_matrix_tsv_out: Path | None,
    ambiguous_group_missingness_tsv_out: Path | None,
    excluded_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Quantify PTM sites across samples from localized evidence and feature intensities."""
    try:
        resolved_ambiguity_policy = PtmSiteQuantAmbiguityPolicy(
            ambiguity_policy.lower()
        )
        if (
            resolved_ambiguity_policy is PtmSiteQuantAmbiguityPolicy.EXCLUDE
            and (
                ambiguous_group_summary_tsv_out is not None
                or ambiguous_group_matrix_tsv_out is not None
                or ambiguous_group_missingness_tsv_out is not None
            )
        ):
            raise click.ClickException(
                "ambiguous-group TSV outputs require --ambiguity-policy preserve because excluded ambiguous site rows are not quantified into one group matrix"
            )
        evidence = parse_ptm_localization_tsv(
            evidence_tsv,
            mapping=PtmLocalizationColumnMapping(
                sample_id=sample_column,
                spectrum_id=spectrum_id_column,
                peptide=peptide_column,
                charge=charge_column,
                score=score_column,
                protein_refs=protein_refs_column,
                q_value=q_value_column,
                localization_score=localization_score_column,
                localization_probability=localization_probability_column,
                candidate_sites=candidate_sites_column,
                decoy_label=decoy_label_column,
                protein_separator=protein_separator,
                site_separator=site_separator,
            ),
        )
        fasta_report = parse_fasta_document(
            proteins_fasta.read_text(),
            mode=FastaParseMode.STRICT,
        )
        if fasta_report.rejected_records:
            rejected = ", ".join(
                record.source_identifier for record in fasta_report.rejected_records
            )
            raise click.ClickException(
                f"FASTA input contains rejected records under strict mode: {rejected}"
            )
        protein_sequences = {
            record.canonical_accession: record.residues
            for record in fasta_report.accepted_records
        }
        mappings = map_ptm_evidence_to_protein_sites(
            evidence.accepted_records,
            protein_sequences=protein_sequences,
        )
        site_table = build_ptm_site_table(mappings)
        feature_report = parse_ms1_feature_table(feature_tsv)
        report = build_ptm_site_quantification_report(
            site_table,
            feature_records=feature_report.accepted_records,
            ambiguity_policy=resolved_ambiguity_policy,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_ptm_site_quant_summary_tsv(report),
            encoding="utf-8",
        )
    if matrix_tsv_out is not None:
        matrix_tsv_out.write_text(
            render_ptm_site_quant_matrix_tsv(report),
            encoding="utf-8",
        )
    if missingness_tsv_out is not None:
        missingness_tsv_out.write_text(
            render_ptm_site_quant_missingness_tsv(report),
            encoding="utf-8",
        )
    if (
        ambiguous_group_summary_tsv_out is not None
        and report.ambiguous_group_quantification is not None
    ):
        ambiguous_group_summary_tsv_out.write_text(
            render_ptm_site_group_quant_summary_tsv(
                report.ambiguous_group_quantification
            ),
            encoding="utf-8",
        )
    if (
        ambiguous_group_matrix_tsv_out is not None
        and report.ambiguous_group_quantification is not None
    ):
        ambiguous_group_matrix_tsv_out.write_text(
            render_ptm_site_group_quant_matrix_tsv(
                report.ambiguous_group_quantification
            ),
            encoding="utf-8",
        )
    if (
        ambiguous_group_missingness_tsv_out is not None
        and report.ambiguous_group_quantification is not None
    ):
        ambiguous_group_missingness_tsv_out.write_text(
            render_ptm_site_group_quant_missingness_tsv(
                report.ambiguous_group_quantification
            ),
            encoding="utf-8",
        )
    if excluded_tsv_out is not None:
        excluded_tsv_out.write_text(
            render_ptm_site_quant_excluded_tsv(report),
            encoding="utf-8",
        )

    _emit_json(
        {
            "accepted_rows": len(evidence.accepted_records),
            "feature_rows": len(feature_report.accepted_records),
            "site_quantification": report.to_dict(),
        },
        out_path=out_path,
    )


@ptm_group.command("estimate-occupancy")
@click.argument(
    "evidence_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "feature_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option(
    "--localization-score-column", default="localization_score", show_default=True
)
@click.option(
    "--localization-probability-column",
    default="localization_probability",
    show_default=True,
)
@click.option("--candidate-sites-column", default="candidate_sites", show_default=True)
@click.option("--decoy-label-column", default="decoy_label", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--site-separator", default=";", show_default=True)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--occupancy-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--counterpart-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_estimate_occupancy_command(
    evidence_tsv: Path,
    proteins_fasta: Path,
    feature_tsv: Path,
    sample_column: str,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    protein_refs_column: str,
    q_value_column: str | None,
    localization_score_column: str,
    localization_probability_column: str | None,
    candidate_sites_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
    site_separator: str,
    summary_tsv_out: Path | None,
    occupancy_tsv_out: Path | None,
    counterpart_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Estimate PTM occupancy and export counterpart-coverage review ledgers."""
    try:
        evidence = parse_ptm_localization_tsv(
            evidence_tsv,
            mapping=PtmLocalizationColumnMapping(
                sample_id=sample_column,
                spectrum_id=spectrum_id_column,
                peptide=peptide_column,
                charge=charge_column,
                score=score_column,
                protein_refs=protein_refs_column,
                q_value=q_value_column,
                localization_score=localization_score_column,
                localization_probability=localization_probability_column,
                candidate_sites=candidate_sites_column,
                decoy_label=decoy_label_column,
                protein_separator=protein_separator,
                site_separator=site_separator,
            ),
        )
        fasta_report = parse_fasta_document(
            proteins_fasta.read_text(),
            mode=FastaParseMode.STRICT,
        )
        if fasta_report.rejected_records:
            rejected = ", ".join(
                record.source_identifier for record in fasta_report.rejected_records
            )
            raise click.ClickException(
                f"FASTA input contains rejected records under strict mode: {rejected}"
            )
        protein_sequences = {
            record.canonical_accession: record.residues
            for record in fasta_report.accepted_records
        }
        mappings = map_ptm_evidence_to_protein_sites(
            evidence.accepted_records,
            protein_sequences=protein_sequences,
        )
        site_table = build_ptm_site_table(mappings)
        feature_report = parse_ms1_feature_table(feature_tsv)
        occupancy_report = build_ptm_site_occupancy_report(
            site_table,
            feature_records=feature_report.accepted_records,
        )
        counterpart_report = build_ptm_occupancy_counterpart_report(
            site_table,
            feature_records=feature_report.accepted_records,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_ptm_site_occupancy_summary_tsv(occupancy_report),
            encoding="utf-8",
        )
    if occupancy_tsv_out is not None:
        occupancy_tsv_out.write_text(
            render_ptm_site_occupancy_entry_tsv(occupancy_report),
            encoding="utf-8",
        )
    if counterpart_tsv_out is not None:
        counterpart_tsv_out.write_text(
            render_ptm_occupancy_counterpart_tsv(counterpart_report),
            encoding="utf-8",
        )

    _emit_json(
        {
            "accepted_rows": len(evidence.accepted_records),
            "feature_rows": len(feature_report.accepted_records),
            "occupancy_report": occupancy_report.to_dict(),
            "counterpart_report": counterpart_report.to_dict(),
        },
        out_path=out_path,
    )


@ptm_group.command("differential")
@click.argument(
    "evidence_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "feature_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option(
    "--localization-score-column", default="localization_score", show_default=True
)
@click.option(
    "--localization-probability-column",
    default="localization_probability",
    show_default=True,
)
@click.option("--candidate-sites-column", default="candidate_sites", show_default=True)
@click.option("--decoy-label-column", default="decoy_label", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--site-separator", default=";", show_default=True)
@click.option(
    "--ambiguity-policy",
    type=click.Choice(
        [policy.value for policy in PtmSiteQuantAmbiguityPolicy], case_sensitive=False
    ),
    default=PtmSiteQuantAmbiguityPolicy.PRESERVE.value,
    show_default=True,
)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option("--design-batch-field", default="batch", show_default=True)
@click.option("--design-pairing-field", default=None)
@click.option("--design-covariate", "design_covariates", multiple=True)
@click.option(
    "--protein-correction-mode",
    type=click.Choice(
        [mode.value for mode in PtmProteinCorrectionMode], case_sensitive=False
    ),
    default=PtmProteinCorrectionMode.NONE.value,
    show_default=True,
)
@click.option(
    "--results-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--broken-pairs-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--volcano-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--volcano-json-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--volcano-svg-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--volcano-html-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--volcano-adjusted-p-value-threshold",
    type=float,
    default=0.1,
    show_default=True,
)
@click.option(
    "--volcano-absolute-log2-fold-change-threshold",
    type=float,
    default=1.0,
    show_default=True,
)
@click.option(
    "--volcano-top-label-count",
    type=int,
    default=10,
    show_default=True,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_differential_command(
    evidence_tsv: Path,
    proteins_fasta: Path,
    feature_tsv: Path,
    design_path: Path,
    sample_column: str,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    protein_refs_column: str,
    q_value_column: str | None,
    localization_score_column: str,
    localization_probability_column: str | None,
    candidate_sites_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
    site_separator: str,
    ambiguity_policy: str,
    normalization: str,
    condition_a: str | None,
    condition_b: str | None,
    design_batch_field: str,
    design_pairing_field: str | None,
    design_covariates: tuple[str, ...],
    protein_correction_mode: str,
    results_tsv_out: Path | None,
    broken_pairs_tsv_out: Path | None,
    volcano_tsv_out: Path | None,
    volcano_json_out: Path | None,
    volcano_svg_out: Path | None,
    volcano_html_out: Path | None,
    volcano_adjusted_p_value_threshold: float,
    volcano_absolute_log2_fold_change_threshold: float,
    volcano_top_label_count: int,
    out_path: Path | None,
) -> None:
    """Test PTM site changes across conditions from localized evidence and feature intensities."""
    try:
        evidence = parse_ptm_localization_tsv(
            evidence_tsv,
            mapping=PtmLocalizationColumnMapping(
                sample_id=sample_column,
                spectrum_id=spectrum_id_column,
                peptide=peptide_column,
                charge=charge_column,
                score=score_column,
                protein_refs=protein_refs_column,
                q_value=q_value_column,
                localization_score=localization_score_column,
                localization_probability=localization_probability_column,
                candidate_sites=candidate_sites_column,
                decoy_label=decoy_label_column,
                protein_separator=protein_separator,
                site_separator=site_separator,
            ),
        )
        fasta_report = parse_fasta_document(
            proteins_fasta.read_text(),
            mode=FastaParseMode.STRICT,
        )
        if fasta_report.rejected_records:
            rejected = ", ".join(
                record.source_identifier for record in fasta_report.rejected_records
            )
            raise click.ClickException(
                f"FASTA input contains rejected records under strict mode: {rejected}"
            )
        protein_sequences = {
            record.canonical_accession: record.residues
            for record in fasta_report.accepted_records
        }
        mappings = map_ptm_evidence_to_protein_sites(
            evidence.accepted_records,
            protein_sequences=protein_sequences,
        )
        site_table = build_ptm_site_table(mappings)
        feature_report = parse_ms1_feature_table(feature_tsv)
        site_quantification = build_ptm_site_quantification_report(
            site_table,
            feature_records=feature_report.accepted_records,
            ambiguity_policy=PtmSiteQuantAmbiguityPolicy(ambiguity_policy.lower()),
        )
        design_report = parse_experimental_design_table(design_path)
        if design_report.rejected_rows:
            raise click.ClickException("design table contains rejected rows")
        report = build_ptm_differential_analysis_report(
            site_quantification,
            design_report.accepted_entries,
            normalization_method=NormalizationMethod(normalization),
            condition_a=condition_a,
            condition_b=condition_b,
            feature_records=feature_report.accepted_records,
            protein_correction_mode=PtmProteinCorrectionMode(
                protein_correction_mode.lower()
            ),
            batch_field=design_batch_field,
            covariate_fields=tuple(dict.fromkeys(design_covariates)),
            pairing_field=design_pairing_field,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    volcano_plot = report.volcano_plot
    volcano_review = None
    if (
        volcano_tsv_out is not None
        or volcano_json_out is not None
        or volcano_svg_out is not None
        or volcano_html_out is not None
    ):
        volcano_plot = build_ptm_differential_volcano_plot(
            report.differential_report,
            adjusted_p_value_threshold=volcano_adjusted_p_value_threshold,
            absolute_log2_fold_change_threshold=(
                volcano_absolute_log2_fold_change_threshold
            ),
        )
        volcano_review = build_ptm_volcano_review(
            volcano_plot,
            policy=_build_volcano_review_policy(
                adjusted_p_value_threshold=volcano_adjusted_p_value_threshold,
                absolute_log2_fold_change_threshold=(
                    volcano_absolute_log2_fold_change_threshold
                ),
                top_label_count=volcano_top_label_count,
            ),
        )

    if results_tsv_out is not None:
        export_ptm_site_differential_tsv(report.differential_report, results_tsv_out)
    if broken_pairs_tsv_out is not None:
        export_ptm_site_differential_broken_pairs_tsv(
            report.differential_report,
            broken_pairs_tsv_out,
        )
    if volcano_tsv_out is not None:
        assert volcano_plot is not None
        export_ptm_differential_volcano_tsv(volcano_plot, volcano_tsv_out)
    if volcano_review is not None:
        _export_volcano_review_assets(
            review_report=volcano_review,
            json_out=volcano_json_out,
            svg_out=volcano_svg_out,
            html_out=volcano_html_out,
        )

    _emit_json(
        {
            "accepted_rows": len(evidence.accepted_records),
            "feature_rows": len(feature_report.accepted_records),
            "site_quantification": report.site_quantification.to_dict(),
            "design_matrix": report.design_matrix.to_dict(),
            "design_model_fit": report.design_model_fit.to_dict(),
            "protein_correction_mode": report.protein_correction_mode.value,
            "differential_report": report.differential_report.to_dict(),
            "volcano_plot": None if volcano_plot is None else volcano_plot.to_dict(),
            "volcano_review": (
                None if volcano_review is None else volcano_review.to_dict()
            ),
            "outputs": {
                "results_tsv": None if results_tsv_out is None else str(results_tsv_out),
                "broken_pairs_tsv": (
                    None if broken_pairs_tsv_out is None else str(broken_pairs_tsv_out)
                ),
                "volcano_tsv": None if volcano_tsv_out is None else str(volcano_tsv_out),
                "volcano_json": (
                    None if volcano_json_out is None else str(volcano_json_out)
                ),
                "volcano_svg": (
                    None if volcano_svg_out is None else str(volcano_svg_out)
                ),
                "volcano_html": (
                    None if volcano_html_out is None else str(volcano_html_out)
                ),
            },
        },
        out_path=out_path,
    )


@ptm_group.command("motif-enrichment")
@click.argument(
    "evidence_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "feature_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option(
    "--localization-score-column", default="localization_score", show_default=True
)
@click.option(
    "--localization-probability-column",
    default="localization_probability",
    show_default=True,
)
@click.option("--candidate-sites-column", default="candidate_sites", show_default=True)
@click.option("--decoy-label-column", default="decoy_label", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--site-separator", default=";", show_default=True)
@click.option(
    "--ambiguity-policy",
    type=click.Choice(
        [policy.value for policy in PtmSiteQuantAmbiguityPolicy], case_sensitive=False
    ),
    default=PtmSiteQuantAmbiguityPolicy.PRESERVE.value,
    show_default=True,
)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option("--design-batch-field", default="batch", show_default=True)
@click.option("--design-pairing-field", default=None)
@click.option("--design-covariate", "design_covariates", multiple=True)
@click.option(
    "--protein-correction-mode",
    type=click.Choice(
        [mode.value for mode in PtmProteinCorrectionMode], case_sensitive=False
    ),
    default=PtmProteinCorrectionMode.NONE.value,
    show_default=True,
)
@click.option("--flank-size", default=7, show_default=True, type=int)
@click.option("--max-adjusted-p-value", default=0.1, show_default=True, type=float)
@click.option(
    "--min-absolute-log2-fold-change",
    default=1.0,
    show_default=True,
    type=float,
)
@click.option(
    "--direction",
    type=click.Choice(
        [direction.value for direction in PtmMotifRegulationDirection],
        case_sensitive=False,
    ),
    default=PtmMotifRegulationDirection.BOTH.value,
    show_default=True,
)
@click.option(
    "--include-ambiguous-regulated-sites/--exclude-ambiguous-regulated-sites",
    default=False,
    show_default=True,
)
@click.option(
    "--include-ambiguous-background-sites/--exclude-ambiguous-background-sites",
    default=False,
    show_default=True,
)
@click.option(
    "--background-mode",
    type=click.Choice(
        [mode.value for mode in PtmMotifBackgroundMode],
        case_sensitive=False,
    ),
    default=PtmMotifBackgroundMode.OBSERVED_SITE_BACKGROUND.value,
    show_default=True,
)
@click.option(
    "--min-frequency-difference",
    default=0.1,
    show_default=True,
    type=float,
)
@click.option(
    "--min-enrichment-ratio",
    default=1.5,
    show_default=True,
    type=float,
)
@click.option(
    "--max-reported-term-count",
    default=25,
    show_default=True,
    type=int,
)
@click.option(
    "--window-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--frequency-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--enriched-term-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--logo-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_motif_enrichment_command(
    evidence_tsv: Path,
    proteins_fasta: Path,
    feature_tsv: Path,
    design_path: Path,
    sample_column: str,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    protein_refs_column: str,
    q_value_column: str | None,
    localization_score_column: str,
    localization_probability_column: str | None,
    candidate_sites_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
    site_separator: str,
    ambiguity_policy: str,
    normalization: str,
    condition_a: str | None,
    condition_b: str | None,
    design_batch_field: str,
    design_pairing_field: str | None,
    design_covariates: tuple[str, ...],
    protein_correction_mode: str,
    flank_size: int,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
    direction: str,
    include_ambiguous_regulated_sites: bool,
    include_ambiguous_background_sites: bool,
    background_mode: str,
    min_frequency_difference: float,
    min_enrichment_ratio: float,
    max_reported_term_count: int,
    window_tsv_out: Path | None,
    frequency_tsv_out: Path | None,
    enriched_term_tsv_out: Path | None,
    logo_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Compare regulated phosphosite sequence motifs against a PTM background set."""
    try:
        evidence = parse_ptm_localization_tsv(
            evidence_tsv,
            mapping=PtmLocalizationColumnMapping(
                sample_id=sample_column,
                spectrum_id=spectrum_id_column,
                peptide=peptide_column,
                charge=charge_column,
                score=score_column,
                protein_refs=protein_refs_column,
                q_value=q_value_column,
                localization_score=localization_score_column,
                localization_probability=localization_probability_column,
                candidate_sites=candidate_sites_column,
                decoy_label=decoy_label_column,
                protein_separator=protein_separator,
                site_separator=site_separator,
            ),
        )
        fasta_report = parse_fasta_document(
            proteins_fasta.read_text(),
            mode=FastaParseMode.STRICT,
        )
        if fasta_report.rejected_records:
            rejected = ", ".join(
                record.source_identifier for record in fasta_report.rejected_records
            )
            raise click.ClickException(
                f"FASTA input contains rejected records under strict mode: {rejected}"
            )
        protein_sequences = {
            record.canonical_accession: record.residues
            for record in fasta_report.accepted_records
        }
        mappings = map_ptm_evidence_to_protein_sites(
            evidence.accepted_records,
            protein_sequences=protein_sequences,
        )
        site_table = build_ptm_site_table(mappings)
        feature_report = parse_ms1_feature_table(feature_tsv)
        site_quantification = build_ptm_site_quantification_report(
            site_table,
            feature_records=feature_report.accepted_records,
            ambiguity_policy=PtmSiteQuantAmbiguityPolicy(ambiguity_policy.lower()),
        )
        design_report = parse_experimental_design_table(design_path)
        if design_report.rejected_rows:
            raise click.ClickException("design table contains rejected rows")
        differential = build_ptm_differential_analysis_report(
            site_quantification,
            design_report.accepted_entries,
            normalization_method=NormalizationMethod(normalization),
            condition_a=condition_a,
            condition_b=condition_b,
            feature_records=feature_report.accepted_records,
            protein_correction_mode=PtmProteinCorrectionMode(
                protein_correction_mode.lower()
            ),
            batch_field=design_batch_field,
            covariate_fields=tuple(dict.fromkeys(design_covariates)),
            pairing_field=design_pairing_field,
        )
        report = build_ptm_phosphosite_motif_enrichment_report(
            differential,
            protein_sequences=protein_sequences,
            flank_size=flank_size,
            selection_policy=PtmPhosphositeSelectionPolicy(
                max_adjusted_p_value=max_adjusted_p_value,
                min_absolute_log2_fold_change=min_absolute_log2_fold_change,
                direction=PtmMotifRegulationDirection(direction.lower()),
                include_ambiguous_regulated_sites=include_ambiguous_regulated_sites,
                include_ambiguous_background_sites=include_ambiguous_background_sites,
            ),
            comparison_policy=PtmMotifComparisonPolicy(
                background_mode=PtmMotifBackgroundMode(background_mode.lower()),
                min_frequency_difference=min_frequency_difference,
                min_enrichment_ratio=min_enrichment_ratio,
                max_reported_term_count=max_reported_term_count,
            ),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if window_tsv_out is not None:
        export_ptm_phosphosite_motif_window_tsv(report, window_tsv_out)
    if frequency_tsv_out is not None:
        export_ptm_phosphosite_motif_frequency_tsv(report, frequency_tsv_out)
    if enriched_term_tsv_out is not None:
        export_ptm_phosphosite_motif_enriched_term_tsv(report, enriched_term_tsv_out)
    if logo_tsv_out is not None:
        export_ptm_phosphosite_motif_logo_tsv(report, logo_tsv_out)

    _emit_json(
        {
            "accepted_rows": len(evidence.accepted_records),
            "feature_rows": len(feature_report.accepted_records),
            "protein_correction_mode": differential.protein_correction_mode.value,
            "motif_enrichment_report": report.to_dict(),
            "outputs": {
                "window_tsv": None if window_tsv_out is None else str(window_tsv_out),
                "frequency_tsv": None
                if frequency_tsv_out is None
                else str(frequency_tsv_out),
                "enriched_term_tsv": None
                if enriched_term_tsv_out is None
                else str(enriched_term_tsv_out),
                "logo_tsv": None if logo_tsv_out is None else str(logo_tsv_out),
            },
        },
        out_path=out_path,
    )


@ptm_group.command("annotate-sites")
@click.argument(
    "evidence_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "annotation_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option(
    "--localization-score-column", default="localization_score", show_default=True
)
@click.option(
    "--localization-probability-column",
    default="localization_probability",
    show_default=True,
)
@click.option("--candidate-sites-column", default="candidate_sites", show_default=True)
@click.option("--decoy-label-column", default="decoy_label", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--site-separator", default=";", show_default=True)
@click.option("--annotation-species-column", default="species", show_default=True)
@click.option(
    "--annotation-protein-ref-column",
    default="protein_ref",
    show_default=True,
)
@click.option("--annotation-residue-column", default="residue", show_default=True)
@click.option("--annotation-position-column", default="position", show_default=True)
@click.option(
    "--annotation-modification-column",
    default="modification_name",
    show_default=True,
)
@click.option(
    "--annotation-function-column",
    default="site_function",
    show_default=True,
)
@click.option("--annotation-kinase-column", default="kinases", show_default=True)
@click.option(
    "--annotation-phosphatase-column",
    default="phosphatases",
    show_default=True,
)
@click.option("--annotation-pathway-column", default="pathways", show_default=True)
@click.option("--annotation-source-name-column", default="source_name", show_default=True)
@click.option(
    "--annotation-source-accession-column",
    default="source_accession",
    show_default=True,
)
@click.option("--kinase-separator", default=";", show_default=True)
@click.option("--phosphatase-separator", default=";", show_default=True)
@click.option("--pathway-separator", default=";", show_default=True)
@click.option("--species", "target_species", default=None)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--mapped-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unmapped-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--function-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--kinase-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--phosphatase-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--pathway-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_annotate_sites_command(
    evidence_tsv: Path,
    proteins_fasta: Path,
    annotation_tsv: Path,
    sample_column: str,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    protein_refs_column: str,
    q_value_column: str | None,
    localization_score_column: str,
    localization_probability_column: str | None,
    candidate_sites_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
    site_separator: str,
    annotation_species_column: str,
    annotation_protein_ref_column: str,
    annotation_residue_column: str,
    annotation_position_column: str,
    annotation_modification_column: str,
    annotation_function_column: str,
    annotation_kinase_column: str,
    annotation_phosphatase_column: str,
    annotation_pathway_column: str,
    annotation_source_name_column: str,
    annotation_source_accession_column: str,
    kinase_separator: str,
    phosphatase_separator: str,
    pathway_separator: str,
    target_species: str | None,
    summary_tsv_out: Path | None,
    mapped_tsv_out: Path | None,
    unmapped_tsv_out: Path | None,
    function_tsv_out: Path | None,
    kinase_tsv_out: Path | None,
    phosphatase_tsv_out: Path | None,
    pathway_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Map imported PTM site annotations onto observed PTM sites."""
    try:
        evidence = parse_ptm_localization_tsv(
            evidence_tsv,
            mapping=PtmLocalizationColumnMapping(
                sample_id=sample_column,
                spectrum_id=spectrum_id_column,
                peptide=peptide_column,
                charge=charge_column,
                score=score_column,
                protein_refs=protein_refs_column,
                q_value=q_value_column,
                localization_score=localization_score_column,
                localization_probability=localization_probability_column,
                candidate_sites=candidate_sites_column,
                decoy_label=decoy_label_column,
                protein_separator=protein_separator,
                site_separator=site_separator,
            ),
        )
        fasta_report = parse_fasta_document(
            proteins_fasta.read_text(),
            mode=FastaParseMode.STRICT,
        )
        if fasta_report.rejected_records:
            rejected = ", ".join(
                record.source_identifier for record in fasta_report.rejected_records
            )
            raise click.ClickException(
                f"FASTA input contains rejected records under strict mode: {rejected}"
            )
        protein_sequences = {
            record.canonical_accession: record.residues
            for record in fasta_report.accepted_records
        }
        resolved_target_species = target_species
        if resolved_target_species is None:
            observed_species = {
                record.organism for record in fasta_report.accepted_records if record.organism
            }
            if len(observed_species) == 1:
                resolved_target_species = next(iter(observed_species))
        mappings = map_ptm_evidence_to_protein_sites(
            evidence.accepted_records,
            protein_sequences=protein_sequences,
        )
        site_table = build_ptm_site_table(mappings)
        annotation_report = parse_ptm_site_annotation_tsv(
            annotation_tsv,
            mapping=PtmSiteAnnotationColumnMapping(
                species=annotation_species_column,
                protein_ref=annotation_protein_ref_column,
                residue=annotation_residue_column,
                position=annotation_position_column,
                modification_name=annotation_modification_column,
                site_function=annotation_function_column,
                kinases=annotation_kinase_column,
                phosphatases=annotation_phosphatase_column,
                pathways=annotation_pathway_column,
                source_name=annotation_source_name_column,
                source_accession=annotation_source_accession_column,
            ),
            kinase_separator=kinase_separator,
            phosphatase_separator=phosphatase_separator,
            pathway_separator=pathway_separator,
        )
        mapping_report = build_ptm_site_annotation_mapping_report(
            site_table,
            annotation_report.accepted_records,
            target_species=resolved_target_species,
        )
        biology_summary = build_ptm_site_annotation_biology_summary(mapping_report)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_ptm_site_annotation_mapping_summary_tsv(
            mapping_report,
            summary_tsv_out,
        )
    if mapped_tsv_out is not None:
        export_ptm_mapped_site_annotation_tsv(mapping_report, mapped_tsv_out)
    if unmapped_tsv_out is not None:
        export_ptm_unmapped_site_annotation_tsv(mapping_report, unmapped_tsv_out)
    if function_tsv_out is not None:
        export_ptm_site_annotation_biology_tsv(
            biology_summary,
            category="function",
            path=function_tsv_out,
        )
    if kinase_tsv_out is not None:
        export_ptm_site_annotation_biology_tsv(
            biology_summary,
            category="kinase",
            path=kinase_tsv_out,
        )
    if phosphatase_tsv_out is not None:
        export_ptm_site_annotation_biology_tsv(
            biology_summary,
            category="phosphatase",
            path=phosphatase_tsv_out,
        )
    if pathway_tsv_out is not None:
        export_ptm_site_annotation_biology_tsv(
            biology_summary,
            category="pathway",
            path=pathway_tsv_out,
        )

    _emit_json(
        {
            "accepted_rows": len(evidence.accepted_records),
            "annotation_rows": annotation_report.summary.accepted_record_count,
            "rejected_annotation_rows": annotation_report.summary.rejected_row_count,
            "target_species": resolved_target_species,
            "mapping_report": mapping_report.to_dict(),
            "biology_summary": biology_summary.to_dict(),
            "outputs": {
                "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
                "mapped_tsv": None if mapped_tsv_out is None else str(mapped_tsv_out),
                "unmapped_tsv": None
                if unmapped_tsv_out is None
                else str(unmapped_tsv_out),
                "function_tsv": None
                if function_tsv_out is None
                else str(function_tsv_out),
                "kinase_tsv": None if kinase_tsv_out is None else str(kinase_tsv_out),
                "phosphatase_tsv": None
                if phosphatase_tsv_out is None
                else str(phosphatase_tsv_out),
                "pathway_tsv": None
                if pathway_tsv_out is None
                else str(pathway_tsv_out),
            },
        },
        out_path=out_path,
    )


@ptm_group.command("annotate-context")
@click.argument(
    "evidence_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "context_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option(
    "--localization-score-column", default="localization_score", show_default=True
)
@click.option(
    "--localization-probability-column",
    default="localization_probability",
    show_default=True,
)
@click.option("--candidate-sites-column", default="candidate_sites", show_default=True)
@click.option("--decoy-label-column", default="decoy_label", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--site-separator", default=";", show_default=True)
@click.option("--context-protein-ref-column", default="protein_ref", show_default=True)
@click.option("--context-start-column", default="start", show_default=True)
@click.option("--context-end-column", default="end", show_default=True)
@click.option("--context-domain-column", default="domain_name", show_default=True)
@click.option(
    "--context-disorder-column",
    default="disorder_region",
    show_default=True,
)
@click.option(
    "--context-transmembrane-column",
    default="transmembrane_region",
    show_default=True,
)
@click.option(
    "--context-active-site-column",
    default="active_site_label",
    show_default=True,
)
@click.option("--context-motif-column", default="motif_name", show_default=True)
@click.option(
    "--context-conservation-column",
    default="conservation_score",
    show_default=True,
)
@click.option("--context-source-name-column", default="source_name", show_default=True)
@click.option(
    "--context-source-accession-column",
    default="source_accession",
    show_default=True,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--context-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_annotate_context_command(
    evidence_tsv: Path,
    proteins_fasta: Path,
    context_tsv: Path,
    sample_column: str,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    protein_refs_column: str,
    q_value_column: str | None,
    localization_score_column: str,
    localization_probability_column: str | None,
    candidate_sites_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
    site_separator: str,
    context_protein_ref_column: str,
    context_start_column: str,
    context_end_column: str,
    context_domain_column: str | None,
    context_disorder_column: str | None,
    context_transmembrane_column: str | None,
    context_active_site_column: str | None,
    context_motif_column: str | None,
    context_conservation_column: str | None,
    context_source_name_column: str | None,
    context_source_accession_column: str | None,
    summary_tsv_out: Path | None,
    context_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Annotate observed PTM sites with provided protein-region context."""
    try:
        evidence = parse_ptm_localization_tsv(
            evidence_tsv,
            mapping=PtmLocalizationColumnMapping(
                sample_id=sample_column,
                spectrum_id=spectrum_id_column,
                peptide=peptide_column,
                charge=charge_column,
                score=score_column,
                protein_refs=protein_refs_column,
                q_value=q_value_column,
                localization_score=localization_score_column,
                localization_probability=localization_probability_column,
                candidate_sites=candidate_sites_column,
                decoy_label=decoy_label_column,
                protein_separator=protein_separator,
                site_separator=site_separator,
            ),
        )
        fasta_report = parse_fasta_document(
            proteins_fasta.read_text(),
            mode=FastaParseMode.STRICT,
        )
        if fasta_report.rejected_records:
            rejected = ", ".join(
                record.source_identifier for record in fasta_report.rejected_records
            )
            raise click.ClickException(
                f"FASTA input contains rejected records under strict mode: {rejected}"
            )
        protein_sequences = {
            record.canonical_accession: record.residues
            for record in fasta_report.accepted_records
        }
        mappings = map_ptm_evidence_to_protein_sites(
            evidence.accepted_records,
            protein_sequences=protein_sequences,
        )
        site_table = build_ptm_site_table(mappings)
        context_import_report = parse_ptm_site_context_tsv(
            context_tsv,
            mapping=PtmSiteContextColumnMapping(
                protein_ref=context_protein_ref_column,
                start=context_start_column,
                end=context_end_column,
                domain_name=context_domain_column,
                disorder_region=context_disorder_column,
                transmembrane_region=context_transmembrane_column,
                active_site_label=context_active_site_column,
                motif_name=context_motif_column,
                conservation_score=context_conservation_column,
                source_name=context_source_name_column,
                source_accession=context_source_accession_column,
            ),
        )
        context_report = build_ptm_site_context_report(
            site_table,
            context_import_report.accepted_records,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_ptm_site_context_summary_tsv(context_report, summary_tsv_out)
    if context_tsv_out is not None:
        export_ptm_site_context_tsv(context_report, context_tsv_out)

    _emit_json(
        {
            "accepted_rows": len(evidence.accepted_records),
            "context_rows": context_import_report.summary.accepted_record_count,
            "rejected_context_rows": context_import_report.summary.rejected_row_count,
            "context_report": context_report.to_dict(),
            "outputs": {
                "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
                "context_tsv": None if context_tsv_out is None else str(context_tsv_out),
            },
        },
        out_path=out_path,
    )


@ptm_group.command("regulator-enrichment")
@click.argument(
    "evidence_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "feature_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "annotation_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option(
    "--localization-score-column", default="localization_score", show_default=True
)
@click.option(
    "--localization-probability-column",
    default="localization_probability",
    show_default=True,
)
@click.option("--candidate-sites-column", default="candidate_sites", show_default=True)
@click.option("--decoy-label-column", default="decoy_label", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--site-separator", default=";", show_default=True)
@click.option("--annotation-species-column", default="species", show_default=True)
@click.option(
    "--annotation-protein-ref-column",
    default="protein_ref",
    show_default=True,
)
@click.option("--annotation-residue-column", default="residue", show_default=True)
@click.option("--annotation-position-column", default="position", show_default=True)
@click.option(
    "--annotation-modification-column",
    default="modification_name",
    show_default=True,
)
@click.option(
    "--annotation-function-column",
    default="site_function",
    show_default=True,
)
@click.option("--annotation-kinase-column", default="kinases", show_default=True)
@click.option(
    "--annotation-phosphatase-column",
    default="phosphatases",
    show_default=True,
)
@click.option("--annotation-pathway-column", default="pathways", show_default=True)
@click.option("--annotation-source-name-column", default="source_name", show_default=True)
@click.option(
    "--annotation-source-accession-column",
    default="source_accession",
    show_default=True,
)
@click.option("--kinase-separator", default=";", show_default=True)
@click.option("--phosphatase-separator", default=";", show_default=True)
@click.option("--pathway-separator", default=";", show_default=True)
@click.option("--species", "target_species", default=None)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option("--design-batch-field", default="batch", show_default=True)
@click.option("--design-pairing-field", default=None)
@click.option("--design-covariate", "design_covariates", multiple=True)
@click.option(
    "--protein-correction-mode",
    type=click.Choice(
        [mode.value for mode in PtmProteinCorrectionMode], case_sensitive=False
    ),
    default=PtmProteinCorrectionMode.NONE.value,
    show_default=True,
)
@click.option("--max-adjusted-p-value", default=0.1, show_default=True, type=float)
@click.option(
    "--min-absolute-log2-fold-change",
    default=1.0,
    show_default=True,
    type=float,
)
@click.option(
    "--include-ambiguous-sites/--exclude-ambiguous-sites",
    default=False,
    show_default=True,
)
@click.option(
    "--include-low-localization-sites/--exclude-low-localization-sites",
    default=False,
    show_default=True,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--results-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_regulator_enrichment_command(
    evidence_tsv: Path,
    proteins_fasta: Path,
    feature_tsv: Path,
    design_path: Path,
    annotation_tsv: Path,
    sample_column: str,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    protein_refs_column: str,
    q_value_column: str | None,
    localization_score_column: str,
    localization_probability_column: str | None,
    candidate_sites_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
    site_separator: str,
    annotation_species_column: str,
    annotation_protein_ref_column: str,
    annotation_residue_column: str,
    annotation_position_column: str,
    annotation_modification_column: str,
    annotation_function_column: str,
    annotation_kinase_column: str,
    annotation_phosphatase_column: str,
    annotation_pathway_column: str,
    annotation_source_name_column: str,
    annotation_source_accession_column: str,
    kinase_separator: str,
    phosphatase_separator: str,
    pathway_separator: str,
    target_species: str | None,
    normalization: str,
    condition_a: str | None,
    condition_b: str | None,
    design_batch_field: str,
    design_pairing_field: str | None,
    design_covariates: tuple[str, ...],
    protein_correction_mode: str,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
    include_ambiguous_sites: bool,
    include_low_localization_sites: bool,
    summary_tsv_out: Path | None,
    results_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Score kinase and phosphatase substrate annotations over regulated PTM sites."""
    try:
        evidence = parse_ptm_localization_tsv(
            evidence_tsv,
            mapping=PtmLocalizationColumnMapping(
                sample_id=sample_column,
                spectrum_id=spectrum_id_column,
                peptide=peptide_column,
                charge=charge_column,
                score=score_column,
                protein_refs=protein_refs_column,
                q_value=q_value_column,
                localization_score=localization_score_column,
                localization_probability=localization_probability_column,
                candidate_sites=candidate_sites_column,
                decoy_label=decoy_label_column,
                protein_separator=protein_separator,
                site_separator=site_separator,
            ),
        )
        fasta_report = parse_fasta_document(
            proteins_fasta.read_text(),
            mode=FastaParseMode.STRICT,
        )
        if fasta_report.rejected_records:
            rejected = ", ".join(
                record.source_identifier for record in fasta_report.rejected_records
            )
            raise click.ClickException(
                f"FASTA input contains rejected records under strict mode: {rejected}"
            )
        protein_sequences = {
            record.canonical_accession: record.residues
            for record in fasta_report.accepted_records
        }
        resolved_target_species = target_species
        if resolved_target_species is None:
            observed_species = {
                record.organism for record in fasta_report.accepted_records if record.organism
            }
            if len(observed_species) == 1:
                resolved_target_species = next(iter(observed_species))
        mappings = map_ptm_evidence_to_protein_sites(
            evidence.accepted_records,
            protein_sequences=protein_sequences,
        )
        site_table = build_ptm_site_table(mappings)
        feature_report = parse_ms1_feature_table(feature_tsv)
        site_quantification = build_ptm_site_quantification_report(
            site_table,
            feature_records=feature_report.accepted_records,
        )
        design_report = parse_experimental_design_table(design_path)
        if design_report.rejected_rows:
            raise click.ClickException("design table contains rejected rows")
        differential = build_ptm_differential_analysis_report(
            site_quantification,
            design_report.accepted_entries,
            normalization_method=NormalizationMethod(normalization),
            condition_a=condition_a,
            condition_b=condition_b,
            feature_records=feature_report.accepted_records,
            protein_correction_mode=PtmProteinCorrectionMode(
                protein_correction_mode.lower()
            ),
            batch_field=design_batch_field,
            covariate_fields=tuple(dict.fromkeys(design_covariates)),
            pairing_field=design_pairing_field,
        )
        annotation_report = parse_ptm_site_annotation_tsv(
            annotation_tsv,
            mapping=PtmSiteAnnotationColumnMapping(
                species=annotation_species_column,
                protein_ref=annotation_protein_ref_column,
                residue=annotation_residue_column,
                position=annotation_position_column,
                modification_name=annotation_modification_column,
                site_function=annotation_function_column,
                kinases=annotation_kinase_column,
                phosphatases=annotation_phosphatase_column,
                pathways=annotation_pathway_column,
                source_name=annotation_source_name_column,
                source_accession=annotation_source_accession_column,
            ),
            kinase_separator=kinase_separator,
            phosphatase_separator=phosphatase_separator,
            pathway_separator=pathway_separator,
        )
        mapping_report = build_ptm_site_annotation_mapping_report(
            site_table,
            annotation_report.accepted_records,
            target_species=resolved_target_species,
        )
        enrichment_report = build_ptm_regulator_enrichment_report(
            differential.differential_report,
            mapping_report,
            policy=PtmRegulatorEnrichmentPolicy(
                max_adjusted_p_value=max_adjusted_p_value,
                min_absolute_log2_fold_change=min_absolute_log2_fold_change,
                include_ambiguous_sites=include_ambiguous_sites,
                include_low_localization_sites=include_low_localization_sites,
            ),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_ptm_regulator_enrichment_summary_tsv(
            enrichment_report,
            summary_tsv_out,
        )
    if results_tsv_out is not None:
        export_ptm_regulator_enrichment_tsv(
            enrichment_report,
            results_tsv_out,
        )

    _emit_json(
        {
            "accepted_rows": len(evidence.accepted_records),
            "feature_rows": len(feature_report.accepted_records),
            "annotation_rows": annotation_report.summary.accepted_record_count,
            "rejected_annotation_rows": annotation_report.summary.rejected_row_count,
            "target_species": resolved_target_species,
            "protein_correction_mode": differential.protein_correction_mode.value,
            "mapping_report": mapping_report.to_dict(),
            "regulator_enrichment_report": enrichment_report.to_dict(),
            "outputs": {
                "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
                "results_tsv": None if results_tsv_out is None else str(results_tsv_out),
            },
        },
        out_path=out_path,
    )


@ptm_group.command("report")
@click.argument(
    "evidence_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "feature_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option(
    "--localization-score-column", default="localization_score", show_default=True
)
@click.option(
    "--localization-probability-column",
    default="localization_probability",
    show_default=True,
)
@click.option("--candidate-sites-column", default="candidate_sites", show_default=True)
@click.option("--decoy-label-column", default="decoy_label", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--site-separator", default=";", show_default=True)
@click.option(
    "--fragment-support-json",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--ambiguity-policy",
    type=click.Choice(
        [policy.value for policy in PtmSiteQuantAmbiguityPolicy], case_sensitive=False
    ),
    default=PtmSiteQuantAmbiguityPolicy.PRESERVE.value,
    show_default=True,
)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option("--design-batch-field", default="batch", show_default=True)
@click.option("--design-pairing-field", default=None)
@click.option("--design-covariate", "design_covariates", multiple=True)
@click.option(
    "--protein-correction-mode",
    type=click.Choice(
        [mode.value for mode in PtmProteinCorrectionMode], case_sensitive=False
    ),
    default=PtmProteinCorrectionMode.NONE.value,
    show_default=True,
)
@click.option("--flank-size", default=7, show_default=True, type=int)
@click.option("--max-adjusted-p-value", default=0.1, show_default=True, type=float)
@click.option(
    "--min-absolute-log2-fold-change",
    default=1.0,
    show_default=True,
    type=float,
)
@click.option(
    "--direction",
    type=click.Choice(
        [direction.value for direction in PtmMotifRegulationDirection],
        case_sensitive=False,
    ),
    default=PtmMotifRegulationDirection.BOTH.value,
    show_default=True,
)
@click.option(
    "--include-ambiguous-regulated-sites/--exclude-ambiguous-regulated-sites",
    default=False,
    show_default=True,
)
@click.option(
    "--include-ambiguous-background-sites/--exclude-ambiguous-background-sites",
    default=False,
    show_default=True,
)
@click.option(
    "--min-frequency-difference",
    default=0.1,
    show_default=True,
    type=float,
)
@click.option(
    "--min-enrichment-ratio",
    default=1.5,
    show_default=True,
    type=float,
)
@click.option(
    "--max-reported-term-count",
    default=25,
    show_default=True,
    type=int,
)
@click.option(
    "--annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--species", "target_species", default=None)
@click.option(
    "--card-max-adjusted-p-value",
    default=0.1,
    show_default=True,
    type=float,
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path, file_okay=False),
    required=True,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_report_command(
    evidence_tsv: Path,
    proteins_fasta: Path,
    feature_tsv: Path,
    design_path: Path,
    sample_column: str,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    protein_refs_column: str,
    q_value_column: str | None,
    localization_score_column: str,
    localization_probability_column: str | None,
    candidate_sites_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
    site_separator: str,
    fragment_support_json: Path | None,
    ambiguity_policy: str,
    normalization: str,
    condition_a: str | None,
    condition_b: str | None,
    design_batch_field: str,
    design_pairing_field: str | None,
    design_covariates: tuple[str, ...],
    protein_correction_mode: str,
    flank_size: int,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
    direction: str,
    include_ambiguous_regulated_sites: bool,
    include_ambiguous_background_sites: bool,
    min_frequency_difference: float,
    min_enrichment_ratio: float,
    max_reported_term_count: int,
    annotation_tsv: Path | None,
    target_species: str | None,
    card_max_adjusted_p_value: float,
    output_dir: Path,
    out_path: Path | None,
) -> None:
    """Build one governed PTM report directory over peptide, site, quant, and motif surfaces."""
    result = _run_orchestrated_workflow(
        PtmWorkflowConfig(
            evidence_tsv_path=evidence_tsv,
            proteins_fasta_path=proteins_fasta,
            feature_tsv_path=feature_tsv,
            design_tsv_path=design_path,
            mapping=PtmLocalizationColumnMapping(
                sample_id=sample_column,
                spectrum_id=spectrum_id_column,
                peptide=peptide_column,
                charge=charge_column,
                score=score_column,
                protein_refs=protein_refs_column,
                q_value=q_value_column,
                localization_score=localization_score_column,
                localization_probability=localization_probability_column,
                candidate_sites=candidate_sites_column,
                decoy_label=decoy_label_column,
                protein_separator=protein_separator,
                site_separator=site_separator,
            ),
            fragment_support_json_path=fragment_support_json,
            ambiguity_policy=PtmSiteQuantAmbiguityPolicy(ambiguity_policy.lower()),
            normalization_method=NormalizationMethod(normalization),
            condition_a=condition_a,
            condition_b=condition_b,
            batch_field=design_batch_field,
            covariate_fields=tuple(dict.fromkeys(design_covariates)),
            pairing_field=design_pairing_field,
            protein_correction_mode=PtmProteinCorrectionMode(
                protein_correction_mode.lower()
            ),
            motif_flank_size=flank_size,
            max_adjusted_p_value=max_adjusted_p_value,
            min_absolute_log2_fold_change=min_absolute_log2_fold_change,
            direction=PtmMotifRegulationDirection(direction.lower()),
            include_ambiguous_regulated_sites=include_ambiguous_regulated_sites,
            include_ambiguous_background_sites=include_ambiguous_background_sites,
            min_frequency_difference=min_frequency_difference,
            min_enrichment_ratio=min_enrichment_ratio,
            max_reported_term_count=max_reported_term_count,
            annotation_tsv_path=annotation_tsv,
            annotation_target_species=target_species,
            card_max_adjusted_p_value=card_max_adjusted_p_value,
            output_dir=output_dir,
        )
    )
    workflow_report = result.report
    workflow_manifest = result.export_manifest
    if workflow_manifest is None:
        raise click.ClickException("workflow export manifest was not produced")

    _emit_json(
        {
            "accepted_rows": workflow_report.summary.accepted_evidence_count,
            "rejected_rows": workflow_report.summary.rejected_evidence_count,
            "feature_rows": workflow_report.summary.feature_row_count,
            "design_rows": workflow_report.summary.design_row_count,
            "workflow_report": workflow_report.to_dict(),
            "report": workflow_report.report.to_dict(),
            "workflow_export_manifest": workflow_manifest.to_dict(),
            "export_manifest": workflow_manifest.ptm_report_manifest.to_dict(),
            "outputs": result.outputs,
        },
        out_path=out_path,
    )


@ptm_group.command("summarize")
@click.argument(
    "evidence_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--features",
    "feature_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option(
    "--localization-score-column", default="localization_score", show_default=True
)
@click.option(
    "--localization-probability-column",
    default="localization_probability",
    show_default=True,
)
@click.option("--candidate-sites-column", default="candidate_sites", show_default=True)
@click.option("--decoy-label-column", default="decoy_label", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--site-separator", default=";", show_default=True)
@click.option("--threshold", type=float, default=0.05, show_default=True)
@click.option("--flank-size", type=int, default=7, show_default=True)
@click.option(
    "--site-quant-ambiguity-policy",
    type=click.Choice(
        [policy.value for policy in PtmSiteQuantAmbiguityPolicy], case_sensitive=False
    ),
    default=PtmSiteQuantAmbiguityPolicy.PRESERVE.value,
    show_default=True,
)
@click.option(
    "--occupancy-summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--occupancy-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--occupancy-counterpart-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_summarize_command(
    evidence_tsv: Path,
    proteins_fasta: Path,
    feature_path: Path | None,
    sample_column: str,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    protein_refs_column: str,
    q_value_column: str | None,
    localization_score_column: str,
    localization_probability_column: str | None,
    candidate_sites_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
    site_separator: str,
    threshold: float,
    flank_size: int,
    site_quant_ambiguity_policy: str,
    occupancy_summary_tsv_out: Path | None,
    occupancy_tsv_out: Path | None,
    occupancy_counterpart_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Summarize PTM site evidence from localized peptides and optional feature intensities."""
    try:
        if feature_path is None and any(
            output is not None
            for output in (
                occupancy_summary_tsv_out,
                occupancy_tsv_out,
                occupancy_counterpart_tsv_out,
            )
        ):
            raise click.ClickException(
                "occupancy TSV outputs require --features because occupancy depends on feature intensities"
            )
        mapping = PtmLocalizationColumnMapping(
            sample_id=sample_column,
            spectrum_id=spectrum_id_column,
            peptide=peptide_column,
            charge=charge_column,
            score=score_column,
                protein_refs=protein_refs_column,
                q_value=q_value_column,
                localization_score=localization_score_column,
                localization_probability=localization_probability_column,
                candidate_sites=candidate_sites_column,
                decoy_label=decoy_label_column,
                protein_separator=protein_separator,
            site_separator=site_separator,
        )
        evidence = parse_ptm_localization_tsv(evidence_tsv, mapping=mapping)
        fasta_report = parse_fasta_document(
            proteins_fasta.read_text(), mode=FastaParseMode.STRICT
        )
        if fasta_report.rejected_records:
            rejected = ", ".join(
                record.source_identifier for record in fasta_report.rejected_records
            )
            raise click.ClickException(
                f"FASTA input contains rejected records under strict mode: {rejected}"
            )
        protein_sequences = {
            record.canonical_accession: record.residues
            for record in fasta_report.accepted_records
        }
        mappings = map_ptm_evidence_to_protein_sites(
            evidence.accepted_records,
            protein_sequences=protein_sequences,
        )
        site_table = build_ptm_site_table(mappings)
        localization = build_ptm_localization_scoring_report(
            evidence.accepted_records
        )
        ambiguity_review = build_ptm_ambiguity_review_report(
            site_table,
            localization_scoring_report=localization,
            protein_sequences=protein_sequences,
        )
        coverage = build_ptm_site_coverage_report(mappings)
        fdr = build_ptm_site_fdr(site_table, threshold=threshold)
        motifs = build_ptm_motif_windows(
            site_table, protein_sequences=protein_sequences, flank_size=flank_size
        )
        enrichment = build_ptm_enrichment_input(
            site_table, protein_sequences=protein_sequences
        )
        occupancy_report = None
        occupancy_counterpart_report = None
        site_quantification = None
        site_group_quantification = None
        if feature_path is not None:
            feature_report = parse_ms1_feature_table(feature_path)
            occupancy_report = build_ptm_site_occupancy_report(
                site_table,
                feature_records=feature_report.accepted_records,
            )
            occupancy_counterpart_report = build_ptm_occupancy_counterpart_report(
                site_table,
                feature_records=feature_report.accepted_records,
            )
            site_quantification = build_ptm_site_quantification_report(
                site_table,
                feature_records=feature_report.accepted_records,
                ambiguity_policy=PtmSiteQuantAmbiguityPolicy(
                    site_quant_ambiguity_policy.lower()
                ),
            )
            site_group_quantification = build_ptm_site_group_quantification_report(
                site_table,
                feature_records=feature_report.accepted_records,
                localization_scoring_report=localization,
                protein_sequences=protein_sequences,
            )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if occupancy_summary_tsv_out is not None and occupancy_report is not None:
        occupancy_summary_tsv_out.write_text(
            render_ptm_site_occupancy_summary_tsv(occupancy_report),
            encoding="utf-8",
        )
    if occupancy_tsv_out is not None and occupancy_report is not None:
        occupancy_tsv_out.write_text(
            render_ptm_site_occupancy_entry_tsv(occupancy_report),
            encoding="utf-8",
        )
    if (
        occupancy_counterpart_tsv_out is not None
        and occupancy_counterpart_report is not None
    ):
        occupancy_counterpart_tsv_out.write_text(
            render_ptm_occupancy_counterpart_tsv(occupancy_counterpart_report),
            encoding="utf-8",
        )

    payload = {
        "accepted_rows": len(evidence.accepted_records),
        "rejected_rows": len(evidence.rejected_rows),
        "site_table": [entry.to_dict() for entry in site_table],
        "ambiguity_review": ambiguity_review.to_dict(),
        "coverage_report": [entry.to_dict() for entry in coverage],
        "fdr_report": fdr.to_dict(),
        "motif_windows": [entry.to_dict() for entry in motifs],
        "enrichment_input": enrichment.to_dict(),
        "occupancy": [entry.to_dict() for entry in occupancy_report.entries]
        if occupancy_report is not None
        else None,
        "occupancy_report": occupancy_report.to_dict()
        if occupancy_report is not None
        else None,
        "occupancy_counterpart_report": occupancy_counterpart_report.to_dict()
        if occupancy_counterpart_report is not None
        else None,
        "site_quantification": site_quantification.to_dict()
        if site_quantification is not None
        else None,
        "site_group_quantification": site_group_quantification.to_dict()
        if site_group_quantification is not None
        else None,
    }
    _emit_json(payload, out_path=out_path)


@cli.group("search-adapter")
def search_adapter_group() -> None:
    """Inspect and normalize search-engine-specific result tables."""


@search_adapter_group.command("inspect")
@click.option("--adapter", "adapter_name", type=_search_adapter_choice(), default=None)
def search_adapter_inspect_command(adapter_name: str | None) -> None:
    """Inspect one adapter manifest or the full capability matrix."""
    if adapter_name is None:
        payload = {
            "capabilities": [
                row.to_dict() for row in build_search_adapter_capability_matrix()
            ],
        }
        _emit_json(payload)
        return
    manifest = get_search_adapter_manifest(SearchAdapterKind(adapter_name))
    _emit_json(manifest)


@search_adapter_group.command("params")
@click.argument("adapter_name", type=_search_adapter_choice())
@click.argument(
    "config_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def search_adapter_params_command(
    adapter_name: str,
    config_path: Path,
    out_path: Path | None,
) -> None:
    """Parse one supported search-engine parameter file."""
    try:
        payload = parse_search_parameter_file(
            source_path=config_path,
            adapter_kind=SearchAdapterKind(adapter_name),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(payload, out_path=out_path)


@search_adapter_group.command("validate-config")
@click.argument("adapter_name", type=_search_adapter_choice())
@click.argument(
    "config_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def search_adapter_validate_config_command(
    adapter_name: str,
    config_path: Path,
    out_path: Path | None,
) -> None:
    """Validate one supported search-engine parameter file."""
    try:
        parameters = parse_search_parameter_file(
            source_path=config_path,
            adapter_kind=SearchAdapterKind(adapter_name),
        )
        payload = validate_search_parameters(parameters)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(payload, out_path=out_path)


@search_adapter_group.command("normalize")
@click.argument("adapter_name", type=_search_adapter_choice())
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mapping-json",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--adapter-version", default=None)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--jsonl-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--provenance-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON normalization output path.",
)
def search_adapter_normalize_command(
    adapter_name: str,
    input_path: Path,
    mapping_json: Path | None,
    adapter_version: str | None,
    config_path: Path | None,
    jsonl_out: Path | None,
    provenance_out: Path | None,
    out_path: Path | None,
) -> None:
    """Normalize one engine-specific search-result table into stable PSM records."""
    mapping = None
    if mapping_json is not None:
        mapping = SearchResultColumnMapping.model_validate_json(
            mapping_json.read_text()
        )
    try:
        report = normalize_search_results_with_adapter(
            source_path=input_path,
            adapter_kind=SearchAdapterKind(adapter_name),
            mapping=mapping,
        )
        provenance = build_search_adapter_provenance_manifest(
            source_path=input_path,
            normalization_report=report,
            adapter_version=adapter_version,
            config_path=config_path,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    if jsonl_out is not None:
        export_psm_jsonl(report.normalized_records, jsonl_out)
    if provenance_out is not None:
        provenance_out.write_text(provenance.to_stable_json() + "\n")
    payload = {
        "adapter": report.adapter_manifest.to_dict(),
        "accepted_rows": len(report.parse_report.accepted_records),
        "rejected_rows": len(report.parse_report.rejected_rows),
        "normalized_records": [
            record.to_dict() for record in report.normalized_records
        ],
        "provenance": provenance.to_dict(),
    }
    _emit_json(payload, out_path=out_path)


@search_adapter_group.command("compare")
@click.argument("left_adapter_name", type=_search_adapter_choice())
@click.argument(
    "left_input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument("right_adapter_name", type=_search_adapter_choice())
@click.argument(
    "right_input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--left-mapping-json",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--right-mapping-json",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def search_adapter_compare_command(
    left_adapter_name: str,
    left_input_path: Path,
    right_adapter_name: str,
    right_input_path: Path,
    left_mapping_json: Path | None,
    right_mapping_json: Path | None,
    out_path: Path | None,
) -> None:
    """Compare two normalized adapter outputs on a shared score scale."""
    left_mapping = (
        SearchResultColumnMapping.model_validate_json(left_mapping_json.read_text())
        if left_mapping_json is not None
        else None
    )
    right_mapping = (
        SearchResultColumnMapping.model_validate_json(right_mapping_json.read_text())
        if right_mapping_json is not None
        else None
    )
    try:
        left_report = normalize_search_results_with_adapter(
            source_path=left_input_path,
            adapter_kind=SearchAdapterKind(left_adapter_name),
            mapping=left_mapping,
        )
        right_report = normalize_search_results_with_adapter(
            source_path=right_input_path,
            adapter_kind=SearchAdapterKind(right_adapter_name),
            mapping=right_mapping,
        )
        payload = compare_search_result_reports(left_report, right_report)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(payload, out_path=out_path)


@search_adapter_group.command("conformance")
@click.argument("adapter_name", type=_search_adapter_choice())
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mapping-json",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def search_adapter_conformance_command(
    adapter_name: str,
    input_path: Path,
    mapping_json: Path | None,
    out_path: Path | None,
) -> None:
    """Run the built-in adapter conformance checks on one search-result table."""
    mapping = (
        SearchResultColumnMapping.model_validate_json(mapping_json.read_text())
        if mapping_json is not None
        else None
    )
    try:
        normalization_report = normalize_search_results_with_adapter(
            source_path=input_path,
            adapter_kind=SearchAdapterKind(adapter_name),
            mapping=mapping,
        )
        payload = build_search_adapter_conformance_report(normalization_report)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(payload, out_path=out_path)
