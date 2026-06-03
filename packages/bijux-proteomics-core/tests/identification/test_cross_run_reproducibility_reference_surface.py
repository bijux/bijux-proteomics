# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import PsmRecord
from bijux_proteomics.identification.cross_run_reproducibility import (
    CrossRunEntityType,
    CrossRunReproducibilityClass,
    RunDetectionContext,
    build_peptide_cross_run_reproducibility_report,
    build_protein_cross_run_reproducibility_report,
)
from bijux_proteomics_foundation import JsonModel


class CrossRunReferenceExpectation(JsonModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    detected_run_count: int = Field(..., ge=0)
    detection_frequency: float = Field(..., ge=0.0, le=1.0)
    detected_condition_count: int = Field(..., ge=0)
    primary_condition: str | None = None
    condition_specificity: float = Field(..., ge=0.0, le=1.0)
    replicate_consistency: float = Field(..., ge=0.0, le=1.0)
    reproducibility_class: CrossRunReproducibilityClass


class CrossRunReferenceSummary(JsonModel):
    model_config = ConfigDict(extra="forbid")

    total_entries: int = Field(..., ge=0)
    reproducible_count: int = Field(..., ge=0)
    condition_specific_count: int = Field(..., ge=0)
    single_run_only_count: int = Field(..., ge=0)
    exploratory_count: int = Field(..., ge=0)
    condition_aware_entry_count: int = Field(..., ge=0)


class CrossRunReferenceCase(JsonModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., min_length=1)
    entity_type: CrossRunEntityType
    exploratory_entities: tuple[str, ...] = Field(default_factory=tuple)
    run_contexts: tuple[RunDetectionContext, ...] = Field(default_factory=tuple)
    records: tuple[PsmRecord, ...] = Field(default_factory=tuple)
    expected_summary: CrossRunReferenceSummary
    expected_entries: tuple[CrossRunReferenceExpectation, ...] = Field(
        default_factory=tuple
    )


def _identification_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "identification" / name


def test_cross_run_reproducibility_reference_cases_match_expected_outputs() -> None:
    raw_cases = json.loads(
        _identification_fixture(
            "cross_run_reproducibility_reference_cases.json"
        ).read_text(encoding="utf-8")
    )
    cases = tuple(CrossRunReferenceCase.model_validate(case) for case in raw_cases)

    for case in cases:
        if case.entity_type is CrossRunEntityType.PEPTIDE:
            report = build_peptide_cross_run_reproducibility_report(
                case.records,
                run_contexts=case.run_contexts,
                exploratory_canonical_peptides=case.exploratory_entities,
            )
        else:
            report = build_protein_cross_run_reproducibility_report(
                case.records,
                run_contexts=case.run_contexts,
                exploratory_protein_refs=case.exploratory_entities,
            )

        assert report.summary.total_entries == case.expected_summary.total_entries
        assert (
            report.summary.reproducible_count
            == case.expected_summary.reproducible_count
        )
        assert (
            report.summary.condition_specific_count
            == case.expected_summary.condition_specific_count
        )
        assert (
            report.summary.single_run_only_count
            == case.expected_summary.single_run_only_count
        )
        assert (
            report.summary.exploratory_count == case.expected_summary.exploratory_count
        )
        assert (
            report.summary.condition_aware_entry_count
            == case.expected_summary.condition_aware_entry_count
        )

        observed = {entry.entity_id: entry for entry in report.entries}
        assert set(observed) == {
            expected.entity_id for expected in case.expected_entries
        }
        for expected in case.expected_entries:
            entry = observed[expected.entity_id]
            assert entry.detected_run_count == expected.detected_run_count
            assert entry.detection_frequency == expected.detection_frequency
            assert entry.detected_condition_count == expected.detected_condition_count
            assert entry.primary_condition == expected.primary_condition
            assert entry.condition_specificity == expected.condition_specificity
            assert entry.replicate_consistency == expected.replicate_consistency
            assert entry.reproducibility_class is expected.reproducibility_class
