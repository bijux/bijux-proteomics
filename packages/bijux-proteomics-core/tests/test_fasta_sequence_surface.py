from __future__ import annotations

import pytest

from bijux_proteomics import parse_fasta_records


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
