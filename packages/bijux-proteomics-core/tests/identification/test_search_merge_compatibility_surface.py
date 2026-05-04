# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics.search_adapters import (
    SearchAdapterKind,
    SearchResultColumnMapping,
    assess_search_merge_compatibility,
    merge_search_result_reports_with_compatibility,
    normalize_search_results_with_adapter,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "search_adapters" / name


def test_merge_compatibility_flags_incompatible_score_families() -> None:
    comet = normalize_search_results_with_adapter(
        source_path=_fixture("comet_merge.tsv"),
        adapter_kind=SearchAdapterKind.COMET,
    )
    fragger = normalize_search_results_with_adapter(
        source_path=_fixture("msfragger_results.tsv"),
        adapter_kind=SearchAdapterKind.MSFRAGGER,
    )

    compatibility = assess_search_merge_compatibility((comet, fragger))

    assert compatibility.compatible is False
    assert any(issue.code == "score_family_mismatch" for issue in compatibility.issues)


def test_merge_with_compatibility_refuses_incompatible_mixed_engine_merge() -> None:
    comet = normalize_search_results_with_adapter(
        source_path=_fixture("comet_merge.tsv"),
        adapter_kind=SearchAdapterKind.COMET,
    )
    sage = normalize_search_results_with_adapter(
        source_path=_fixture("sage_merge.tsv"),
        adapter_kind=SearchAdapterKind.SAGE,
    )

    with pytest.raises(ValueError, match="compatibility errors"):
        merge_search_result_reports_with_compatibility((comet, sage))


def test_merge_with_compatibility_allows_generic_bridge_with_shared_semantics() -> None:
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

    merged = merge_search_result_reports_with_compatibility((sage, generic))

    assert merged.exact_agreement_count == 2
    assert merged.conflict_count == 0
    assert merged.partial_coverage_count == 0
