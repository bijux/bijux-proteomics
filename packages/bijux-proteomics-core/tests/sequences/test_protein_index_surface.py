# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.sequences.protein_index import (
    build_protein_index,
    load_protein_index,
    lookup_accession,
    lookup_peptide_entry,
    lookup_peptide_proteins,
    lookup_protein_peptides,
    lookup_protein_sequence,
)


def test_build_protein_index_reloads_with_identical_protein_and_peptide_queries(
    tmp_path: Path,
) -> None:
    index_path = tmp_path / "protein_index.json"
    fasta_path = tmp_path / "index_input.fasta"
    fasta_path.write_text(
        (
            ">sp|P11111|ALPHA_HUMAN Alpha GN=ALPHA\nMPEPTIDEK\n"
            ">sp|P11111-2|ALPHA_HUMAN Isoform GN=ALPHA\nMPEPTIDEK\n"
            ">sp|P22222|BETA_HUMAN Beta GN=BETA\nAAAKPEPTIDER\n"
        ),
        encoding="utf-8",
    )

    built = build_protein_index(
        fasta_path,
        enzyme="trypsin",
        missed_cleavages=0,
        out_path=index_path,
    )
    reloaded = load_protein_index(index_path)

    assert index_path.exists()
    assert built.digest_policy.protease == "trypsin"
    assert reloaded.digest_policy == built.digest_policy
    assert reloaded.source_sha256 == built.source_sha256
    assert reloaded.document_schema.content_hash == built.document_schema.content_hash
    assert reloaded.summary == built.summary
    assert lookup_peptide_proteins(reloaded, "MPEPTIDEK") == lookup_peptide_proteins(
        built, "MPEPTIDEK"
    )
    assert lookup_protein_peptides(reloaded, "P11111") == lookup_protein_peptides(
        built, "P11111"
    )
    assert lookup_protein_sequence(reloaded, "P22222") == lookup_protein_sequence(
        built, "P22222"
    )
    assert lookup_accession(reloaded, "P11111-2") == lookup_accession(built, "P11111-2")


def test_build_protein_index_preserves_decoy_and_contaminant_flags(
    tmp_path: Path,
) -> None:
    built = build_protein_index(
        (
            ">sp|P11111|ALPHA_HUMAN Alpha GN=ALPHA\nMPEPTIDEK\n"
            ">DECOY_sp|P22222|DECOY_BETA Decoy GN=BETA\nMPEPTIDEK\n"
            ">sp|P33333|KERATIN_CONTAM Keratin CONTAMINANT\nKERATINPEPK\n"
        ),
        enzyme="trypsin",
        missed_cleavages=0,
        out_path=tmp_path / "protein_index_surface.json",
    )

    shared_entry = lookup_peptide_entry(built, "MPEPTIDEK")
    contaminant_entry = lookup_accession(built, "P33333")
    decoy_entry = lookup_accession(built, "DECOY_P22222")

    assert shared_entry is not None
    assert shared_entry.contains_decoy_parent is True
    assert shared_entry.contains_contaminant_parent is False
    assert shared_entry.protein_accessions == ("DECOY_P22222", "P11111")
    assert contaminant_entry is not None
    assert contaminant_entry.contaminant is True
    assert decoy_entry is not None
    assert decoy_entry.decoy is True
    assert built.summary.decoy_protein_count == 1
    assert built.summary.contaminant_protein_count == 1
