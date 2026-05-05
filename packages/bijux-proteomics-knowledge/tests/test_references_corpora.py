# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_knowledge.references import (
    DEFAULT_CORPUS_MANIFESTS,
    KnowledgeCorpusSourceKind,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_corpus_manifests_split_bundled_and_external_sources() -> None:
    bundled = {
        manifest.corpus_id
        for manifest in DEFAULT_CORPUS_MANIFESTS
        if manifest.source_kind is KnowledgeCorpusSourceKind.BUNDLED_FIXTURE
    }
    external = {
        manifest.corpus_id
        for manifest in DEFAULT_CORPUS_MANIFESTS
        if manifest.source_kind is KnowledgeCorpusSourceKind.EXTERNAL_REFERENCE
    }

    assert bundled == {
        "corpus:search_adapter_fixture_suite",
        "corpus:quant_fixture_suite",
        "corpus:ptm_fixture_suite",
        "corpus:chromatogram_qc_fixture",
    }
    assert external == {
        "corpus:uniprot_reference_proteome",
        "corpus:target_decoy_method_reference",
        "corpus:swath_method_reference",
        "corpus:ptm_localization_method_reference",
        "corpus:tmtpro_labeling_reference",
        "corpus:protein_inference_review_reference",
    }


def test_bundled_corpora_point_to_real_fixture_paths() -> None:
    for manifest in DEFAULT_CORPUS_MANIFESTS:
        if manifest.source_kind is not KnowledgeCorpusSourceKind.BUNDLED_FIXTURE:
            continue
        assert manifest.repo_relative_path is not None
        assert (REPO_ROOT / manifest.repo_relative_path).exists()


def test_external_corpora_carry_reference_locators() -> None:
    for manifest in DEFAULT_CORPUS_MANIFESTS:
        if manifest.source_kind is not KnowledgeCorpusSourceKind.EXTERNAL_REFERENCE:
            continue
        assert manifest.reference_locator is not None
        assert manifest.reference_accession is not None
        assert manifest.citation_ids
