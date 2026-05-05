# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.search_adapters import (
    ExternalEngineDisagreementKind,
    SearchAdapterKind,
    SearchResultColumnMapping,
    build_external_engine_disagreement_report,
    normalize_search_results_with_adapter,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "search_adapters" / name


def test_external_engine_disagreement_report_detects_missing_and_peptide_conflicts() -> (
    None
):
    comet = normalize_search_results_with_adapter(
        source_path=_fixture("comet_merge.tsv"),
        adapter_kind=SearchAdapterKind.COMET,
    )
    sage = normalize_search_results_with_adapter(
        source_path=_fixture("sage_merge.tsv"),
        adapter_kind=SearchAdapterKind.SAGE,
    )

    report = build_external_engine_disagreement_report((comet, sage))

    kinds = {entry.kind for entry in report.entries}
    assert ExternalEngineDisagreementKind.PEPTIDE_CONFLICT in kinds
    assert report.disagreement_counts["peptide_conflict"] >= 1


def test_external_engine_disagreement_report_surfaces_missing_evidence() -> None:
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
    comet = normalize_search_results_with_adapter(
        source_path=_fixture("comet_results.tsv"),
        adapter_kind=SearchAdapterKind.COMET,
    )

    report = build_external_engine_disagreement_report((sage, generic, comet))

    assert ExternalEngineDisagreementKind.MISSING_EVIDENCE in {
        entry.kind for entry in report.entries
    }
    assert report.disagreement_counts["missing_evidence"] >= 1
