# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import (
    PathwayEnrichmentCorrectionPolicy,
    apply_pathway_enrichment_multiple_testing,
    build_pathway_enrichment_report,
    parse_pathway_membership_table,
    parse_protein_annotation_table,
    parse_protein_reference_table,
    render_pathway_enrichment_entry_tsv,
    render_pathway_enrichment_summary_tsv,
    render_pathway_unresolved_member_tsv,
    render_rejected_pathway_membership_tsv,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_render_pathway_enrichment_ledgers() -> None:
    foreground = parse_protein_reference_table(_fixture_path("pathway_foreground.tsv"))
    background = parse_protein_reference_table(_fixture_path("pathway_background.tsv"))
    pathway_memberships = parse_pathway_membership_table(
        _fixture_path("pathway_memberships.tsv")
    )
    fasta_report = parse_fasta_document(
        _fixture_path("protein_annotation_reference.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    custom_annotations = parse_protein_annotation_table(
        _fixture_path("protein_annotation_custom.tsv")
    )
    report = apply_pathway_enrichment_multiple_testing(
        build_pathway_enrichment_report(
            foreground.accepted_entries,
            background.accepted_entries,
            pathway_memberships.accepted_records,
            fasta_records=fasta_report.accepted_records,
            custom_annotations=custom_annotations.accepted_records,
        ),
        policy=PathwayEnrichmentCorrectionPolicy(
            max_adjusted_p_value=1.0,
            min_enrichment_ratio=1.0,
        ),
    )

    summary_tsv = render_pathway_enrichment_summary_tsv(report)
    entry_tsv = render_pathway_enrichment_entry_tsv(report)
    unresolved_tsv = render_pathway_unresolved_member_tsv(report)
    rejected_tsv = render_rejected_pathway_membership_tsv(pathway_memberships)

    assert summary_tsv.splitlines()[0].startswith("foreground_size\tbackground_size")
    assert "hsa04115" in entry_tsv
    assert "background\tQ88888\t" in unresolved_tsv
    assert (
        "duplicate pathway membership for custom:stress and gene member TP53"
        in rejected_tsv
    )
