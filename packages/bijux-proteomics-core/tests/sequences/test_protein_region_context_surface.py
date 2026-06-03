# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.sequences import (
    FastaParseMode,
    ProteinPeptideRegionReference,
    ProteinRegionContextStatus,
    ProteinSiteRegionReference,
    build_protein_peptide_region_context_report,
    build_protein_site_region_context_report,
    parse_fasta_document,
    parse_protein_region_context_tsv,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "sequences" / name


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


def test_protein_region_context_parser_preserves_functional_regions_and_rejected_rows() -> (
    None
):
    report = parse_protein_region_context_tsv(
        _fixture_path("protein_region_context.tsv")
    )

    assert report.total_rows == 6
    assert report.summary.accepted_record_count == 5
    assert report.summary.rejected_row_count == 1
    assert report.summary.distinct_protein_ref_count == 2
    assert report.summary.domain_record_count == 2
    assert report.summary.signal_peptide_record_count == 1
    assert report.summary.transmembrane_record_count == 1
    assert report.summary.disorder_record_count == 2
    assert report.summary.low_complexity_record_count == 1
    assert report.summary.active_site_record_count == 2
    assert report.summary.binding_region_record_count == 3
    assert report.summary.motif_record_count == 1
    assert report.rejected_rows[0].issues[0].code == "missing_context_fields"


def test_protein_region_context_site_report_preserves_domain_signal_and_binding_support() -> (
    None
):
    context = parse_protein_region_context_tsv(
        _fixture_path("protein_region_context.tsv")
    )
    report = build_protein_site_region_context_report(
        (
            ProteinSiteRegionReference(
                site_key="P11111:S5:Phospho",
                protein_ref="P11111",
                position=5,
            ),
            ProteinSiteRegionReference(
                site_key="P11111:S17:Phospho",
                protein_ref="P11111",
                position=17,
            ),
            ProteinSiteRegionReference(
                site_key="Q9DEC1:S5:Phospho",
                protein_ref="Q9DEC1",
                position=5,
            ),
        ),
        context.accepted_records,
    )

    assert report.summary.site_count == 3
    assert report.summary.context_annotated_site_count == 2
    assert report.summary.outside_annotation_site_count == 1
    annotated = next(
        entry for entry in report.entries if entry.site_key == "P11111:S5:Phospho"
    )
    assert annotated.context_status is ProteinRegionContextStatus.CONTEXT_ANNOTATED
    assert annotated.domain_names == ("regulatory_head",)
    assert annotated.signal_peptides == ("leader_1",)
    assert annotated.binding_regions == ("14-3-3_site",)
    assert annotated.active_site_labels == ("SP_acceptor",)
    assert annotated.motif_names == ("SP_motif",)
    assert any(
        region.supporting_evidence_refs == ("P11111:S5:Phospho",)
        for region in annotated.functional_regions
    )
    outside = next(
        entry for entry in report.entries if entry.site_key == "Q9DEC1:S5:Phospho"
    )
    assert (
        outside.context_status
        is ProteinRegionContextStatus.OUTSIDE_PROVIDED_ANNOTATIONS
    )


def test_protein_region_context_peptide_report_preserves_sequence_spans_and_unmapped_rows() -> (
    None
):
    context = parse_protein_region_context_tsv(
        _fixture_path("protein_region_context.tsv")
    )
    report = build_protein_peptide_region_context_report(
        (
            ProteinPeptideRegionReference(
                peptide_key="P11111:SPEPTIDEK",
                protein_ref="P11111",
                peptide_sequence="SPEPTIDEK",
            ),
            ProteinPeptideRegionReference(
                peptide_key="P22222:MPEPTIDEY",
                protein_ref="P22222",
                peptide_sequence="MPEPTIDEY",
            ),
            ProteinPeptideRegionReference(
                peptide_key="P11111:DOESNOTMAP",
                protein_ref="P11111",
                peptide_sequence="DOESNOTMAP",
            ),
        ),
        protein_sequences=_protein_sequences(),
        context_records=context.accepted_records,
    )

    assert report.summary.peptide_count == 3
    assert report.summary.context_annotated_peptide_count == 2
    assert report.summary.unmapped_peptide_count == 1
    p11111 = next(
        entry for entry in report.entries if entry.peptide_key == "P11111:SPEPTIDEK"
    )
    assert p11111.spans[0].start == 5
    assert p11111.spans[0].end == 13
    assert p11111.context_status is ProteinRegionContextStatus.CONTEXT_ANNOTATED
    assert p11111.signal_peptides == ("leader_1",)
    assert p11111.binding_regions == ("14-3-3_site",)
    p22222 = next(
        entry for entry in report.entries if entry.peptide_key == "P22222:MPEPTIDEY"
    )
    assert p22222.domain_names == ("catalytic_tail",)
    assert p22222.active_site_labels == ("catalytic_tyrosine",)
    unmapped = next(
        entry for entry in report.entries if entry.peptide_key == "P11111:DOESNOTMAP"
    )
    assert unmapped.context_status is ProteinRegionContextStatus.UNMAPPED_TO_SEQUENCE
    assert unmapped.functional_regions == ()
