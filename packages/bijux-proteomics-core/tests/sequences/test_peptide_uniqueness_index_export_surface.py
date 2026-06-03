# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.sequences import (
    FastaParseMode,
    PeptideDigestionMode,
    build_peptide_uniqueness_index,
    export_peptide_uniqueness_index_tsv,
    parse_fasta_document,
    render_peptide_uniqueness_index_tsv,
)


def test_peptide_uniqueness_index_export_renders_governed_tsv(tmp_path: Path) -> None:
    report = parse_fasta_document(
        (
            ">sp|P11111|TP53_HUMAN Canonical GN=TP53\nAKAK\n"
            ">sp|P11111-2|TP53_HUMAN Isoform GN=TP53\nAKAK\n"
        ),
        mode=FastaParseMode.STRICT,
    )
    index = build_peptide_uniqueness_index(
        report.accepted_records,
        protease="trypsin",
        digestion_mode=PeptideDigestionMode.FULL,
    )

    rendered = render_peptide_uniqueness_index_tsv(index)
    out_path = export_peptide_uniqueness_index_tsv(
        index,
        tmp_path / "peptide_uniqueness_index.tsv",
    )

    assert rendered.startswith("peptide_sequence\tlookup_sequence\t")
    assert "\tisoform_shared\n" in rendered
    assert out_path.read_text() == rendered
