# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics.identification.search_adapters import (
    ScoreOrientation,
    SearchAdapterDialectManifest,
    SearchAdapterFieldAccounting,
    SearchAdapterKind,
    SearchInputRefusalKind,
    SearchNormalizedEvidenceEntry,
    SearchRegressionFixtureKind,
    SearchResultColumnMapping,
    SearchResultFamily,
    SearchScoreFamily,
    assess_search_result_input,
    build_search_adapter_capability_matrix,
    build_search_adapter_conformance_report,
    build_search_adapter_provenance_manifest,
    build_search_adapter_regression_corpus_manifest,
    build_search_result_family_policy,
    compare_search_parameters,
    compare_search_result_reports,
    get_search_adapter_manifest,
    merge_search_result_reports,
    normalize_search_results_with_adapter,
    parse_search_parameter_file,
    search_adapter_dialect_registry,
    validate_search_parameters,
)


def _fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent / "fixtures" / "search_adapters" / name
    )


def test_search_adapter_registry_exposes_capability_matrix() -> None:
    matrix = build_search_adapter_capability_matrix()
    by_kind = {row.adapter_kind: row for row in matrix}

    assert SearchAdapterKind.COMET in by_kind
    assert (
        by_kind[SearchAdapterKind.COMET].score_orientation
        is ScoreOrientation.LOWER_BETTER
    )
    assert (
        by_kind[SearchAdapterKind.COMET].score_family
        is SearchScoreFamily.EXPECTATION_VALUE
    )
    assert (
        by_kind[SearchAdapterKind.DIANN].result_family
        is SearchResultFamily.MIXED_TARGET_LIBRARY
    )
    assert by_kind[SearchAdapterKind.SAGE].supports_q_value is True
    assert by_kind[SearchAdapterKind.GENERIC].supports_config_hash is True


def test_search_adapter_regression_corpus_manifest_covers_engine_like_and_failure_fixtures() -> (
    None
):
    manifest = build_search_adapter_regression_corpus_manifest(_fixture(""))

    assert SearchAdapterKind.COMET in manifest.covered_adapter_kinds
    assert SearchAdapterKind.SAGE in manifest.covered_adapter_kinds
    assert manifest.engine_export_like_count >= 8
    assert manifest.failure_case_count >= 2
    assert any(
        entry.fixture_kind is SearchRegressionFixtureKind.PIPELINE_EXPORT
        for entry in manifest.entries
    )


def test_search_adapter_extension_dialect_normalizes_without_core_rewrites() -> None:
    dialect = SearchAdapterDialectManifest(
        adapter_kind=SearchAdapterKind.SAGE,
        dialect_id="pipeline-export",
        display_name="Sage pipeline export",
        description="Normalize a Sage-like pipeline export with renamed score fields.",
        native_columns=(
            "scan_id",
            "stripped_peptide",
            "precursor_charge",
            "score_discriminant",
            "protein_group",
            "decoy_flag",
            "qvalue",
        ),
        mapping=SearchResultColumnMapping(
            spectrum_id="scan_id",
            peptide="stripped_peptide",
            charge="precursor_charge",
            score="score_discriminant",
            protein_refs="protein_group",
            q_value="qvalue",
            decoy_label="decoy_flag",
            protein_separator=";",
        ),
    )

    report = normalize_search_results_with_adapter(
        source_path=_fixture("sage_pipeline_export.tsv"),
        adapter_kind=SearchAdapterKind.SAGE,
        dialect_id="pipeline-export",
        additional_dialects=(dialect,),
    )

    assert report.adapter_manifest.display_name == "Sage pipeline export"
    assert report.normalized_records[0].canonical_peptide == "PEPTIDE"
    assert report.normalized_records[1].target_decoy_label.value == "decoy"


