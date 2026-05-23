# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm.site_annotation_import import parse_ptm_site_annotation_tsv


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def test_ptm_site_annotation_import_preserves_known_biology_and_rejected_rows() -> None:
    report = parse_ptm_site_annotation_tsv(_fixture_path("ptm_site_annotations.tsv"))

    assert report.total_rows == 6
    assert report.summary.accepted_record_count == 5
    assert report.summary.rejected_row_count == 1
    assert report.summary.species_count == 2
    assert report.summary.kinase_annotated_count == 5
    assert report.summary.phosphatase_annotated_count == 5
    assert report.summary.pathway_annotated_count == 5
    record = next(
        entry
        for entry in report.accepted_records
        if entry.protein_ref == "P11111" and entry.position == 5
    )
    assert record.species == "Homo sapiens"
    assert record.site_function == "activation-linked phosphosite"
    assert record.kinases == ("AKT1", "MTOR")
    assert record.phosphatases == ("PPP2CA",)
    assert record.pathways == ("PI3K signaling", "growth control")
    assert report.rejected_rows[0].issues[0].code == "invalid_position"
