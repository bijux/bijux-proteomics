# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import ParsimonyVariant, PsmRecord
from bijux_proteomics.identification.protein_parsimony import (
    build_protein_parsimony_report,
)
from bijux_proteomics_foundation import JsonModel


class ProteinParsimonyReferenceProtein(JsonModel):
    model_config = ConfigDict(extra="forbid")

    selection_rank: int = Field(..., ge=1)
    protein_ref: str = Field(..., min_length=1)
    source_group_id: str = Field(..., min_length=1)
    newly_explained_peptides: tuple[str, ...] = Field(default_factory=tuple)
    unresolved_shared_peptides: tuple[str, ...] = Field(default_factory=tuple)


class ProteinParsimonyReferenceCase(JsonModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., min_length=1)
    variant: ParsimonyVariant
    review_variants: tuple[ParsimonyVariant, ...] = Field(default_factory=tuple)
    records: tuple[PsmRecord, ...] = Field(default_factory=tuple)
    expected_selected_proteins: tuple[ProteinParsimonyReferenceProtein, ...] = Field(
        default_factory=tuple
    )
    expected_explained_peptides: tuple[str, ...] = Field(default_factory=tuple)
    expected_unexplained_peptides: tuple[str, ...] = Field(default_factory=tuple)
    expected_ambiguity_subjects: tuple[str, ...] = Field(default_factory=tuple)


def _identification_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "identification" / name


def test_protein_parsimony_reference_cases_match_expected_outputs() -> None:
    raw_cases = json.loads(
        _identification_fixture("protein_parsimony_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    cases = tuple(
        ProteinParsimonyReferenceCase.model_validate(case) for case in raw_cases
    )

    for case in cases:
        report = build_protein_parsimony_report(
            case.records,
            variant=case.variant,
            review_variants=case.review_variants,
        )

        assert report.explained_peptides == case.expected_explained_peptides
        assert report.unexplained_peptides == case.expected_unexplained_peptides
        assert len(report.selected_proteins) == len(case.expected_selected_proteins)
        for observed, expected in zip(
            report.selected_proteins,
            case.expected_selected_proteins,
            strict=True,
        ):
            assert observed.selection_rank == expected.selection_rank
            assert observed.protein_ref == expected.protein_ref
            assert observed.source_group_id == expected.source_group_id
            assert (
                observed.newly_explained_peptides == expected.newly_explained_peptides
            )
            assert (
                observed.unresolved_shared_peptides
                == expected.unresolved_shared_peptides
            )
        assert tuple(entry.subject_id for entry in report.unresolved_ambiguities) == (
            case.expected_ambiguity_subjects
        )


def test_protein_parsimony_reference_cases_are_reproducible() -> None:
    raw_cases = json.loads(
        _identification_fixture("protein_parsimony_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    case = ProteinParsimonyReferenceCase.model_validate(raw_cases[0])

    first = build_protein_parsimony_report(
        case.records,
        variant=case.variant,
        review_variants=case.review_variants,
    )
    second = build_protein_parsimony_report(
        case.records,
        variant=case.variant,
        review_variants=case.review_variants,
    )

    assert first.reproducibility_hash == second.reproducibility_hash
