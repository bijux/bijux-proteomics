# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Explicit result-family policy over normalized search-adapter outputs."""

from __future__ import annotations

from bijux_proteomics.identification.search_adapters.contracts import (
    SearchAdapterManifest,
    SearchResultFamily,
    SearchResultFamilyPolicy,
)


def build_search_result_family_policy(
    manifest: SearchAdapterManifest,
) -> SearchResultFamilyPolicy:
    """Build the explicit policy for one adapter result family."""
    if manifest.result_family is SearchResultFamily.DATABASE_TARGET_DECOY:
        return SearchResultFamilyPolicy(
            result_family=manifest.result_family,
            requires_target_decoy_evidence=True,
            requires_protein_references=manifest.supports_protein_refs,
            allows_library_style_scores=False,
            note="database target-decoy search results should preserve decoy evidence and protein references when the engine provides them",
        )
    if manifest.result_family is SearchResultFamily.LIBRARY_SEARCH:
        return SearchResultFamilyPolicy(
            result_family=manifest.result_family,
            requires_target_decoy_evidence=False,
            requires_protein_references=manifest.supports_protein_refs,
            allows_library_style_scores=True,
            note="library search results may rank by spectral-library confidence without explicit target-decoy evidence on every row",
        )
    return SearchResultFamilyPolicy(
        result_family=manifest.result_family,
        requires_target_decoy_evidence=False,
        requires_protein_references=manifest.supports_protein_refs,
        allows_library_style_scores=True,
        note="mixed target and library search results must keep their hybrid family explicit so downstream review does not assume pure database semantics",
    )
