# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
from typing import cast

from bijux_proteomics.ptm import (
    PtmSiteEntry,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.ptm.review import evaluate_ptm_site_fdr_boundary
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


def _site_entries() -> tuple[PtmSiteEntry, ...]:
    parsed = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records, protein_sequences=_protein_sequences()
    )
    return cast(tuple[PtmSiteEntry, ...], build_ptm_site_table(mappings))


def test_ptm_site_fdr_boundary_supports_site_specific_confidence() -> None:
    report = evaluate_ptm_site_fdr_boundary(
        _site_entries(),
        requested_confidence_family="ptm_site",
        has_site_level_decoys=True,
    )

    assert report.disposition.value == "supported"
    assert report.preserve_site_level is True
    assert report.supporting_site_count >= 1
    assert report.issues == ()


def test_ptm_site_fdr_boundary_refuses_non_site_confidence() -> None:
    report = evaluate_ptm_site_fdr_boundary(
        _site_entries(),
        requested_confidence_family="protein_group",
        has_site_level_decoys=False,
    )

    assert report.disposition.value == "refused"
    assert report.preserve_site_level is False
    assert {issue.code for issue in report.issues} == {
        "non_site_confidence_family",
        "missing_site_level_decoy_support",
    }
