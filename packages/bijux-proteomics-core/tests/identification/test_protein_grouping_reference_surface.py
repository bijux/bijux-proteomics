# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import PsmRecord
from bijux_proteomics.identification.protein_grouping import (
    build_protein_grouping_report,
)
from bijux_proteomics_foundation import JsonModel


class ProteinGroupingReferenceExpectation(JsonModel):
    model_config = ConfigDict(extra="forbid")

    group_id: str = Field(..., min_length=1)
    leading_protein: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    unique_peptides: tuple[str, ...] = Field(default_factory=tuple)
    shared_peptides: tuple[str, ...] = Field(default_factory=tuple)


class ProteinGroupingReferenceCase(JsonModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., min_length=1)
    records: tuple[PsmRecord, ...] = Field(default_factory=tuple)
    expected_groups: tuple[ProteinGroupingReferenceExpectation, ...] = Field(
        default_factory=tuple
    )


def _identification_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "identification" / name


def test_protein_grouping_reference_cases_match_expected_groups() -> None:
    raw_cases = json.loads(
        _identification_fixture("protein_grouping_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    cases = tuple(
        ProteinGroupingReferenceCase.model_validate(case) for case in raw_cases
    )

    for case in cases:
        report = build_protein_grouping_report(case.records)

        assert len(report.groups) == len(case.expected_groups)
        for observed, expected in zip(report.groups, case.expected_groups, strict=True):
            assert observed.group_id == expected.group_id
            assert observed.leading_protein == expected.leading_protein
            assert observed.protein_refs == expected.protein_refs
            assert observed.unique_peptides == expected.unique_peptides
            assert observed.shared_peptides == expected.shared_peptides


def test_protein_grouping_reference_cases_are_reproducible() -> None:
    raw_cases = json.loads(
        _identification_fixture("protein_grouping_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    case = ProteinGroupingReferenceCase.model_validate(raw_cases[0])

    first = build_protein_grouping_report(case.records)
    second = build_protein_grouping_report(case.records)

    assert first.reproducibility_hash == second.reproducibility_hash
