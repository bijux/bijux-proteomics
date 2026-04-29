from __future__ import annotations

from bijux_proteomics import PeptideDigestionMode, digest_sequence


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


def test_digest_sequence_supports_missed_cleavages() -> None:
    peptides = digest_sequence(
        "AKAAKAAK",
        source_accession="missed-cleavage-test",
        missed_cleavages=1,
    )

    assert [peptide.sequence for peptide in peptides] == [
        "AK",
        "AKAAK",
        "AAK",
        "AAKAAK",
        "AAK",
    ]
    assert [peptide.missed_cleavages for peptide in peptides] == [0, 1, 0, 1, 0]


def test_digest_sequence_supports_semi_specific_mode() -> None:
    peptides = digest_sequence(
        "AKAAK",
        source_accession="semi-specific-test",
        mode=PeptideDigestionMode.SEMI_SPECIFIC,
    )

    sequences = {peptide.sequence for peptide in peptides}
    assert {"AK", "AKAAK", "K", "KAAK", "AAK"} <= sequences
    assert any(peptide.cleavage_type == "semi_specific" for peptide in peptides)