def test_built_in_pipeline_dialects_cover_richer_engine_like_outputs() -> None:
    registry = search_adapter_dialect_registry()
    reports = {
        "comet": normalize_search_results_with_adapter(
            source_path=_fixture("comet_pipeline_export.tsv"),
            adapter_kind=SearchAdapterKind.COMET,
            dialect_id="pipeline-export",
        ),
        "msfragger": normalize_search_results_with_adapter(
            source_path=_fixture("msfragger_pipeline_export.tsv"),
            adapter_kind=SearchAdapterKind.MSFRAGGER,
            dialect_id="pipeline-export",
        ),
        "sage": normalize_search_results_with_adapter(
            source_path=_fixture("sage_pipeline_export.tsv"),
            adapter_kind=SearchAdapterKind.SAGE,
            dialect_id="pipeline-export",
        ),
        "maxquant": normalize_search_results_with_adapter(
            source_path=_fixture("maxquant_pipeline_export.tsv"),
            adapter_kind=SearchAdapterKind.MAXQUANT_EVIDENCE,
            dialect_id="pipeline-export",
        ),
        "diann": normalize_search_results_with_adapter(
            source_path=_fixture("diann_pipeline_export.tsv"),
            adapter_kind=SearchAdapterKind.DIANN,
            dialect_id="pipeline-export",
        ),
        "spectronaut": normalize_search_results_with_adapter(
            source_path=_fixture("spectronaut_pipeline_export.tsv"),
            adapter_kind=SearchAdapterKind.SPECTRONAUT,
            dialect_id="pipeline-export",
        ),
    }

    assert (
        registry[(SearchAdapterKind.COMET, "pipeline-export")].display_name
        == "Comet pipeline export"
    )
    assert reports["comet"].normalized_records[0].canonical_peptide == "PEPTIDE"
    assert reports["msfragger"].normalized_records[0].score == 132.4
    assert reports["sage"].normalized_records[0].q_value == 0.001
    assert reports["maxquant"].normalized_records[1].target_decoy_label.value == "decoy"
    assert (
        reports["maxquant"].normalized_records[0].posterior_error_probability == 0.001
    )
    assert reports["maxquant"].normalized_records[0].q_value is None
    assert reports["diann"].normalized_records[0].q_value == 0.002
    assert reports["spectronaut"].normalized_records[0].protein_refs == (
        "P12345",
        "Q33333",
    )


def test_normalization_report_preserves_raw_engine_evidence_rows() -> None:
    report = normalize_search_results_with_adapter(
        source_path=_fixture("sage_results.tsv"),
        adapter_kind=SearchAdapterKind.SAGE,
    )

    accepted_row = next(row for row in report.evidence_rows if row.accepted)
    assert isinstance(accepted_row, SearchNormalizedEvidenceEntry)
    assert report.source_columns[0] == "scannr"
    assert accepted_row.raw_fields["proteins"] == "P12345"
    assert accepted_row.mapped_field_values["score"] == "15.2"
    assert accepted_row.unmapped_native_fields == {}
    assert accepted_row.normalized_record is not None
    assert (
        report.family_policy.result_family is SearchResultFamily.DATABASE_TARGET_DECOY
    )


def test_engine_specific_adapters_normalize_psm_contracts() -> None:
    comet = normalize_search_results_with_adapter(
        source_path=_fixture("comet_results.tsv"),
        adapter_kind=SearchAdapterKind.COMET,
    )
    fragger = normalize_search_results_with_adapter(
        source_path=_fixture("msfragger_results.tsv"),
        adapter_kind=SearchAdapterKind.MSFRAGGER,
    )
    sage = normalize_search_results_with_adapter(
        source_path=_fixture("sage_results.tsv"),
        adapter_kind=SearchAdapterKind.SAGE,
    )
    maxquant = normalize_search_results_with_adapter(
        source_path=_fixture("maxquant_evidence.tsv"),
        adapter_kind=SearchAdapterKind.MAXQUANT_EVIDENCE,
    )
    diann = normalize_search_results_with_adapter(
        source_path=_fixture("diann_report.tsv"),
        adapter_kind=SearchAdapterKind.DIANN,
    )
    spectronaut = normalize_search_results_with_adapter(
        source_path=_fixture("spectronaut_report.tsv"),
        adapter_kind=SearchAdapterKind.SPECTRONAUT,
    )

    assert comet.normalized_records[0].spectrum_id == "comet-1"
    assert comet.normalized_records[1].target_decoy_label.value == "decoy"
    assert fragger.normalized_records[0].score == 125.0
    assert sage.normalized_records[0].q_value == 0.002
    assert maxquant.normalized_records[1].target_decoy_label.value == "decoy"
    assert maxquant.normalized_records[0].posterior_error_probability == 0.001
    assert maxquant.normalized_records[0].q_value is None
    diann_by_id = {record.spectrum_id: record for record in diann.normalized_records}
    assert diann_by_id["run1_PEPTIDE_2"].q_value == 0.003
    assert spectronaut.normalized_records[0].protein_refs == ("P12345", "Q22222")


