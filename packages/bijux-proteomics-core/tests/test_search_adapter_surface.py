# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics import (
    build_search_adapter_conformance_report,
    build_search_adapter_capability_matrix,
    build_search_adapter_provenance_manifest,
    compare_search_result_reports,
    get_search_adapter_manifest,
    normalize_search_results_with_adapter,
    parse_search_parameter_file,
    ScoreOrientation,
    SearchAdapterKind,
    SearchResultColumnMapping,
    validate_search_parameters,
)


def _fixture(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "search_adapters" / name


def test_search_adapter_registry_exposes_capability_matrix() -> None:
    matrix = build_search_adapter_capability_matrix()
    by_kind = {row.adapter_kind: row for row in matrix}

    assert SearchAdapterKind.COMET in by_kind
    assert by_kind[SearchAdapterKind.COMET].score_orientation is ScoreOrientation.LOWER_BETTER
    assert by_kind[SearchAdapterKind.SAGE].supports_q_value is True
    assert by_kind[SearchAdapterKind.GENERIC].supports_config_hash is True


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
    diann_by_id = {record.spectrum_id: record for record in diann.normalized_records}
    assert diann_by_id["run1_PEPTIDE_2"].q_value == 0.003
    assert spectronaut.normalized_records[0].protein_refs == ("P12345", "Q22222")


def test_generic_adapter_and_provenance_manifest_are_stable() -> None:
    mapping = SearchResultColumnMapping.model_validate_json(_fixture("generic_mapping.json").read_text())
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
        config_path=_fixture("sage_config.json"),
    )

    assert generic.normalized_records[0].canonical_peptide == "PEPTIDE"
    assert generic.normalized_records[1].target_decoy_label.value == "decoy"
    assert provenance.adapter_kind is SearchAdapterKind.SAGE
    assert provenance.adapter_version == "0.16.0"
    assert provenance.config_sha256
    assert provenance.parse_provenance.column_mapping.spectrum_id == "scannr"


def test_built_in_manifests_are_self_describing() -> None:
    manifest = get_search_adapter_manifest(SearchAdapterKind.MAXQUANT_EVIDENCE)
    rendered = json.loads(manifest.to_stable_json())

    assert manifest.display_name == "MaxQuant evidence"
    assert "Modified sequence" in manifest.native_columns
    assert rendered["adapter_kind"] == "maxquant-evidence"


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
    assert comet.precursor_tolerance_unit.value == "ppm"
    assert comet.fixed_modifications[0].site == "C"
    assert fragger.fragment_tolerance == 20.0
    assert fragger.decoy_prefix == "DECOY_"
    assert sage.variable_modifications[0].site == "M"
    assert sage.has_decoy_strategy is True


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


def test_search_result_comparability_normalizes_score_orientation() -> None:
    sage = normalize_search_results_with_adapter(
        source_path=_fixture("sage_results.tsv"),
        adapter_kind=SearchAdapterKind.SAGE,
    )
    generic = normalize_search_results_with_adapter(
        source_path=_fixture("sage_results.tsv"),
        adapter_kind=SearchAdapterKind.GENERIC,
        mapping=SearchResultColumnMapping.model_validate_json(_fixture("sage_mapping.json").read_text()),
    )
    report = compare_search_result_reports(sage, generic)

    assert report.shared_spectrum_count == 2
    assert report.exact_match_count == 2
    assert report.label_conflict_count == 0
    assert report.peptide_agreement_fraction == 1.0


def test_search_adapter_conformance_reports_rejection_and_unknown_label_failures() -> None:
    malformed = normalize_search_results_with_adapter(
        source_path=_fixture("sage_malformed.tsv"),
        adapter_kind=SearchAdapterKind.SAGE,
    )
    conformance = build_search_adapter_conformance_report(malformed)

    assert conformance.passes is False
    assert conformance.rejection_issue_counts["invalid_score"] == 1
    assert conformance.rejection_issue_counts["invalid_q_value"] == 1
    explicit_check = next(check for check in conformance.checks if check.code == "explicit_decoy_contract")
    assert explicit_check.passed is False
    assert conformance.fdr_audit_trail is not None
    assert conformance.calibration_plot is not None
