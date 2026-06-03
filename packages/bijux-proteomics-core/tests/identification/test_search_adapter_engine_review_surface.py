# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from collections.abc import Callable
import csv
from importlib import import_module
from pathlib import Path
from typing import TypedDict, cast

import pytest

from bijux_proteomics.identification.search_adapters import (
    SearchAdapterKind,
    SearchEngineCorpusReport,
    build_search_adapter_provenance_manifest,
    normalize_search_results_with_adapter,
)


class SearchAdapterEngineCase(TypedDict):
    adapter_kind: SearchAdapterKind
    corpus_dir: str
    result_file: str
    config_file: str
    builder_name: str
    charge_column: str


SearchEngineCorpusBuilder = Callable[[Path], SearchEngineCorpusReport]


_ENGINE_CASES: tuple[SearchAdapterEngineCase, ...] = (
    {
        "adapter_kind": SearchAdapterKind.COMET,
        "corpus_dir": "comet",
        "result_file": "comet_results.tsv",
        "config_file": "comet.params",
        "builder_name": "build_comet_output_corpus_report",
        "charge_column": "charge",
    },
    {
        "adapter_kind": SearchAdapterKind.MSFRAGGER,
        "corpus_dir": "msfragger",
        "result_file": "msfragger_results.tsv",
        "config_file": "msfragger.params",
        "builder_name": "build_msfragger_output_corpus_report",
        "charge_column": "Charge",
    },
    {
        "adapter_kind": SearchAdapterKind.SAGE,
        "corpus_dir": "sage",
        "result_file": "sage_results.tsv",
        "config_file": "sage_search.json",
        "builder_name": "build_sage_output_corpus_report",
        "charge_column": "charge",
    },
    {
        "adapter_kind": SearchAdapterKind.MAXQUANT_EVIDENCE,
        "corpus_dir": "maxquant",
        "result_file": "maxquant_evidence.tsv",
        "config_file": "maxquant_settings.txt",
        "builder_name": "build_maxquant_output_corpus_report",
        "charge_column": "Charge",
    },
    {
        "adapter_kind": SearchAdapterKind.DIANN,
        "corpus_dir": "diann",
        "result_file": "diann_report.tsv",
        "config_file": "diann_config.json",
        "builder_name": "build_diann_output_corpus_report",
        "charge_column": "Precursor.Charge",
    },
    {
        "adapter_kind": SearchAdapterKind.SPECTRONAUT,
        "corpus_dir": "spectronaut",
        "result_file": "spectronaut_report.tsv",
        "config_file": "spectronaut_settings.txt",
        "builder_name": "build_spectronaut_output_corpus_report",
        "charge_column": "FG.Charge",
    },
)


def _matrix_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent / "fixtures" / "search_adapter_corpora"
    )


def _builder(case: SearchAdapterEngineCase) -> SearchEngineCorpusBuilder:
    module = import_module("bijux_proteomics.identification.search_adapters")
    return cast(SearchEngineCorpusBuilder, getattr(module, case["builder_name"]))


@pytest.mark.parametrize(
    ("adapter_kind", "corpus_dir", "builder_name"),
    [
        (case["adapter_kind"], case["corpus_dir"], case["builder_name"])
        for case in _ENGINE_CASES
    ],
    ids=[case["corpus_dir"] for case in _ENGINE_CASES],
)
def test_engine_output_corpus_reports_preserve_schema_contract(
    adapter_kind: SearchAdapterKind,
    corpus_dir: str,
    builder_name: str,
) -> None:
    case = next(item for item in _ENGINE_CASES if item["builder_name"] == builder_name)
    report = _builder(case)(_matrix_root() / corpus_dir)

    assert report.adapter_kind is adapter_kind
    assert report.passes is True
    assert report.missing_artifacts == ()
    assert len(report.entries) == 2
    for entry in report.entries:
        assert entry.source_sha256
        assert entry.config_sha256
        assert entry.accepted_rows > 0
        assert entry.rejected_rows == 0


@pytest.mark.parametrize(
    "case", _ENGINE_CASES, ids=[case["corpus_dir"] for case in _ENGINE_CASES]
)
def test_engine_normalization_preserves_invalid_row_rejections(
    case: SearchAdapterEngineCase,
    tmp_path: Path,
) -> None:
    source_path = _matrix_root() / str(case["corpus_dir"]) / str(case["result_file"])
    invalid_path = tmp_path / f"{case['corpus_dir']}_invalid.tsv"

    with source_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        assert reader.fieldnames is not None
        rows = list(reader)

    rows[1][str(case["charge_column"])] = "bad"
    with invalid_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=reader.fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    report = normalize_search_results_with_adapter(
        source_path=invalid_path,
        adapter_kind=case["adapter_kind"],
    )

    assert len(report.parse_report.rejected_rows) == 1
    assert report.evidence_rows[1].accepted is False
    assert {issue.code for issue in report.evidence_rows[1].issues} == {
        "invalid_charge"
    }


@pytest.mark.parametrize(
    "case", _ENGINE_CASES, ids=[case["corpus_dir"] for case in _ENGINE_CASES]
)
def test_engine_provenance_manifests_hash_source_and_config(
    case: SearchAdapterEngineCase,
) -> None:
    corpus_root = _matrix_root() / str(case["corpus_dir"])
    source_path = corpus_root / str(case["result_file"])
    config_path = corpus_root / str(case["config_file"])
    normalization = normalize_search_results_with_adapter(
        source_path=source_path,
        adapter_kind=case["adapter_kind"],
    )

    provenance = build_search_adapter_provenance_manifest(
        source_path=source_path,
        normalization_report=normalization,
        config_path=config_path,
    )

    assert provenance.adapter_kind is case["adapter_kind"]
    assert provenance.source_sha256
    assert provenance.config_sha256
    assert provenance.parameter_report is not None
    assert provenance.parameter_report.adapter_kind is case["adapter_kind"]
