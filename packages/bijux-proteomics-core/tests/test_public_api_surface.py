# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import bijux_proteomics
import bijux_proteomics_intelligence
import bijux_proteomics_knowledge
import bijux_proteomics_lab


def test_core_public_api_contains_expected_exports() -> None:
    assert "ProgramSpec" in bijux_proteomics.__all__
    assert "ExecutionBackend" in bijux_proteomics.__all__
    assert "ProteinSequence" in bijux_proteomics.__all__
    assert "FastaParseReport" in bijux_proteomics.__all__
    assert "generate_decoy_records" in bijux_proteomics.__all__
    assert "validate_target_decoy_database" in bijux_proteomics.__all__
    assert "digest_sequence" in bijux_proteomics.__all__
    assert "protease_registry" in bijux_proteomics.__all__
    assert "build_peptide_protein_index" in bijux_proteomics.__all__
    assert "calculate_monoisotopic_peptide_mass" in bijux_proteomics.__all__
    assert "calculate_fragment_ions" in bijux_proteomics.__all__
    assert "modification_registry" in bijux_proteomics.__all__
    assert "canonicalize_modified_peptide" in bijux_proteomics.__all__
    assert "build_peptide_charge_state" in bijux_proteomics.__all__
    assert "approximate_peptide_isotope_envelope" in bijux_proteomics.__all__
    assert "PsmRecord" in bijux_proteomics.__all__
    assert "parse_psm_tsv" in bijux_proteomics.__all__
    assert "rollup_protein_evidence" in bijux_proteomics.__all__
    assert "filter_psms_by_fdr" in bijux_proteomics.__all__
    assert "build_fdr_audit_trail" in bijux_proteomics.__all__
    assert "compute_fdr_reproducibility_hash" in bijux_proteomics.__all__
    assert "normalize_psm_score_orientation" in bijux_proteomics.__all__
    assert "calculate_level_specific_fdr" in bijux_proteomics.__all__
    assert "calculate_grouped_fdr" in bijux_proteomics.__all__
    assert "calculate_picked_protein_fdr" in bijux_proteomics.__all__
    assert "build_protein_groups" in bijux_proteomics.__all__
    assert "infer_proteins_by_parsimony" in bijux_proteomics.__all__
    assert "assign_razor_peptides" in bijux_proteomics.__all__
    assert "build_protein_coverage_map" in bijux_proteomics.__all__
    assert "build_peptide_uniqueness_across_database" in bijux_proteomics.__all__
    assert "assign_confidence_labels" in bijux_proteomics.__all__
    assert "build_search_result_provenance_manifest" in bijux_proteomics.__all__
    assert "export_psm_tsv" in bijux_proteomics.__all__
    assert "SpectrumModel" in bijux_proteomics.__all__
    assert "parse_mgf" in bijux_proteomics.__all__
    assert "annotate_spectrum_fragments" in bijux_proteomics.__all__
    assert "calculate_spectral_similarity" in bijux_proteomics.__all__
    assert "build_spectrum_provenance_manifest" in bijux_proteomics.__all__
    assert "parse_mzml" in bijux_proteomics.__all__
    assert "detect_proteomics_format" in bijux_proteomics.__all__
    assert "build_normalized_run_bundle" in bijux_proteomics.__all__
    assert "normalize_search_results_with_adapter" in bijux_proteomics.__all__
    assert "build_search_adapter_capability_matrix" in bijux_proteomics.__all__
    assert "parse_search_parameter_file" in bijux_proteomics.__all__
    assert "validate_search_parameters" in bijux_proteomics.__all__
    assert "compare_search_result_reports" in bijux_proteomics.__all__
    assert "build_search_adapter_conformance_report" in bijux_proteomics.__all__
    assert "SearchAdapterKind" in bijux_proteomics.__all__
    assert "Ms1FeatureRecord" in bijux_proteomics.__all__
    assert "parse_ms1_feature_table" in bijux_proteomics.__all__
    assert "build_label_free_intensity_table" in bijux_proteomics.__all__
    assert "build_spectral_count_table" in bijux_proteomics.__all__
    assert "normalize_label_free_table" in bijux_proteomics.__all__
    assert "build_batch_effect_advisory" in bijux_proteomics.__all__
    assert "build_replicate_correlation_report" in bijux_proteomics.__all__
    assert "build_differential_abundance_report" in bijux_proteomics.__all__
    assert "apply_benjamini_hochberg" in bijux_proteomics.__all__
    assert "PtmEvidenceRecord" in bijux_proteomics.__all__
    assert "parse_ptm_localization_tsv" in bijux_proteomics.__all__
    assert "map_ptm_evidence_to_protein_sites" in bijux_proteomics.__all__
    assert "build_ptm_site_table" in bijux_proteomics.__all__
    assert "build_ptm_site_fdr" in bijux_proteomics.__all__
    assert "estimate_ptm_site_occupancy" in bijux_proteomics.__all__
    assert "build_lcms_run_qc_report" in bijux_proteomics.__all__
    assert "build_instrument_batch_qc_report" in bijux_proteomics.__all__
    assert "LcmsRunQcReport" in bijux_proteomics.__all__
    assert "InstrumentBatchQcReport" in bijux_proteomics.__all__


def test_intelligence_public_api_contains_expected_exports() -> None:
    assert "RankingPolicy" in bijux_proteomics_intelligence.__all__
    assert "ScenarioEvaluation" in bijux_proteomics_intelligence.__all__
    assert "CandidateRejection" in bijux_proteomics_intelligence.__all__


def test_knowledge_public_api_contains_expected_exports() -> None:
    assert "EvidenceClaim" in bijux_proteomics_knowledge.__all__
    assert "ResolutionAction" in bijux_proteomics_knowledge.__all__
    assert "EvidenceGraph" in bijux_proteomics_knowledge.__all__


def test_lab_public_api_contains_expected_exports() -> None:
    assert "ScheduledPlan" in bijux_proteomics_lab.__all__
    assert "AssayOutcome" in bijux_proteomics_lab.__all__
    assert "AssayDependency" in bijux_proteomics_lab.__all__
