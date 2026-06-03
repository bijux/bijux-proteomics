# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.domain.semantic_ids import (
    SemanticIdNamespace,
    build_artifact_id,
    build_cross_study_card_id,
    build_matrix_id,
    build_mechanism_card_id,
    build_pathway_claim_id,
    build_peptide_id,
    build_protein_card_id,
    build_protein_claim_id,
    build_protein_id,
    build_protein_mechanism_card_id,
    build_psm_id,
    build_ptm_card_id,
    build_ptm_claim_id,
    build_raw_signal_card_id,
    build_regulator_claim_id,
    build_site_id,
    classify_semantic_id,
    ensure_semantic_id_namespace,
)


def test_scientific_semantic_ids_are_deterministic_for_core_output_families() -> None:
    site_id = build_site_id("P04637", "S", 15, "Phospho")

    assert build_protein_id("P04637") == "protein:P04637"
    assert build_peptide_id("PEPTIDEK") == "peptide:PEPTIDEK"
    assert build_psm_id("scan=42", "PEPTIDEK", 2) == "psm:scan-42:PEPTIDEK:z2"
    assert site_id == "ptm_site:P04637:S15:Phospho"
    assert build_protein_claim_id("P04637") == "protein-claim:P04637"
    assert build_pathway_claim_id("R-HSA-199420", "control", "treated") == (
        "pathway-claim:R-HSA-199420:control:treated"
    )
    assert build_regulator_claim_id(
        "MAPK14", "kinase_substrate", "site_regulation"
    ) == ("regulator-claim:MAPK14:kinase_substrate:site_regulation")
    assert build_ptm_card_id(site_id, "control", "treated") == (
        "ptm-card:ptm_site:P04637:S15:Phospho:control:treated"
    )
    assert build_ptm_claim_id(site_id, "control", "treated") == (
        "ptm-claim:ptm_site:P04637:S15:Phospho:control:treated"
    )
    assert build_protein_card_id("P04637") == "protein-card:P04637"
    assert build_protein_mechanism_card_id("P04637") == (
        "protein-mechanism-card:P04637"
    )
    assert build_mechanism_card_id("pathway_shift", "reactome:stress_response") == (
        "pathway-shift-card:reactome:stress_response"
    )
    assert build_cross_study_card_id("protein", "P04637") == (
        "cross-study-protein-card:P04637"
    )
    assert build_raw_signal_card_id("prec_peptide") == ("raw-signal-card:prec_peptide")
    assert (
        build_matrix_id(
            "protein",
            "intensity",
            aggregation_method="sum",
            normalization_method="median",
            imputation_method="none",
        )
        == "matrix:protein:intensity:sum:median:none"
    )
    assert (
        build_artifact_id(
            "cards/ptm_evidence_cards.tsv",
            folder="cards",
            artifact_kind="tsv_table",
        )
        == "artifact:cards:tsv_table:cards:ptm_evidence_cards.tsv"
    )


def test_scientific_semantic_ids_are_unique_within_scope() -> None:
    site_id = build_site_id("P04637", "S", 15, "Phospho")

    assert build_ptm_card_id(site_id, "control", "treated") != build_ptm_card_id(
        site_id,
        "control",
        "rescue",
    )
    assert build_matrix_id(
        "protein",
        "intensity",
        aggregation_method="sum",
        normalization_method="median",
        imputation_method="none",
    ) != build_matrix_id(
        "protein",
        "intensity",
        aggregation_method="sum",
        normalization_method="median",
        imputation_method="knn",
    )
    assert build_artifact_id(
        "cards/ptm_evidence_cards.tsv",
        folder="cards",
        artifact_kind="tsv_table",
    ) != build_artifact_id(
        "cards/ptm_summary.tsv",
        folder="cards",
        artifact_kind="tsv_table",
    )
    assert build_cross_study_card_id("protein", "P04637") != build_cross_study_card_id(
        "pathway",
        "P04637",
    )


def test_scientific_semantic_ids_classify_and_validate_namespaces() -> None:
    identifier = build_protein_claim_id("P11111")

    assert classify_semantic_id(identifier) is SemanticIdNamespace.PROTEIN_CLAIM
    ensure_semantic_id_namespace(identifier, SemanticIdNamespace.PROTEIN_CLAIM)

    with pytest.raises(ValueError, match="should use 'protein-card' namespace"):
        ensure_semantic_id_namespace(identifier, SemanticIdNamespace.PROTEIN_CARD)


def test_scientific_semantic_ids_reject_blank_or_invalid_components() -> None:
    with pytest.raises(ValueError, match="must not be blank"):
        build_protein_id(" ")

    with pytest.raises(ValueError, match="must be positive"):
        build_site_id("P04637", "S", 0, "Phospho")

    with pytest.raises(ValueError, match="must be positive"):
        build_psm_id("scan=1", "PEPTIDEK", 0)

    with pytest.raises(ValueError, match="unsupported mechanism card kind"):
        build_mechanism_card_id("unsupported", "P04637")
