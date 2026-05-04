# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.search_adapters import (
    SearchAdapterKind,
    SearchToleranceUnit,
    parse_search_parameter_file,
)


def _corpus_fixture(*parts: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "search_adapter_corpora" / Path(*parts)


def test_maxquant_parameter_parser_extracts_core_provenance_fields() -> None:
    report = parse_search_parameter_file(
        source_path=_corpus_fixture("maxquant", "maxquant_settings.txt"),
        adapter_kind=SearchAdapterKind.MAXQUANT_EVIDENCE,
    )

    assert report.adapter_kind is SearchAdapterKind.MAXQUANT_EVIDENCE
    assert report.enzyme == "trypsin"
    assert report.precursor_tolerance_unit is SearchToleranceUnit.PPM
    assert report.fragment_tolerance_unit is SearchToleranceUnit.DA
    assert report.decoy_prefix == "REV__"
    assert {item.site for item in report.fixed_modifications} == {"C"}
    assert {item.site for item in report.variable_modifications} == {"M", "S"}


def test_diann_parameter_parser_extracts_json_config_provenance() -> None:
    report = parse_search_parameter_file(
        source_path=_corpus_fixture("diann", "diann_config.json"),
        adapter_kind=SearchAdapterKind.DIANN,
    )

    assert report.adapter_kind is SearchAdapterKind.DIANN
    assert report.enzyme == "trypsin"
    assert report.precursor_tolerance == 20.0
    assert report.fragment_tolerance == 30.0
    assert report.decoy_prefix == "DECOY_"
    assert report.has_decoy_strategy is True


def test_spectronaut_parameter_parser_extracts_tolerance_and_modifications() -> None:
    report = parse_search_parameter_file(
        source_path=_corpus_fixture("spectronaut", "spectronaut_settings.txt"),
        adapter_kind=SearchAdapterKind.SPECTRONAUT,
    )

    assert report.adapter_kind is SearchAdapterKind.SPECTRONAUT
    assert report.enzyme == "trypsin"
    assert report.precursor_tolerance_unit is SearchToleranceUnit.PPM
    assert report.fragment_tolerance_unit is SearchToleranceUnit.PPM
    assert report.decoy_prefix == "DECOY_"
    assert {item.site for item in report.variable_modifications} == {"M", "Y"}
