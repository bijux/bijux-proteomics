# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import PsmRecord
from bijux_proteomics.identification.cross_run_reproducibility import (
    RunDetectionContext,
)
from bijux_proteomics.identification.protein_evidence import (
    ProteinEvidenceDowngradeReason,
    ProteinEvidenceTier,
    build_protein_evidence_report,
)
from bijux_proteomics_foundation import JsonModel


class ProteinEvidenceReferenceExpectation(JsonModel):
    model_config = ConfigDict(extra="forbid")

    representative_protein: str = Field(..., min_length=1)
    evidence_tier: ProteinEvidenceTier
    downgrade_reasons: tuple[ProteinEvidenceDowngradeReason, ...] = Field(
        default_factory=tuple
    )
    detected_run_count: int = Field(..., ge=0)


class ProteinEvidenceReferenceCase(JsonModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., min_length=1)
    high_q_value: float = Field(..., ge=0.0)
    moderate_q_value: float = Field(..., ge=0.0)
    score_orientation: str = Field(
        default="higher_better",
        pattern="^(higher_better|lower_better)$",
    )
    run_contexts: tuple[RunDetectionContext, ...] = Field(default_factory=tuple)
    records: tuple[PsmRecord, ...] = Field(default_factory=tuple)
    expected_entries: tuple[ProteinEvidenceReferenceExpectation, ...] = Field(
        default_factory=tuple
    )


def _identification_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "identification" / name


def test_protein_evidence_reference_cases_match_expected_tiers() -> None:
    raw_cases = json.loads(
        _identification_fixture("protein_evidence_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    cases = tuple(
        ProteinEvidenceReferenceCase.model_validate(case) for case in raw_cases
    )

    for case in cases:
        report = build_protein_evidence_report(
            case.records,
            high_q_value=case.high_q_value,
            moderate_q_value=case.moderate_q_value,
            score_orientation=case.score_orientation,
            run_contexts=case.run_contexts,
        )
        observed = {entry.representative_protein: entry for entry in report.entries}

        assert len(observed) == len(case.expected_entries)
        for expected in case.expected_entries:
            entry = observed[expected.representative_protein]
            assert entry.evidence_tier is expected.evidence_tier
            assert entry.downgrade_reasons == expected.downgrade_reasons
            assert entry.detected_run_count == expected.detected_run_count
