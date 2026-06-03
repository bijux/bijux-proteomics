# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification.picked_protein_fdr import (
    build_picked_protein_fdr_report_from_psm_records,
)
from bijux_proteomics_foundation import JsonModel


class PickedProteinFdrReferenceExpectation(JsonModel):
    model_config = ConfigDict(extra="forbid")

    rank: int = Field(..., ge=1)
    pair_id: str = Field(..., min_length=1)
    target_ref: str | None = None
    decoy_ref: str | None = None
    target_score: float | None = Field(default=None, ge=0.0)
    decoy_score: float | None = Field(default=None, ge=0.0)
    winner_ref: str = Field(..., min_length=1)
    winner_target_decoy_label: TargetDecoyLabel
    raw_fdr: float = Field(..., ge=0.0)
    q_value: float = Field(..., ge=0.0)
    accepted: bool


class PickedProteinFdrReferenceCase(JsonModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., min_length=1)
    score_orientation: str = Field(
        default="higher_better",
        pattern="^(higher_better|lower_better)$",
    )
    threshold: float | None = Field(default=None, ge=0.0)
    records: tuple[PsmRecord, ...] = Field(default_factory=tuple)
    expected_entries: tuple[PickedProteinFdrReferenceExpectation, ...] = Field(
        default_factory=tuple
    )


def _identification_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "identification" / name


def test_picked_protein_reference_cases_match_expected_pair_competition() -> None:
    raw_cases = json.loads(
        _identification_fixture("picked_protein_fdr_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    cases = tuple(
        PickedProteinFdrReferenceCase.model_validate(case) for case in raw_cases
    )

    assert {case.score_orientation for case in cases} == {"higher_better"}

    for case in cases:
        report = build_picked_protein_fdr_report_from_psm_records(
            case.records,
            threshold=case.threshold,
            score_orientation=case.score_orientation,
        )

        assert report.summary.q_values_monotonic is True
        assert len(report.entries) == len(case.expected_entries)
        for observed, expected in zip(
            report.entries, case.expected_entries, strict=True
        ):
            assert observed.rank == expected.rank
            assert observed.pair_id == expected.pair_id
            assert observed.target_ref == expected.target_ref
            assert observed.decoy_ref == expected.decoy_ref
            assert observed.target_score == expected.target_score
            assert observed.decoy_score == expected.decoy_score
            assert observed.winner_ref == expected.winner_ref
            assert (
                observed.winner_target_decoy_label is expected.winner_target_decoy_label
            )
            assert observed.raw_fdr == expected.raw_fdr
            assert observed.q_value == expected.q_value
            assert observed.accepted is expected.accepted


def test_picked_protein_reference_cases_are_reproducible() -> None:
    raw_cases = json.loads(
        _identification_fixture("picked_protein_fdr_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    case = PickedProteinFdrReferenceCase.model_validate(raw_cases[0])

    first = build_picked_protein_fdr_report_from_psm_records(
        case.records,
        threshold=case.threshold,
        score_orientation=case.score_orientation,
    )
    second = build_picked_protein_fdr_report_from_psm_records(
        case.records,
        threshold=case.threshold,
        score_orientation=case.score_orientation,
    )

    assert first.reproducibility_hash == second.reproducibility_hash
