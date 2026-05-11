from __future__ import annotations

from bijux_proteomics_dev.tools.manage_examples import parse_fasta_per_chain


def test_parse_fasta_per_chain_expands_combined_chain_headers() -> None:
    fasta_text = (
        ">4KRP_1|Chains A and B|example\nMPEPTIDE\n>4KRP_2|Chain C|example\nMSECOND\n"
    )

    mapping = parse_fasta_per_chain(fasta_text)

    assert mapping == {
        "A": "MPEPTIDE",
        "B": "MPEPTIDE",
        "C": "MSECOND",
    }


def test_parse_fasta_per_chain_rejects_unrecognized_headers() -> None:
    fasta_text = ">4KRP:A\nMPEPTIDE\n"

    mapping = parse_fasta_per_chain(fasta_text)

    assert mapping == {}
