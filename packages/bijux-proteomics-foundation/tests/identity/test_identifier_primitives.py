# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pydantic import BaseModel, ValidationError
import pytest

from bijux_proteomics_foundation import ProgramId
from bijux_proteomics_foundation.identity.identifiers import (
    ExperimentId,
    IdentifierKind,
    PeptideId,
    PromotionId,
    ProteinId,
    ReviewId,
    RunId,
    SpectrumId,
    build_identifier,
    classify_identifier,
    ensure_identifier_kind,
)


class IdentifierHolder(BaseModel):
    program_id: ProgramId


class ScientificIdentifierHolder(BaseModel):
    protein_id: ProteinId
    peptide_id: PeptideId
    spectrum_id: SpectrumId
    experiment_id: ExperimentId
    run_id: RunId
    review_id: ReviewId
    promotion_id: PromotionId


def test_typed_ids_enforce_non_empty_values() -> None:
    with pytest.raises(ValidationError):
        IdentifierHolder(program_id="  ")


def test_typed_ids_enforce_stable_identifier_pattern() -> None:
    IdentifierHolder(program_id="prog-1")

    with pytest.raises(ValidationError):
        IdentifierHolder(program_id="Program 1")


def test_identifier_helpers_classify_and_validate_prefix() -> None:
    assert classify_identifier("prog-1") is IdentifierKind.PROGRAM
    assert classify_identifier("protein-p12345") is IdentifierKind.PROTEIN
    assert classify_identifier("claim-mechanism-1") is IdentifierKind.CLAIM
    assert classify_identifier("unknown-1") is None

    ensure_identifier_kind("target-1", IdentifierKind.TARGET)

    with pytest.raises(ValueError, match="should use 'prog-' prefix"):
        ensure_identifier_kind("target-1", IdentifierKind.PROGRAM)


def test_build_identifier_creates_canonical_prefixed_ids() -> None:
    identifier = build_identifier(IdentifierKind.ASSAY, "Primary Readout")

    assert identifier == "assay-primary-readout"


def test_scientific_identifier_aliases_accept_expected_prefixes() -> None:
    payload = ScientificIdentifierHolder(
        protein_id="protein-p12345",
        peptide_id="peptide-acdefghik-2",
        spectrum_id="spectrum-run-1-scan-22",
        experiment_id="experiment-dose-response",
        run_id="run-lcms-001",
        review_id="review-gate-binding",
        promotion_id="promotion-batch-1",
    )

    assert payload.protein_id == "protein-p12345"


def test_identifier_helpers_validate_new_scientific_kinds() -> None:
    ensure_identifier_kind("review-gate-binding", IdentifierKind.REVIEW)
    ensure_identifier_kind("promotion-batch-1", IdentifierKind.PROMOTION)

    with pytest.raises(ValueError, match="should use 'run-' prefix"):
        ensure_identifier_kind("experiment-dose-response", IdentifierKind.RUN)
