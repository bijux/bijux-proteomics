# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics import interpretation
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def _fasta_fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "fasta" / name


def test_interpretation_package_exports_complete_protein_annotation_surface() -> None:
    protein_table = interpretation.parse_protein_reference_table(
        _fixture_path("protein_annotation_input.tsv")
    )
    custom_table = interpretation.parse_protein_annotation_table(
        _fixture_path("protein_annotation_custom.tsv")
    )
    fasta_report = parse_fasta_document(
        _fasta_fixture_path("valid_records.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    mapping_report = interpretation.build_protein_annotation_mapping_report(
        protein_table.accepted_entries
        + (
            interpretation.ProteinReferenceEntry(
                row_number=99,
                source_row_id="row-missing",
                input_protein_ref="UNKNOWN123",
                protein_ref="UNKNOWN123",
            ),
        ),
        fasta_report.accepted_records,
        custom_annotations=custom_table.accepted_records
        + (
            interpretation.ProteinAnnotationRecord(
                protein_ref="Q99999",
                gene_symbol="CUST1",
            ),
        ),
    )

    assert hasattr(interpretation, "render_protein_annotation_tsv")
    rendered = interpretation.render_protein_annotation_tsv(mapping_report)

    assert "annotation_status" in rendered.splitlines()[0]
    assert "UNKNOWN123" in rendered
    assert "unmapped" in rendered


def test_interpretation_package_exports_protein_set_enrichment_surface() -> None:
    foreground = interpretation.parse_protein_reference_table(
        _fixture_path("protein_set_enrichment_foreground.tsv")
    )
    protein_sets = interpretation.parse_protein_set_table(
        _fixture_path("protein_set_enrichment.tsv")
    )
    report = interpretation.build_protein_set_enrichment_report(
        foreground.accepted_entries,
        protein_sets.accepted_records,
        policy=interpretation.ProteinSetEnrichmentPolicy(
            missing_background_policy=(
                interpretation.ProteinSetEnrichmentMissingBackgroundPolicy.MEMBERSHIP_UNIVERSE
            ),
            max_adjusted_p_value=1.0,
            min_enrichment_ratio=0.0,
        ),
    )

    assert hasattr(interpretation, "render_protein_set_enrichment_tsv")
    rendered = interpretation.render_protein_set_enrichment_tsv(report)

    assert "set_category" in rendered.splitlines()[0]
    assert "nucleus" in rendered
