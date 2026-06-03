# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import PsmRecord
from bijux_proteomics.identification.protein_target_decoy_fdr import (
    build_protein_target_decoy_fdr_report,
)
from bijux_proteomics_foundation import JsonModel


class ProteinTargetDecoyReferenceExpectation(JsonModel):
    model_config = ConfigDict(extra="forbid")

    rank: int = Field(..., ge=1)
    protein_ref: str = Field(..., min_length=1)
    peptide_count: int = Field(..., ge=1)
    unique_peptide_count: int = Field(..., ge=0)
    cumulative_targets: int = Field(..., ge=0)
    cumulative_decoys: int = Field(..., ge=0)
    raw_fdr: float = Field(..., ge=0.0)
    q_value: float = Field(..., ge=0.0)
    accepted: bool


class ProteinTargetDecoyReferenceCase(JsonModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., min_length=1)
    score_orientation: str = Field(
        default="higher_better",
        pattern="^(higher_better|lower_better)$",
    )
    evidence_policy: str = Field(
        default="best_score",
        pattern="^(best_score|combined_evidence)$",
    )
    threshold: float | None = Field(default=None, ge=0.0)
    records: tuple[PsmRecord, ...] = Field(default_factory=tuple)
    expected_entries: tuple[ProteinTargetDecoyReferenceExpectation, ...] = Field(
        default_factory=tuple
    )


def _identification_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "identification" / name


def test_protein_target_decoy_reference_cases_match_expected_q_values() -> None:
    raw_cases = json.loads(
        _identification_fixture("protein_target_decoy_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    cases = tuple(
        ProteinTargetDecoyReferenceCase.model_validate(case) for case in raw_cases
    )

    assert {case.score_orientation for case in cases} == {
        "higher_better",
        "lower_better",
    }

    for case in cases:
        report = build_protein_target_decoy_fdr_report(
            case.records,
            threshold=case.threshold,
            score_orientation=case.score_orientation,
            evidence_policy=case.evidence_policy,
        )

        assert len(report.entries) == len(case.expected_entries)
        for observed, expected in zip(
            report.entries, case.expected_entries, strict=True
        ):
            assert observed.rank == expected.rank
            assert observed.evidence.protein_ref == expected.protein_ref
            assert observed.evidence.peptide_count == expected.peptide_count
            assert (
                observed.evidence.unique_peptide_count == expected.unique_peptide_count
            )
            assert observed.cumulative_targets == expected.cumulative_targets
            assert observed.cumulative_decoys == expected.cumulative_decoys
            assert observed.raw_fdr == expected.raw_fdr
            assert observed.q_value == expected.q_value
            assert observed.accepted is expected.accepted
