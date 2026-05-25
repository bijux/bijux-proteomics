# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import importlib
import os
from pathlib import Path
import subprocess
import sys


def _source_pythonpath() -> str:
    repo_root = Path(__file__).resolve().parents[4]
    src_roots = sorted(repo_root.glob("packages/*/src"))
    return ":".join(str(path) for path in src_roots)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _assert_clean_checkout_command_succeeds(statement: str) -> None:
    result = subprocess.run(
        [sys.executable, "-c", statement],
        capture_output=True,
        text=True,
        cwd=_repository_root(),
        env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
        check=False,
    )
    assert result.returncode == 0, result.stderr


def _assert_import_statement_succeeds_without_modules(
    statement: str, *blocked_modules: str
) -> None:
    blocked_list = ", ".join(repr(name) for name in blocked_modules)
    code = f"""
import builtins
import sys

blocked = ({blocked_list},)
original_import = builtins.__import__

def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    for blocked_name in blocked:
        if name == blocked_name or name.startswith(blocked_name + "."):
            raise ModuleNotFoundError(f"blocked import: {{blocked_name}}")
    return original_import(name, globals, locals, fromlist, level)

for module_name in list(sys.modules):
    for blocked_name in blocked:
        if module_name == blocked_name or module_name.startswith(blocked_name + "."):
            sys.modules.pop(module_name, None)

builtins.__import__ = guarded_import
{statement}
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": _source_pythonpath()},
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_core_package_import_contract() -> None:
    package = importlib.import_module("bijux_proteomics")

    assert package.__name__ == "bijux_proteomics"


def test_core_cli_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics.interfaces.cli")

    assert module.cli is not None


def test_core_package_import_contract_succeeds_from_clean_checkout() -> None:
    _assert_clean_checkout_command_succeeds("import bijux_proteomics")


def test_core_cli_import_contract_succeeds_from_clean_checkout() -> None:
    _assert_clean_checkout_command_succeeds(
        "from bijux_proteomics.interfaces.cli import cli"
    )


def test_core_package_import_contract_avoids_pydantic_at_root_import_time() -> None:
    _assert_import_statement_succeeds_without_modules(
        "import bijux_proteomics",
        "pydantic",
    )


def test_core_cli_import_contract_avoids_click_and_pydantic_at_import_time() -> None:
    _assert_import_statement_succeeds_without_modules(
        "from bijux_proteomics.interfaces.cli import cli",
        "click",
        "pydantic",
    )


def test_chemistry_package_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics.chemistry")

    assert hasattr(module, "load_modification_pack")
    assert hasattr(module, "ModificationPackValidationError")


def test_io_package_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics.io")

    assert hasattr(module, "compare_observed_to_library")
    assert hasattr(module, "deisotope_peaks")
    assert hasattr(module, "parse_mzml")
    assert hasattr(module, "estimate_peak_noise")
    assert hasattr(module, "render_spectral_library_intensity_agreement_tsv")
    assert hasattr(module, "score_spectrum_entropy")
    assert hasattr(module, "score_chromatographic_evidence")
    assert hasattr(module, "score_fragment_coelution")
    assert hasattr(module, "score_dia_fragment_trace_coelution")
    assert hasattr(module, "score_dia_fragment_ratio_stability")
    assert hasattr(module, "score_chimeric_spectra")
    assert hasattr(module, "extract_mzml_precursor_isotope_fit")
    assert hasattr(module, "extract_mzml_raw_signal_evidence_cards")
    assert hasattr(module, "build_targeted_fragment_ratio_stability_report")
    assert hasattr(module, "pick_peak")
    assert hasattr(module, "pick_chromatographic_peaks")
    assert hasattr(module, "score_peak_shape")
    assert hasattr(module, "fit_rt_alignment")
    assert hasattr(module, "apply_rt_residuals")
    assert hasattr(module, "align_chromatographic_peak_retention_times")
    assert hasattr(module, "extract_xic")
    assert hasattr(module, "extract_mzml_xic_traces")
    assert hasattr(module, "render_peak_shape_score_tsv")
    assert hasattr(module, "render_rt_alignment_fit_models_tsv")
    assert hasattr(module, "scan_input_integrity")
    assert hasattr(module, "render_input_integrity_issues_tsv")
    assert hasattr(module, "render_rt_residual_penalties_tsv")
    assert hasattr(module, "render_dia_fragment_trace_coelution_tsv")
    assert hasattr(module, "render_picked_chromatographic_peaks_tsv")
    assert hasattr(module, "render_xic_extraction_tsv")
    assert hasattr(module, "validate_precursor_isotope_charge")


def test_identification_package_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics.identification")

    assert hasattr(module, "extract_psm_features")
    assert hasattr(module, "fit_target_decoy_logistic_model")
    assert hasattr(module, "explain_rescored_psm")
    assert hasattr(module, "render_psm_rescoring_explanation_tsv")


def test_lab_package_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics.lab")

    assert hasattr(module, "build_lab_action_packets")
    assert hasattr(module, "build_internal_standard_sample_qc")
    assert hasattr(module, "check_cohort_balance")
    assert hasattr(module, "compare_samples_to_blanks")
    assert hasattr(module, "classify_contamination")
    assert hasattr(module, "classify_digestion")
    assert hasattr(module, "classify_run_failure")
    assert hasattr(module, "detect_sample_swaps")
    assert hasattr(module, "render_lab_action_packets_tsv")
    assert hasattr(module, "render_cohort_balance_tsv")
    assert hasattr(module, "render_internal_standard_tracking_tsv")
    assert hasattr(module, "render_sample_swap_suspicion_tsv")
    assert hasattr(module, "track_internal_standards")
    assert hasattr(module, "render_background_comparison_tsv")
    assert hasattr(module, "render_contamination_classification_tsv")
    assert hasattr(module, "render_digestion_diagnosis_tsv")
    assert hasattr(module, "render_run_diagnosis_tsv")


def test_ptm_package_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics.ptm")

    assert hasattr(module, "analyze_acetylation_sites")
    assert hasattr(module, "correct_site_by_protein")
    assert hasattr(module, "detect_ptm_hotspots")
    assert hasattr(module, "infer_kinases")
    assert hasattr(module, "infer_phosphatases")
    assert hasattr(module, "detect_oxidation_artifacts")
    assert hasattr(module, "test_occupancy_contrast")
    assert hasattr(module, "detect_false_localization")
    assert hasattr(module, "build_site_groups")
    assert hasattr(module, "render_acetylation_site_analysis_tsv")
    assert hasattr(module, "render_false_localization_tsv")
    assert hasattr(module, "render_ptm_hotspots_tsv")
    assert hasattr(module, "render_ptm_kinase_inference_tsv")
    assert hasattr(module, "render_ptm_oxidation_artifact_tsv")
    assert hasattr(module, "render_ptm_phosphatase_inference_tsv")
    assert hasattr(module, "render_ptm_occupancy_contrast_tsv")
    assert hasattr(module, "render_site_protein_correction_tsv")
    assert hasattr(module, "render_ptm_site_group_tsv")
    assert hasattr(module, "score_ptm_fragments")
    assert hasattr(module, "render_ptm_fragment_scores_tsv")


def test_proteoforms_package_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics.proteoforms")

    assert hasattr(module, "assemble_proteoform_candidates")
    assert hasattr(module, "quantify_supported_proteoforms")
    assert hasattr(module, "render_proteoform_candidate_tsv")
    assert hasattr(module, "render_proteoform_quantification_tsv")


def test_quantification_package_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics.quantification")

    assert hasattr(module, "build_label_free_intensity_table")
    assert hasattr(module, "bootstrap_effect_stability")
    assert hasattr(module, "compare_quant_methods")
    assert hasattr(module, "detect_compositional_bias")
    assert hasattr(module, "compare_imputation_policies")
    assert hasattr(module, "estimate_sample_weights")
    assert hasattr(module, "fit_peptide_bias_model")
    assert hasattr(module, "test_protein_effect_from_peptides")
    assert hasattr(module, "render_bootstrap_effect_stability_tsv")
    assert hasattr(module, "render_compositional_bias_tsv")
    assert hasattr(module, "render_quant_matrix_archive_tsv")
    assert hasattr(module, "render_quant_method_agreement_tsv")
    assert hasattr(module, "render_protein_abundance_tsv")
    assert hasattr(module, "render_imputation_policy_comparison_tsv")
    assert hasattr(module, "render_sample_reliability_weights_tsv")
    assert hasattr(module, "render_peptide_level_differential_tsv")
    assert hasattr(module, "render_peptide_bias_tsv")
    assert hasattr(module, "render_rollup_residuals_tsv")
    assert hasattr(module, "classify_missingness")
    assert hasattr(module, "estimate_protein_uncertainty")
    assert hasattr(module, "fit_mean_variance_trend")
    assert hasattr(module, "test_censored_two_group")
    assert hasattr(module, "render_missingness_classification_tsv")
    assert hasattr(module, "render_censored_differential_tsv")
    assert hasattr(module, "render_mean_variance_trend_tsv")
    assert hasattr(module, "render_protein_uncertainty_tsv")
    assert hasattr(module, "save_matrix_archive")
    assert hasattr(module, "load_matrix_archive")


def test_sequences_package_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics.sequences")

    assert hasattr(module, "build_protein_index")
    assert hasattr(module, "load_protein_index")
    assert hasattr(module, "lookup_accession")
    assert hasattr(module, "lookup_peptide_entry")
    assert hasattr(module, "lookup_peptide_proteins")
    assert hasattr(module, "lookup_protein_peptides")
    assert hasattr(module, "lookup_protein_sequence")


def test_study_package_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics.study")

    assert hasattr(module, "detect_carryover")
    assert hasattr(module, "detect_batch_condition_confounding")
    assert hasattr(module, "detect_lc_drift")
    assert hasattr(module, "render_carryover_detection_tsv")
    assert hasattr(module, "render_batch_condition_confounding_tsv")
    assert hasattr(module, "render_lc_drift_tsv")
    assert hasattr(module, "build_run_qc_assessment")


def test_interpretation_ppi_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics.interpretation")

    assert hasattr(module, "build_ppi_network_module_report")
    assert hasattr(module, "load_annotation_pack")
    assert hasattr(module, "AnnotationPackValidationError")


def test_workflow_package_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics.workflow")

    assert hasattr(module, "AdvancedDiannWorkflowConfig")
    assert hasattr(module, "AdvancedFragpipeWorkflowConfig")
    assert hasattr(module, "AdvancedMaxquantWorkflowConfig")
    assert hasattr(module, "AdvancedPtmWorkflowConfig")
    assert hasattr(module, "TargetedValidationWorkflowConfig")
    assert hasattr(module, "AdvancedTmtWorkflowConfig")
    assert hasattr(module, "DiscoveryAssaySourceResult")
    assert hasattr(module, "DiscoveryAssayTargetInput")
    assert hasattr(module, "run_proteomics_workflow")
    assert hasattr(module, "run_advanced_diann_workflow")
    assert hasattr(module, "run_advanced_fragpipe_workflow")
    assert hasattr(module, "run_advanced_maxquant_workflow")
    assert hasattr(module, "run_advanced_ptm_workflow")
    assert hasattr(module, "run_targeted_validation_workflow")
    assert hasattr(module, "run_advanced_tmt_workflow")
    assert hasattr(module, "design_assay_from_discovery")
    assert hasattr(module, "load_result_archive")
    assert hasattr(module, "load_public_benchmark_descriptor")
    assert hasattr(module, "build_public_benchmark_subset")
    assert hasattr(module, "generate_quant_truth_dataset")
    assert hasattr(module, "build_interactive_result_bundle_from_artifacts")
    assert hasattr(module, "build_interactive_result_comparison_from_artifacts")
    assert hasattr(module, "build_result_manifest_from_artifacts")
    assert hasattr(module, "build_result_search_index_from_artifacts")


def test_review_package_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics.review")

    assert hasattr(module, "build_analysis_recommendation_report_from_artifacts")
    assert hasattr(module, "build_belief_audit_report_from_artifacts")
    assert hasattr(module, "build_compact_result_summary_report_from_artifacts")
    assert hasattr(module, "build_failure_explanation_report")
    assert hasattr(module, "build_biological_claim_validation_report")
    assert hasattr(module, "build_biological_hypothesis_report")
    assert hasattr(module, "build_biomarker_candidate_ranking_report")
    assert hasattr(module, "build_result_explanation_report_from_artifacts")
    assert hasattr(module, "build_result_query_report_from_artifacts")


def test_targeted_package_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics.targeted")

    assert hasattr(module, "build_panel_redundancy_report")
    assert hasattr(module, "build_discovery_targeted_peptide_selection_report")
    assert hasattr(module, "build_targeted_assay_interference_report")
    assert hasattr(module, "build_biomarker_stability_report")
    assert hasattr(module, "build_validation_evidence_card_report")
    assert hasattr(module, "build_targeted_panel_design_report")
    assert hasattr(module, "build_targeted_result_validation_report")
    assert hasattr(module, "score_fragment_ratio_drift")
    assert hasattr(module, "render_fragment_ratio_drift_tsv")
    assert hasattr(module, "build_targeted_transition_selection_report")
    assert hasattr(module, "score_transition_coelution")
    assert hasattr(module, "render_transition_coelution_tsv")
    assert hasattr(module, "build_validation_experiment_planning_report")
