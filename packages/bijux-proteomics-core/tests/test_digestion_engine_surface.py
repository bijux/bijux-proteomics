from __future__ import annotations

from bijux_proteomics import digest_sequence


def test_digest_sequence_performs_full_tryptic_cleavage() -> None:
    peptides = digest_sequence(
        "MKWVTFISLLFLFSSAYSRGVFRRDTHKSEIAHRFKDLGE",
        source_accession="ALBU_HUMAN",
    )

    assert [peptide.sequence for peptide in peptides] == [
        "MK",
        "WVTFISLLFLFSSAYSR",
        "GVFR",
        "R",
        "DTHK",
        "SEIAHR",
        "FK",
        "DLGE",
    ]
    assert peptides[0].start == 1
    assert peptides[1].start == 3
    assert all(peptide.protease == "trypsin" for peptide in peptides)


def test_digest_sequence_honors_trypsin_proline_block() -> None:
    peptides = digest_sequence("AKRPQKAAAR", source_accession="block-test")

    assert [peptide.sequence for peptide in peptides] == ["AK", "RPQK", "AAAR"]