def test_generic_adapter_and_provenance_manifest_are_stable() -> None:
    mapping = SearchResultColumnMapping.model_validate_json(
        _fixture("generic_mapping.json").read_text()
    )
    generic = normalize_search_results_with_adapter(
        source_path=_fixture("generic_results.tsv"),
        adapter_kind=SearchAdapterKind.GENERIC,
        mapping=mapping,
    )
    provenance = build_search_adapter_provenance_manifest(
        source_path=_fixture("sage_results.tsv"),
        normalization_report=normalize_search_results_with_adapter(
            source_path=_fixture("sage_results.tsv"),
            adapter_kind=SearchAdapterKind.SAGE,
        ),
        adapter_version="0.16.0",
        config_path=_fixture("sage_search.json"),
    )

    assert generic.normalized_records[0].canonical_peptide == "PEPTIDE"
    assert generic.normalized_records[1].target_decoy_label.value == "decoy"
    assert provenance.adapter_kind is SearchAdapterKind.SAGE
    assert provenance.adapter_version == "0.16.0"
    assert provenance.config_sha256
    assert provenance.parameter_report is not None
    assert provenance.parameter_report.decoy_prefix == "DECOY_"
    assert provenance.result_family is SearchResultFamily.DATABASE_TARGET_DECOY
    assert provenance.parse_provenance.column_mapping.spectrum_id == "scannr"


def test_built_in_manifests_are_self_describing() -> None:
    manifest = get_search_adapter_manifest(SearchAdapterKind.MAXQUANT_EVIDENCE)
    rendered = json.loads(manifest.to_stable_json())

    assert manifest.display_name == "MaxQuant evidence"
    assert "Modified sequence" in manifest.native_columns
    assert rendered["adapter_kind"] == "maxquant-evidence"
    assert manifest.score_family is SearchScoreFamily.ENGINE_SCORE
    assert manifest.mapping is not None
    assert manifest.mapping.posterior_error_probability == "PEP"
    assert manifest.mapping.q_value is None
    assert manifest.supports_q_value is False


def test_search_parameter_parsers_extract_enzyme_tolerances_and_mods() -> None:
    comet = parse_search_parameter_file(
        source_path=_fixture("comet.params"),
        adapter_kind=SearchAdapterKind.COMET,
    )
    fragger = parse_search_parameter_file(
        source_path=_fixture("msfragger.params"),
        adapter_kind=SearchAdapterKind.MSFRAGGER,
    )
    sage = parse_search_parameter_file(
        source_path=_fixture("sage_search.json"),
        adapter_kind=SearchAdapterKind.SAGE,
    )

    assert comet.enzyme == "trypsin"
    assert comet.precursor_tolerance_unit is not None
    assert comet.precursor_tolerance_unit.value == "ppm"
    assert comet.fixed_modifications[0].site == "C"
    assert fragger.fragment_tolerance == 20.0
    assert fragger.decoy_prefix == "DECOY_"
    assert sage.variable_modifications[0].site == "M"
    assert sage.has_decoy_strategy is True


