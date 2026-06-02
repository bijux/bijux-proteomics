# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics_foundation.testing.source_tree_complexity import (
    SourceFunctionComplexityException,
    build_source_tree_complexity_report,
)

pytestmark = [pytest.mark.governance, pytest.mark.slow]

CORE_SRC_ROOT = Path("packages/bijux-proteomics-core/src/bijux_proteomics")
COMPLEXITY_CEILING = 25


def _temporary_reason(relative_path: str) -> str:
    if relative_path.startswith("interfaces/python_api/"):
        return "python api command owners still mix orchestration, validation, and report assembly that need narrower boundaries."
    if relative_path.startswith("workflow/"):
        return "workflow owners still combine cross-study synthesis, report assembly, and publication surfaces that need narrower modules."
    if relative_path.startswith("targeted/"):
        return "targeted owners still combine assay scoring, QC, stability, and validation policy that need narrower modules."
    if relative_path.startswith("quantification/"):
        return "quantification owners still combine parsing, matrix assembly, imputation, and statistical reporting that need narrower modules."
    if relative_path.startswith("lab/"):
        return "lab support inside core still combines run-status classification and QC report assembly that need narrower modules."
    if relative_path.startswith("io/"):
        return "io owners still combine table parsing, mzML decoding, and spectrum QC reporting that need narrower modules."
    if relative_path.startswith("ptm/"):
        return "ptm owners still combine parsing, occupancy, quantification, and mechanism classification that need narrower modules."
    if relative_path.startswith("multiplex/"):
        return "multiplex owners still combine import, ratio analysis, and reporter-matrix assembly that need narrower modules."
    if relative_path.startswith("dia/"):
        return "dia owners still combine precursor matrices, transition QC, and run-QC report assembly that need narrower modules."
    if relative_path.startswith("identification/"):
        return "identification owners still combine row parsing, evidence assembly, and benchmark reporting that need narrower modules."
    if relative_path.startswith("sequences/"):
        return "sequence owners still combine parsing and region-context report assembly that need narrower modules."
    if relative_path.startswith("domain/"):
        return "domain owners still combine validation, geometry, and structure policy that need narrower modules."
    if relative_path.startswith("interpretation/"):
        return "interpretation owners still combine enrichment and protein-set projection logic that need narrower modules."
    return "temporary complexity allowance for a core scientific owner that still needs narrower boundaries."


def _exception(
    relative_path: str,
    qualified_name: str,
    allowed_complexity: int,
) -> SourceFunctionComplexityException:
    return SourceFunctionComplexityException(
        relative_path=relative_path,
        qualified_name=qualified_name,
        allowed_complexity=allowed_complexity,
        temporary_reason=_temporary_reason(relative_path),
    )


