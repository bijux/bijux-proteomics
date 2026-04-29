# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics import (
    build_search_adapter_capability_matrix,
    build_search_adapter_provenance_manifest,
    get_search_adapter_manifest,
    normalize_search_results_with_adapter,
    ScoreOrientation,
    SearchAdapterKind,
    SearchResultColumnMapping,
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