def test_compact_sage_config_shapes_still_produce_parameter_provenance() -> None:
    sage = parse_search_parameter_file(
        source_path=_fixture("sage_config.json"),
        adapter_kind=SearchAdapterKind.SAGE,
    )

    assert sage.enzyme == "trypsin"
    assert sage.fragment_tolerance == 20.0
    assert sage.precursor_tolerance == 10.0
    assert {entry.site for entry in sage.variable_modifications} == {"S", "T", "Y"}


def test_search_config_validation_flags_missing_decoys_and_invalid_tolerances() -> None:
    invalid = parse_search_parameter_file(
        source_path=_fixture("comet_invalid.params"),
        adapter_kind=SearchAdapterKind.COMET,
    )
    report = validate_search_parameters(invalid)

    assert report.valid is False
    codes = {issue.code for issue in report.issues}
    assert {
        "unknown_enzyme",
        "missing_decoy_strategy",
        "invalid_precursor_tolerance",
        "invalid_fragment_tolerance",
        "overlapping_modification_definition",
    } <= codes


def test_search_parameter_comparison_reports_engine_assumption_differences() -> None:
    comet = parse_search_parameter_file(
        source_path=_fixture("comet.params"),
        adapter_kind=SearchAdapterKind.COMET,
    )
    fragger = parse_search_parameter_file(
        source_path=_fixture("msfragger.params"),
        adapter_kind=SearchAdapterKind.MSFRAGGER,
    )

    comparison = compare_search_parameters(comet, fragger)

    assert comparison.comparable is False
    differences = {entry.field_name: entry for entry in comparison.differences}
    assert differences["enzyme"].severity == "compatible"
    assert differences["fragment_tolerance"].severity == "different"
    assert differences["variable_modifications"].severity == "different"


def test_search_input_assessment_classifies_refusals_explicitly() -> None:
    malformed = assess_search_result_input(
        source_path=_fixture("malformed_columns.tsv"),
        adapter_kind=SearchAdapterKind.GENERIC,
        mapping=SearchResultColumnMapping(
            spectrum_id="scan",
            peptide="peptide",
            charge="charge",
            score="score",
        ),
    )
    underspecified = assess_search_result_input(
        source_path=_fixture("generic_results.tsv"),
        adapter_kind=SearchAdapterKind.GENERIC,
    )
    incompatible = assess_search_result_input(
        source_path=_fixture("generic_results.tsv"),
        adapter_kind=SearchAdapterKind.GENERIC,
        mapping=SearchResultColumnMapping(
            spectrum_id="scan_id",
            peptide="sequence",
            charge="z",
            score="score",
        ),
    )

    assert malformed.valid is False
    assert malformed.refusals[0].kind is SearchInputRefusalKind.MALFORMED_INPUT
    assert underspecified.valid is False
    assert (
        underspecified.refusals[0].kind is SearchInputRefusalKind.UNDER_SPECIFIED_INPUT
    )
    assert incompatible.valid is False
    assert any(
        refusal.kind is SearchInputRefusalKind.SCIENTIFIC_INCOMPATIBILITY
        for refusal in incompatible.refusals
    )


def test_search_result_comparability_normalizes_score_orientation() -> None:
    sage = normalize_search_results_with_adapter(
        source_path=_fixture("sage_results.tsv"),
        adapter_kind=SearchAdapterKind.SAGE,
    )
    generic = normalize_search_results_with_adapter(
        source_path=_fixture("sage_results.tsv"),
        adapter_kind=SearchAdapterKind.GENERIC,
        mapping=SearchResultColumnMapping.model_validate_json(
            _fixture("sage_mapping.json").read_text()
        ),
    )
    report = compare_search_result_reports(sage, generic)

    assert report.shared_spectrum_count == 2
    assert report.exact_match_count == 2
    assert report.label_conflict_count == 0
    assert report.left_result_family is SearchResultFamily.DATABASE_TARGET_DECOY
    assert report.score_family_compatible is True
    assert report.peptide_agreement_fraction == 1.0


