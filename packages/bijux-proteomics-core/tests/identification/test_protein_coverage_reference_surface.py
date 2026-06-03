# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import PsmRecord
from bijux_proteomics.identification.protein_coverage import (
    ProteinCoverageCoordinateStatus,
    build_protein_coverage_report,
)
from bijux_proteomics_foundation import JsonModel


class ProteinCoverageReferenceEntry(JsonModel):
    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    covered_residue_count: int = Field(..., ge=0)
    coverage_fraction: float = Field(..., ge=0.0, le=1.0)
    covered_ranges: tuple[tuple[int, int], ...] = Field(default_factory=tuple)
    uncovered_ranges: tuple[tuple[int, int], ...] = Field(default_factory=tuple)
    covered_peptides: tuple[str, ...] = Field(default_factory=tuple)
    unmatched_peptides: tuple[str, ...] = Field(default_factory=tuple)


class ProteinCoverageReferenceRegion(JsonModel):
    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    region_index: int = Field(..., ge=1)
    start_residue: int = Field(..., ge=1)
    end_residue: int = Field(..., ge=1)
    residue_count: int = Field(..., ge=1)


class ProteinCoverageReferenceCoordinate(JsonModel):
    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    coordinate_status: ProteinCoverageCoordinateStatus
    occurrence_index: int | None = Field(default=None, ge=1)
    start_residue: int | None = Field(default=None, ge=1)
    end_residue: int | None = Field(default=None, ge=1)


class ProteinCoverageReferenceCase(JsonModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., min_length=1)
    threshold: float = Field(..., ge=0.0)
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    protein_sequences: dict[str, str] = Field(default_factory=dict)
    records: tuple[PsmRecord, ...] = Field(default_factory=tuple)
    expected_entries: tuple[ProteinCoverageReferenceEntry, ...] = Field(
        default_factory=tuple
    )
    expected_uncovered_regions: tuple[ProteinCoverageReferenceRegion, ...] = Field(
        default_factory=tuple
    )
    expected_coordinate_rows: tuple[ProteinCoverageReferenceCoordinate, ...] = Field(
        default_factory=tuple
    )


def _identification_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "identification" / name


def test_protein_coverage_reference_cases_match_expected_outputs() -> None:
    raw_cases = json.loads(
        _identification_fixture("protein_coverage_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    cases = tuple(
        ProteinCoverageReferenceCase.model_validate(case) for case in raw_cases
    )

    for case in cases:
        report = build_protein_coverage_report(
            case.records,
            protein_sequences=case.protein_sequences,
            threshold=case.threshold,
            score_orientation=case.score_orientation,
        )

        assert len(report.entries) == len(case.expected_entries)
        for observed, expected in zip(
            report.entries, case.expected_entries, strict=True
        ):
            assert observed.protein_ref == expected.protein_ref
            assert observed.covered_residue_count == expected.covered_residue_count
            assert observed.coverage_fraction == expected.coverage_fraction
            assert observed.covered_ranges == expected.covered_ranges
            assert observed.uncovered_ranges == expected.uncovered_ranges
            assert observed.covered_peptides == expected.covered_peptides
            assert observed.unmatched_peptides == expected.unmatched_peptides

        assert len(report.uncovered_regions) == len(case.expected_uncovered_regions)
        for observed, expected in zip(
            report.uncovered_regions,
            case.expected_uncovered_regions,
            strict=True,
        ):
            assert observed.protein_ref == expected.protein_ref
            assert observed.region_index == expected.region_index
            assert observed.start_residue == expected.start_residue
            assert observed.end_residue == expected.end_residue
            assert observed.residue_count == expected.residue_count

        assert len(report.peptide_coordinates) == len(case.expected_coordinate_rows)
        for observed, expected in zip(
            report.peptide_coordinates,
            case.expected_coordinate_rows,
            strict=True,
        ):
            assert observed.protein_ref == expected.protein_ref
            assert observed.canonical_peptide == expected.canonical_peptide
            assert observed.coordinate_status is expected.coordinate_status
            assert observed.occurrence_index == expected.occurrence_index
            assert observed.start_residue == expected.start_residue
            assert observed.end_residue == expected.end_residue


def test_protein_coverage_reference_cases_are_reproducible() -> None:
    raw_cases = json.loads(
        _identification_fixture("protein_coverage_reference_cases.json").read_text(
            encoding="utf-8"
        )
    )
    case = ProteinCoverageReferenceCase.model_validate(raw_cases[0])

    first = build_protein_coverage_report(
        case.records,
        protein_sequences=case.protein_sequences,
        threshold=case.threshold,
        score_orientation=case.score_orientation,
    )
    second = build_protein_coverage_report(
        case.records,
        protein_sequences=case.protein_sequences,
        threshold=case.threshold,
        score_orientation=case.score_orientation,
    )

    assert first.reproducibility_hash == second.reproducibility_hash
