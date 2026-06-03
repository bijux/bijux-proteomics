# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import PsmRecord
from bijux_proteomics.identification.peptide_evidence import (
    PeptideEvidenceClass,
    PeptideEvidenceTag,
    build_peptide_evidence_report,
)
from bijux_proteomics_foundation import JsonModel


class PeptideEvidenceReferenceExpectation(JsonModel):
    model_config = ConfigDict(extra="forbid")

    canonical_peptide: str = Field(..., min_length=1)
    primary_class: PeptideEvidenceClass
    accepted: bool
    tags: tuple[PeptideEvidenceTag, ...] = Field(default_factory=tuple)
    spectrum_count: int = Field(..., ge=1)


class PeptideEvidenceReferenceCase(JsonModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., min_length=1)
    threshold: float | None = Field(default=None, ge=0.0)
    score_orientation: str = Field(
        default="higher_better",
        pattern="^(higher_better|lower_better)$",
    )
    strong_q_value: float = Field(..., ge=0.0)
    reproducible_spectrum_count: int = Field(..., ge=2)
    records: tuple[PsmRecord, ...] = Field(default_factory=tuple)
    expected_entries: tuple[PeptideEvidenceReferenceExpectation, ...] = Field(
        default_factory=tuple
    )


def _identification_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "identification" / name


def test_peptide_evidence_reference_cases_match_expected_classes() -> None:
    raw_cases = json.loads(
        _identification_fixture("peptide_evidence_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    cases = tuple(
        PeptideEvidenceReferenceCase.model_validate(case) for case in raw_cases
    )

    for case in cases:
        report = build_peptide_evidence_report(
            case.records,
            threshold=case.threshold,
            score_orientation=case.score_orientation,
            strong_q_value=case.strong_q_value,
            reproducible_spectrum_count=case.reproducible_spectrum_count,
        )
        observed = {entry.canonical_peptide: entry for entry in report.entries}

        assert len(observed) == len(case.expected_entries)
        for expected in case.expected_entries:
            entry = observed[expected.canonical_peptide]
            assert entry.primary_class is expected.primary_class
            assert entry.accepted is expected.accepted
            assert entry.tags == expected.tags
            assert entry.spectrum_count == expected.spectrum_count
