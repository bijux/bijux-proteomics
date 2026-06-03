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
        for observed_entry, expected_entry in zip(
            report.entries, case.expected_entries, strict=True
        ):
            assert observed_entry.protein_ref == expected_entry.protein_ref
            assert (
                observed_entry.covered_residue_count
                == expected_entry.covered_residue_count
            )
            assert observed_entry.coverage_fraction == expected_entry.coverage_fraction
            assert observed_entry.covered_ranges == expected_entry.covered_ranges
            assert observed_entry.uncovered_ranges == expected_entry.uncovered_ranges
            assert observed_entry.covered_peptides == expected_entry.covered_peptides
            assert (
                observed_entry.unmatched_peptides == expected_entry.unmatched_peptides
            )

        assert len(report.uncovered_regions) == len(case.expected_uncovered_regions)
        for observed_region, expected_region in zip(
            report.uncovered_regions,
            case.expected_uncovered_regions,
            strict=True,
        ):
            assert observed_region.protein_ref == expected_region.protein_ref
            assert observed_region.region_index == expected_region.region_index
            assert observed_region.start_residue == expected_region.start_residue
            assert observed_region.end_residue == expected_region.end_residue
            assert observed_region.residue_count == expected_region.residue_count

        assert len(report.peptide_coordinates) == len(case.expected_coordinate_rows)
        for observed_coordinate, expected_coordinate in zip(
            report.peptide_coordinates,
            case.expected_coordinate_rows,
            strict=True,
        ):
            assert observed_coordinate.protein_ref == expected_coordinate.protein_ref
            assert (
                observed_coordinate.canonical_peptide
                == expected_coordinate.canonical_peptide
            )
            assert (
                observed_coordinate.coordinate_status
                is expected_coordinate.coordinate_status
            )
            assert (
                observed_coordinate.occurrence_index
                == expected_coordinate.occurrence_index
            )
            assert observed_coordinate.start_residue == expected_coordinate.start_residue
            assert observed_coordinate.end_residue == expected_coordinate.end_residue


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
