# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.lab import (
    DigestionPeptideObservation,
    DigestionStatus,
    classify_digestion,
    render_digestion_diagnosis_tsv,
)
from bijux_proteomics.study.lab_protocol_context import DigestionEnzyme


def test_classify_digestion_flags_wrong_declared_enzyme_as_mismatch() -> None:
    rows = classify_digestion(
        (
            DigestionPeptideObservation(
                sample_id="sample_tryptic",
                peptide_sequence="PEPTIDER",
                left_flank=None,
                right_flank="A",
            ),
            DigestionPeptideObservation(
                sample_id="sample_tryptic",
                peptide_sequence="AAAQK",
                left_flank=None,
                right_flank="L",
            ),
            DigestionPeptideObservation(
                sample_id="sample_tryptic",
                peptide_sequence="LMNQR",
                left_flank=None,
                right_flank="A",
            ),
            DigestionPeptideObservation(
                sample_id="sample_mismatch",
                peptide_sequence="ARAAK",
                left_flank=None,
                right_flank="L",
            ),
            DigestionPeptideObservation(
                sample_id="sample_mismatch",
                peptide_sequence="QQRAK",
                left_flank=None,
                right_flank="A",
            ),
            DigestionPeptideObservation(
                sample_id="sample_mismatch",
                peptide_sequence="LMRAK",
                left_flank=None,
                right_flank="Q",
            ),
        ),
        declared_enzyme=DigestionEnzyme.TRYPSIN,
    )
    lookup = {row.sample_id: row for row in rows}

    assert lookup["sample_tryptic"].digestion_status is DigestionStatus.PASS

    mismatch = lookup["sample_mismatch"]
    assert mismatch.digestion_status is DigestionStatus.ENZYME_MISMATCH
    assert mismatch.missed_cleavage_rate == 1.0
    assert mismatch.semi_specific_rate == 0.0
    assert mismatch.non_specific_rate == 0.0


def test_classify_digestion_separates_low_specificity_and_inefficient_digestion() -> None:
    rows = classify_digestion(
        (
            DigestionPeptideObservation(
                sample_id="sample_low_specificity",
                peptide_sequence="PEPTIDEA",
                left_flank="A",
                right_flank="A",
            ),
            DigestionPeptideObservation(
                sample_id="sample_low_specificity",
                peptide_sequence="QQQQA",
                left_flank="G",
                right_flank="V",
            ),
            DigestionPeptideObservation(
                sample_id="sample_inefficient",
                peptide_sequence="AAKAEPTR",
                left_flank=None,
                right_flank="A",
            ),
            DigestionPeptideObservation(
                sample_id="sample_inefficient",
                peptide_sequence="LMRQQK",
                left_flank=None,
                right_flank="G",
            ),
            DigestionPeptideObservation(
                sample_id="sample_inefficient",
                peptide_sequence="PRKAAAR",
                left_flank=None,
                right_flank="L",
            ),
            DigestionPeptideObservation(
                sample_id="sample_inefficient",
                peptide_sequence="QQRAAK",
                left_flank=None,
                right_flank="V",
            ),
        ),
        declared_enzyme="trypsin",
    )
    rendered = render_digestion_diagnosis_tsv(rows)
    lookup = {row.sample_id: row for row in rows}

    assert (
        lookup["sample_low_specificity"].digestion_status
        is DigestionStatus.LOW_SPECIFICITY
    )
    assert lookup["sample_low_specificity"].non_specific_rate == 1.0

    assert (
        lookup["sample_inefficient"].digestion_status
        is DigestionStatus.INEFFICIENT_DIGESTION
    )
    assert lookup["sample_inefficient"].missed_cleavage_rate == 1.0
    assert lookup["sample_inefficient"].non_specific_rate == 0.0

    assert rendered.startswith(
        "sample_id\tmissed_cleavage_rate\tsemi_specific_rate\tnon_specific_rate\tdigestion_status\n"
    )
    assert "sample_mismatch" not in rendered
