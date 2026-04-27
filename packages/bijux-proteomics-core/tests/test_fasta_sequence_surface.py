from __future__ import annotations

import pytest

from bijux_proteomics import parse_fasta_records, parse_uniprot_accession


def test_parse_fasta_records_preserves_header_identity() -> None:
    records = parse_fasta_records(
        ">sp|P12345|TP53_HUMAN Cellular tumor antigen p53\nMEEPQSDPSV\n"
    )

    assert len(records) == 1
    assert records[0].identifier == "sp|P12345|TP53_HUMAN"
    assert records[0].description == "Cellular tumor antigen p53"
    assert records[0].residues == "MEEPQSDPSV"


def test_parse_fasta_records_requires_header_first() -> None:
    with pytest.raises(ValueError, match="begin with a header"):
        parse_fasta_records("MEEPQSDPSV")


def test_parse_fasta_records_rejects_noncanonical_residues() -> None:
    with pytest.raises(ValueError, match="non-canonical amino-acid symbols"):
        parse_fasta_records(">tp53\nMEEPQSDPSVX\n")


def test_parse_uniprot_accession_preserves_isoform_suffix() -> None:
    accession = parse_uniprot_accession("P12345-2")

    assert accession.accession == "P12345"
    assert accession.isoform == 2


def test_parse_uniprot_accession_rejects_invalid_tokens() -> None:
    with pytest.raises(ValueError, match="valid UniProt accession"):
        parse_uniprot_accession("TP53_HUMAN")
