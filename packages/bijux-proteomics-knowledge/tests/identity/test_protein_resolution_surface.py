# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics.interpretation.annotation_packs import load_annotation_pack
from bijux_proteomics_knowledge.identity.proteins import (
    ProteinIdentityResolutionStatus,
    render_protein_id_resolution_tsv,
    resolve_protein_ids,
)


def _write_annotation_pack(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "pack_name": "identity_fixture",
                "protein_features": [
                    {
                        "protein_ref": "P04637",
                        "gene_symbol": "TP53",
                        "organism": "Homo sapiens",
                        "annotation_identifier": "ENSP00000269305",
                    },
                    {
                        "protein_ref": "Q9Y243",
                        "gene_symbol": "TP53",
                        "organism": "Mus musculus",
                        "annotation_identifier": "ENSMUSP00000021000",
                    },
                    {
                        "protein_ref": "P15056",
                        "gene_symbol": "BRAF",
                        "organism": "Homo sapiens",
                        "annotation_identifier": "ENSP00000288602",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_resolve_protein_ids_keeps_ambiguous_aliases_explicit(
    tmp_path: Path,
) -> None:
    annotation_pack = load_annotation_pack(
        _write_annotation_pack(tmp_path / "annotation_pack.json")
    )

    entries = resolve_protein_ids(
        ("TP53", "P04637", "ENSP00000288602", "UNKNOWN"),
        annotation_pack,
    )

    tp53_rows = [entry for entry in entries if entry.input_id == "TP53"]
    assert len(tp53_rows) == 2
    assert {entry.resolved_accession for entry in tp53_rows} == {"P04637", "Q9Y243"}
    assert {entry.resolution_status for entry in tp53_rows} == {
        ProteinIdentityResolutionStatus.AMBIGUOUS_ALIAS
    }
    assert {entry.ambiguity_count for entry in tp53_rows} == {2}

    p04637_row = next(entry for entry in entries if entry.input_id == "P04637")
    assert p04637_row.resolution_status is ProteinIdentityResolutionStatus.EXACT_ACCESSION
    assert p04637_row.gene == "TP53"

    ensp_row = next(
        entry for entry in entries if entry.input_id == "ENSP00000288602"
    )
    assert ensp_row.resolved_accession == "P15056"
    assert (
        ensp_row.resolution_status
        is ProteinIdentityResolutionStatus.ANNOTATION_IDENTIFIER
    )

    unresolved_row = next(entry for entry in entries if entry.input_id == "UNKNOWN")
    assert unresolved_row.resolved_accession is None
    assert unresolved_row.resolution_status is ProteinIdentityResolutionStatus.UNRESOLVED
    assert unresolved_row.ambiguity_count == 0


def test_resolve_protein_ids_respects_species_filter(
    tmp_path: Path,
) -> None:
    annotation_pack = load_annotation_pack(
        _write_annotation_pack(tmp_path / "annotation_pack.json")
    )

    entries = resolve_protein_ids(("TP53",), annotation_pack, species="Homo sapiens")
    rendered = render_protein_id_resolution_tsv(entries)

    assert len(entries) == 1
    assert entries[0].resolved_accession == "P04637"
    assert entries[0].resolution_status is ProteinIdentityResolutionStatus.GENE_SYMBOL
    assert entries[0].ambiguity_count == 1
    assert "resolution_status" in rendered
    assert "P04637\tTP53\tHomo sapiens\tgene_symbol\t1" in rendered
