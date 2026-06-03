# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.chemistry import (
    ModifiedPeptideNotationDialect,
    build_modified_peptide_parse_review,
    modification_registry,
    parse_modified_peptide_notation,
)


def test_modified_peptide_parser_builds_canonical_record_from_bijux_notation() -> None:
    review = build_modified_peptide_parse_review(
        "PEPK[Acetyl]IDE",
        dialect=ModifiedPeptideNotationDialect.BIJUX,
        registry=modification_registry(),
    )

    assert review.canonical_notation == "PEPK[AcetylLys]IDE"
    assert review.modified_peptide_record.record_id == "PEPK[AcetylLys]IDE"
    assert review.modified_peptide_record.peptide_sequence == "PEPKIDE"
    assert review.modified_peptide_record.modification_names == ("AcetylLys",)
    assert review.unknown_tokens == ()


def test_modified_peptide_parser_keeps_terminal_and_lysine_acetylation_distinct() -> (
    None
):
    terminal = parse_modified_peptide_notation(
        "[Acetyl]-PEPKIDE",
        dialect=ModifiedPeptideNotationDialect.BIJUX,
        registry=modification_registry(),
    )
    lysine = parse_modified_peptide_notation(
        "PEPK[Acetyl]IDE",
        dialect=ModifiedPeptideNotationDialect.BIJUX,
        registry=modification_registry(),
    )

    assert terminal.canonical_notation == "[Acetyl]-PEPKIDE"
    assert lysine.canonical_notation == "PEPK[AcetylLys]IDE"
    assert terminal.modifications[0].site.value == "peptide_n_term"
    assert lysine.modifications[0].site_index == 4
    assert terminal.modifications[0].name != lysine.modifications[0].name