def test_multi_engine_merge_preserves_engine_specific_uncertainty() -> None:
    comet = normalize_search_results_with_adapter(
        source_path=_fixture("comet_merge.tsv"),
        adapter_kind=SearchAdapterKind.COMET,
    )
    sage = normalize_search_results_with_adapter(
        source_path=_fixture("sage_merge.tsv"),
        adapter_kind=SearchAdapterKind.SAGE,
    )

    merged = merge_search_result_reports((comet, sage))

    exact = next(
        entry for entry in merged.merged_entries if entry.spectrum_id == "shared-1001"
    )
    conflict = next(
        entry for entry in merged.merged_entries if entry.spectrum_id == "shared-1002"
    )

    assert merged.exact_agreement_count == 1
    assert merged.conflict_count == 1
    assert exact.consensus_peptide == "PEPTIDE"
    assert conflict.consensus_peptide is None
    assert conflict.agreement_status.value == "peptide_conflict"
    assert {entry.adapter_kind for entry in conflict.observations} == {
        SearchAdapterKind.COMET,
        SearchAdapterKind.SAGE,
    }


def test_mixed_target_library_results_keep_explicit_family_policy() -> None:
    report = normalize_search_results_with_adapter(
        source_path=_fixture("diann_report.tsv"),
        adapter_kind=SearchAdapterKind.DIANN,
    )
    policy = build_search_result_family_policy(report.adapter_manifest)

    assert (
        report.adapter_manifest.result_family is SearchResultFamily.MIXED_TARGET_LIBRARY
    )
    assert report.family_policy == policy
    assert policy.requires_target_decoy_evidence is False
    assert policy.allows_library_style_scores is True


def test_search_adapter_conformance_reports_rejection_and_unknown_label_failures() -> (
    None
):
    malformed = normalize_search_results_with_adapter(
        source_path=_fixture("sage_malformed.tsv"),
        adapter_kind=SearchAdapterKind.SAGE,
    )
    conformance = build_search_adapter_conformance_report(malformed)

    assert conformance.passes is False
    assert conformance.rejection_issue_counts["invalid_score"] == 1
    assert conformance.rejection_issue_counts["invalid_q_value"] == 1
    explicit_check = next(
        check for check in conformance.checks if check.code == "explicit_decoy_contract"
    )
    assert explicit_check.passed is False
    assert conformance.fdr_audit_trail is not None
    assert conformance.calibration_plot is not None


def test_adapter_conformance_reports_mapped_preserved_and_unsupported_fields() -> None:
    dialect = SearchAdapterDialectManifest(
        adapter_kind=SearchAdapterKind.SAGE,
        dialect_id="conformance-fields",
        display_name="Sage conformance fields",
        description="Expose preserved and unsupported native columns for conformance accounting.",
        native_columns=(
            "scan_id",
            "stripped_peptide",
            "precursor_charge",
            "score_discriminant",
            "protein_group",
            "decoy_flag",
            "qvalue",
            "analysis_batch",
            "missing_runtime_tag",
        ),
        mapping=SearchResultColumnMapping(
            spectrum_id="scan_id",
            peptide="stripped_peptide",
            charge="precursor_charge",
            score="score_discriminant",
            protein_refs="protein_group",
            q_value="qvalue",
            decoy_label="decoy_flag",
            protein_separator=";",
        ),
    )
    report = normalize_search_results_with_adapter(
        source_path=_fixture("sage_conformance_fields.tsv"),
        adapter_kind=SearchAdapterKind.SAGE,
        dialect_id="conformance-fields",
        additional_dialects=(dialect,),
    )
    conformance = build_search_adapter_conformance_report(report)

    assert isinstance(conformance.field_accounting, SearchAdapterFieldAccounting)
    assert conformance.field_accounting.mapped_columns == (
        "decoy_flag",
        "precursor_charge",
        "protein_group",
        "qvalue",
        "scan_id",
        "score_discriminant",
        "stripped_peptide",
    )
    assert conformance.field_accounting.preserved_native_only_columns == (
        "analysis_batch",
    )
    assert conformance.field_accounting.unsupported_columns == ("novel_metric",)
    assert conformance.field_accounting.lost_columns == ("missing_runtime_tag",)
