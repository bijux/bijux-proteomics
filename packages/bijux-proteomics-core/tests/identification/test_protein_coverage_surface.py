# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import PsmRecord
from bijux_proteomics.identification.protein_coverage import (
    ProteinCoverageCoordinateStatus,
    build_protein_coverage_report,
    render_protein_coverage_peptide_coordinates_tsv,
    render_protein_coverage_uncovered_regions_tsv,
)


def test_protein_coverage_report_merges_overlapping_residues_and_tracks_uncovered_regions() -> (
    None
):
    records = (
        PsmRecord(
            spectrum_id="scan=coverage-1",
            peptide="ABCD",
            canonical_peptide="ABCD",
            charge=2,
            score=50.0,
            q_value=0.01,
            protein_refs=("P10001",),
        ),
        PsmRecord(
            spectrum_id="scan=coverage-2",
            peptide="CDEF",
            canonical_peptide="CDEF",
            charge=2,
            score=49.0,
            q_value=0.02,
            protein_refs=("P10001",),
        ),
        PsmRecord(
            spectrum_id="scan=coverage-3",
            peptide="ZZZ",
            canonical_peptide="ZZZ",
            charge=2,
            score=48.0,
            q_value=0.03,
            protein_refs=("P10001",),
        ),
    )

    report = build_protein_coverage_report(
        records,
        protein_sequences={"P10001": "ABCDEFGHIK"},
    )

    assert report.summary.total_proteins == 1
    assert report.summary.total_covered_residues == 6
    entry = report.entries[0]
    assert entry.covered_ranges == ((1, 6),)
    assert entry.uncovered_ranges == ((7, 10),)
    assert entry.covered_residue_count == 6
    assert entry.coverage_fraction == 0.6
    assert entry.covered_peptides == ("ABCD", "CDEF")
    assert entry.unmatched_peptides == ("ZZZ",)
    assert report.uncovered_regions[0].start_residue == 7
    assert report.uncovered_regions[0].end_residue == 10

    coordinates = report.peptide_coordinates
    assert coordinates[0].coordinate_status is ProteinCoverageCoordinateStatus.MATCHED
    assert coordinates[0].canonical_peptide == "ABCD"
    assert coordinates[0].start_residue == 1
    assert coordinates[0].end_residue == 4
    assert coordinates[1].canonical_peptide == "CDEF"
    assert coordinates[1].start_residue == 3
    assert coordinates[1].end_residue == 6
    assert coordinates[2].coordinate_status is ProteinCoverageCoordinateStatus.UNMATCHED
    assert coordinates[2].canonical_peptide == "ZZZ"
    assert coordinates[2].start_residue is None


def test_protein_coverage_report_preserves_repeated_peptide_coordinate_occurrences() -> (
    None
):
    records = (
        PsmRecord(
            spectrum_id="scan=repeat-1",
            peptide="ABCD",
            canonical_peptide="ABCD",
            charge=2,
            score=75.0,
            q_value=0.01,
            protein_refs=("P20002",),
        ),
    )

    report = build_protein_coverage_report(
        records,
        protein_sequences={"P20002": "MABCDABCDZ"},
    )

    entry = report.entries[0]
    assert entry.covered_ranges == ((2, 9),)
    assert entry.uncovered_ranges == ((1, 1), (10, 10))
    coordinates = report.peptide_coordinates
    assert len(coordinates) == 2
    assert coordinates[0].occurrence_index == 1
    assert coordinates[0].start_residue == 2
    assert coordinates[0].end_residue == 5
    assert coordinates[1].occurrence_index == 2
    assert coordinates[1].start_residue == 6
    assert coordinates[1].end_residue == 9


def test_protein_coverage_renderers_emit_uncovered_and_coordinate_ledgers() -> None:
    records = (
        PsmRecord(
            spectrum_id="scan=ledger-1",
            peptide="ABCD",
            canonical_peptide="ABCD",
            charge=2,
            score=50.0,
            q_value=0.01,
            protein_refs=("P10001",),
        ),
        PsmRecord(
            spectrum_id="scan=ledger-2",
            peptide="ZZZ",
            canonical_peptide="ZZZ",
            charge=2,
            score=48.0,
            q_value=0.03,
            protein_refs=("P10001",),
        ),
    )

    report = build_protein_coverage_report(
        records,
        protein_sequences={"P10001": "ABCDEFGHIK"},
    )

    uncovered_tsv = render_protein_coverage_uncovered_regions_tsv(report)
    coordinates_tsv = render_protein_coverage_peptide_coordinates_tsv(report)

    assert (
        "protein_ref\tregion_index\tstart_residue\tend_residue\tresidue_count"
        in uncovered_tsv
    )
    assert "P10001\t1\t5\t10\t6" in uncovered_tsv
    assert (
        "protein_ref\tcanonical_peptide\tpeptide_sequence\tcoordinate_status"
        in coordinates_tsv
    )
    assert (
        "P10001\tABCD\tABCD\tmatched\t1\t1\t4\ttrue\tfalse\t50.0\t0.01\ttarget\tfalse"
        in coordinates_tsv
    )
    assert (
        "P10001\tZZZ\tZZZ\tunmatched\t\t\t\ttrue\tfalse\t48.0\t0.03\ttarget\tfalse"
        in coordinates_tsv
    )
