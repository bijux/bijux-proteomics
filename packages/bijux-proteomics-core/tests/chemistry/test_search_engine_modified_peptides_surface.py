# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_proteomics.chemistry import (
    SearchEngineModifiedPeptideDialect,
    build_search_engine_modified_peptide_report,
    canonicalize_search_engine_modified_peptide,
    modification_registry,
    parse_search_engine_modified_peptide,
)


def _chemistry_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "chemistry" / name


def test_search_engine_modified_peptide_cases_normalize_to_owned_canonical_surface() -> (
    None
):
    cases = json.loads(
        _chemistry_fixture("search_engine_modified_peptide_cases.json").read_text()
    )
    registry = modification_registry()

    for case in cases:
        parsed = parse_search_engine_modified_peptide(
            case["notation"],
            dialect=case["dialect"],
            registry=registry,
        )
        report = build_search_engine_modified_peptide_report(
            case["notation"],
            dialect=case["dialect"],
            registry=registry,
        )

        assert parsed.sequence == case["residue_sequence"]
        assert parsed.at_protein_n_term is case["at_protein_n_term"]
        assert parsed.at_protein_c_term is case["at_protein_c_term"]
        assert (
            canonicalize_search_engine_modified_peptide(
                case["notation"],
                dialect=case["dialect"],
                registry=registry,
            )
            == case["expected"]
        )
        assert report.canonical_notation == case["expected"]
        assert report.residue_sequence == case["residue_sequence"]
        assert report.dialect is SearchEngineModifiedPeptideDialect(case["dialect"])

        observed_sites = [
            modification.site_index
            if modification.site_index is not None
            else modification.site.value
            for modification in parsed.modifications
        ]
        assert observed_sites == case["sites"]


def test_search_engine_modified_peptide_parser_rejects_unknown_maxquant_suffix() -> None:
    with pytest.raises(ValueError, match="unsupported MaxQuant modification token"):
        parse_search_engine_modified_peptide(
            "_PEPTIDE(Phospho (Unknown term))_",
            dialect="maxquant",
            registry=modification_registry(),
        )


def test_search_engine_modified_peptide_parser_rejects_unterminated_bracket_token() -> (
    None
):
    with pytest.raises(ValueError, match="unterminated bracket modification token"):
        parse_search_engine_modified_peptide(
            "M[15.994915PEPTIDE",
            dialect="comet",
            registry=modification_registry(),
        )
