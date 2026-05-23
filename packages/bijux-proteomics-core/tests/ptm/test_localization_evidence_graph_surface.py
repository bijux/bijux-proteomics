# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.ptm.review import (
    build_ptm_site_localization_evidence_graph,
)
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


def test_ptm_site_localization_evidence_graph_links_core_coordinates_and_fragments() -> (
    None
):
    parsed = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records, protein_sequences=_protein_sequences()
    )

    graph = build_ptm_site_localization_evidence_graph(
        parsed.accepted_records,
        mappings,
        fragment_ion_support_by_spectrum={
            "scan=ptm-001": ("b5", "y7"),
            "scan=ptm-002": ("y6",),
            "scan=ptm-005": ("b3-H2O",),
        },
    )

    target = next(node for node in graph.nodes if node.site_key == "P11111:S5:Phospho")
    ambiguous = next(node for node in graph.nodes if node.ambiguous)

    assert graph.source_record_count == len(parsed.accepted_records)
    assert target.psm_spectrum_ids
    assert target.peptide_site_indices == (1,)
    assert target.candidate_protein_positions == (5,)
    assert target.localization_probability > 0.95
    assert target.localization_probability_source == "normalized_score"
    assert target.localization_tier == "supported"
    assert target.fragment_ions == ("b5", "y6", "y7")
    assert target.site_determining_ions == ()
    assert target.supported_site_determining_ions == ()

    assert ambiguous.candidate_protein_positions
    assert ambiguous.localized_peptides
    assert ambiguous.site_determining_ions
    assert ambiguous.supported_site_determining_ions == ()
