# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    PtmSiteContextStatus,
    build_ptm_site_context_report,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.ptm.context_annotation import parse_ptm_site_context_tsv
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _protein_sequences() -> dict[str, str]:
    fasta = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "fasta"
        / "ptm_sites.fasta"
    )
    report = parse_fasta_document(fasta.read_text(), mode=FastaParseMode.STRICT)
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def test_ptm_site_context_parser_preserves_region_annotations_and_rejected_rows() -> (
    None
):
    report = parse_ptm_site_context_tsv(_fixture_path("ptm_site_context.tsv"))

    assert report.total_rows == 6
    assert report.summary.accepted_record_count == 5
    assert report.summary.rejected_row_count == 1
    assert report.summary.distinct_protein_ref_count == 2
    assert report.summary.domain_record_count == 2
    assert report.summary.disorder_record_count == 2
    assert report.summary.transmembrane_record_count == 1
    assert report.summary.active_site_record_count == 2
    assert report.summary.motif_record_count == 4
    assert report.summary.conservation_record_count == 5
    assert report.rejected_rows[0].issues[0].code == "missing_context_fields"


def test_ptm_site_context_report_preserves_annotations_and_explicit_outside_sites() -> (
    None
):
    evidence = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    context = parse_ptm_site_context_tsv(_fixture_path("ptm_site_context.tsv"))

    report = build_ptm_site_context_report(site_table, context.accepted_records)

    assert report.summary.site_count == 5
    assert report.summary.context_annotated_site_count == 4
    assert report.summary.outside_annotation_site_count == 1
    annotated = next(
        entry for entry in report.entries if entry.site_key == "P11111:S5:Phospho"
    )
    assert annotated.context_status is PtmSiteContextStatus.CONTEXT_ANNOTATED
    assert annotated.matched_context_record_count == 2
    assert annotated.domain_names == ("activation_segment",)
    assert annotated.disorder_regions == ("surface_loop",)
    assert annotated.active_site_labels == ("catalytic_acceptor",)
    assert annotated.motif_names == ("SP_acceptor", "SP_motif")
    assert annotated.conservation_scores == (0.97, 0.99)
    assert annotated.max_conservation_score == 0.99
    assert annotated.source_names == ("Curator", "InterPro")

    transmembrane = next(
        entry for entry in report.entries if entry.site_key == "P22222:S4:Phospho"
    )
    assert transmembrane.transmembrane_regions == ("helix_1",)
    assert transmembrane.context_status is PtmSiteContextStatus.CONTEXT_ANNOTATED

    outside = next(
        entry for entry in report.entries if entry.site_key == "Q9DEC1:S5:Phospho"
    )
    assert outside.context_status is PtmSiteContextStatus.OUTSIDE_PROVIDED_ANNOTATIONS
    assert outside.matched_context_record_count == 0
    assert outside.domain_names == ()
    assert outside.conservation_scores == ()