CORE_COMPLEXITY_EXCEPTIONS = (
    _exception("_scientific_tables.py", "_schema_row_issues", 36),
    _exception("dia/precursor_matrix.py", "build_dia_precursor_matrix_report", 34),
    _exception("dia/run_qc.py", "build_dia_run_qc_report", 37),
    _exception("dia/transition_qc.py", "build_transition_qc_report", 32),
    _exception("domain/structure/structure.py", "kabsch_and_pairs", 29),
    _exception("domain/validation.py", "validate_program_readiness", 77),
    _exception("identification/contracts/psm_io.py", "_parse_psm_row", 33),
    _exception(
        "identification/peptide/peptide_evidence.py",
        "build_peptide_evidence_report",
        27,
    ),
    _exception(
        "identification/protein/protein_inference_benchmarks.py",
        "build_protein_inference_benchmark_report",
        26,
    ),
    _exception(
        "identification/search_adapters/engines/sage.py",
        "parse_sage_parameters",
        34,
    ),
    _exception(
        "interfaces/python_api/differential_analysis.py",
        "run_dia_differential_command",
        34,
    ),
    _exception(
        "interfaces/python_api/isotope_labeling.py",
        "run_silac_differential_command",
        27,
    ),
    _exception(
        "interfaces/python_api/multiplex_analysis.py",
        "run_tmt_differential_command",
        27,
    ),
    _exception(
        "interfaces/python_api/qc_commands.py",
        "run_qc_report_command",
        26,
    ),
    _exception(
        "interfaces/python_api/quantify_runner.py",
        "run_quantify_command",
        120,
    ),
    _exception(
        "interfaces/python_api/targeted_matrix_qc.py",
        "run_targeted_assay_qc_command",
        31,
    ),
    _exception(
        "interpretation/protein_set_enrichment.py",
        "build_protein_set_enrichment_report",
        26,
    ),
    _exception(
        "io/chromatography/dia_fragment_coelution.py",
        "score_dia_fragment_trace_coelution",
        32,
    ),
    _exception("io/raw/mzml_reader.py", "_parse_binary_values", 29),
    _exception("io/raw/mzml_reader.py", "_parse_spectrum_element", 45),
    _exception(
        "io/raw/raw_signal_evidence_cards.py",
        "build_raw_signal_evidence_card_report",
        27,
    ),
    _exception("io/raw/run_qc.py", "build_spectrum_run_qc_report", 38),
    _exception("io/tables/target_panel.py", "_parse_target_panel_row", 27),
    _exception("io/tables/transition_table.py", "_parse_transition_row", 29),
    _exception("lab/qc.py", "_build_run_status_reasons", 37),
    _exception("lab/qc.py", "build_lcms_run_qc_report", 55),
    _exception("multiplex/ratio_analysis.py", "build_tmt_ratio_report", 42),
    _exception(
        "multiplex/reporter_ion_import.py",
        "parse_tmt_reporter_table",
        43,
    ),
    _exception(
        "multiplex/reporter_matrix.py",
        "build_tmt_reporter_feature_bundle",
        27,
    ),
    _exception("ptm/contracts.py", "parse_ptm_localization_tsv", 36),
    _exception(
        "ptm/quant/occupancy_estimation.py",
        "build_ptm_site_occupancy_report",
        29,
    ),
    _exception(
        "ptm/quant/site_quantification.py",
        "build_ptm_site_quantification_report",
        34,
    ),
    _exception(
        "ptm/regulation/mechanism_classification.py",
        "_classify_mechanism_entry",
        28,
    ),
    _exception(
        "ptm/sites/ortholog_site_conservation.py",
        "parse_ptm_ortholog_site_tsv",
        27,
    ),
    _exception(
        "quantification/contracts/input_parsing.py",
        "_parse_ms1_feature_row",
        30,
    ),
    _exception(
        "quantification/contracts/input_parsing.py",
        "_parse_precursor_intensity_row",
        30,
    ),
    _exception(
        "quantification/matrix/peptide_intensity_matrix.py",
        "PeptideIntensityMatrixReport.from_quant_matrix",
        38,
    ),
    _exception(
        "quantification/matrix/protein_intensity_matrix.py",
        "build_protein_intensity_matrix_from_peptides",
        40,
    ),
    _exception(
        "quantification/missingness/missingness.py",
        "build_missing_data_mechanism_report",
        26,
    ),
    _exception(
        "quantification/normalization/imputation.py",
        "build_imputation_sensitivity_report",
        47,
    ),
    _exception(
        "quantification/normalization/normalization.py",
        "_normalize_intensity_matrix_pure",
        31,
    ),
    _exception(
        "quantification/provenance/review.py",
        "build_quant_review_bundle",
        36,
    ),
    _exception(
        "quantification/statistics/differential_abundance.py",
        "build_differential_abundance_report",
        48,
    ),
    _exception(
        "sequences/protein_region_context.py",
        "parse_protein_region_context_tsv",
        31,
    ),
    _exception(
        "sequences/protein_region_context.py",
        "build_protein_site_region_context_report",
        26,
    ),
    _exception(
        "sequences/protein_region_context.py",
        "build_protein_peptide_region_context_report",
        29,
    ),
    _exception("study/design/experiment_design.py", "build_experiment_design", 27),
    _exception(
        "targeted/assay_interference.py",
        "build_targeted_assay_interference_report",
        30,
    ),
    _exception("targeted/assay_qc.py", "build_targeted_assay_qc_report", 84),
    _exception("targeted/biomarker_stability.py", "_build_candidate_entry", 39),
    _exception(
        "targeted/transition_coelution.py",
        "build_targeted_transition_coelution_report",
        43,
    ),
    _exception(
        "targeted/validation_evidence_cards.py",
        "build_validation_evidence_card_report",
        31,
    ),
    _exception(
        "workflow/cross_species_effect_comparison.py",
        "build_cross_species_effect_comparison_report_from_observations",
        27,
    ),
    _exception(
        "workflow/cross_study_meta_analysis.py",
        "_build_meta_analysis_entry",
        31,
    ),
    _exception(
        "workflow/cross_study_pathway_comparison.py",
        "_build_pathway_comparison_entry",
        26,
    ),
    _exception(
        "workflow/cross_study_protein_harmonization.py",
        "build_cross_study_protein_harmonization_report_from_observations",
        35,
    ),
    _exception(
        "workflow/pipelines/dia_dda_comparison.py",
        "build_dia_dda_comparison_report",
        31,
    ),
    _exception(
        "workflow/public_dataset_comparison.py",
        "build_public_dataset_comparison_report_from_suite",
        26,
    ),
    _exception(
        "workflow/reports/biological_report_assembly.py",
        "build_biological_result_report_bundle_from_quant_table",
        60,
    ),
    _exception(
        "workflow/reports/biological_report_section_confidence.py",
        "_build_biological_report_section_confidence_entries",
        68,
    ),
)


def test_core_source_tree_respects_complexity_ceiling() -> None:
    report = build_source_tree_complexity_report(
        CORE_SRC_ROOT,
        ceiling=COMPLEXITY_CEILING,
        exceptions=CORE_COMPLEXITY_EXCEPTIONS,
        exclude_marked_generated=True,
    )

    assert report.stale_exceptions == ()
    assert report.unexpected_over_ceiling == ()
    assert tuple(
        (item.relative_path, item.qualified_name) for item in report.approved_over_ceiling
    ) == tuple(
        (item.relative_path, item.qualified_name)
        for item in CORE_COMPLEXITY_EXCEPTIONS
    )
