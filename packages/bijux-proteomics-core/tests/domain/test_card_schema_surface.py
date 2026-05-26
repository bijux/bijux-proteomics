# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from bijux_proteomics.domain import (
    ConfidenceTier,
    STANDARD_CARD_TSV_COLUMNS,
    StandardCardEntry,
    StandardCardKind,
    StandardCardSubjectKind,
    load_standard_card_tsv,
    render_standard_card_row,
)


def test_shared_card_schema_round_trips_governed_entries(tmp_path: Path) -> None:
    entry = StandardCardEntry(
        card_id="protein-card:P12345",
        card_kind=StandardCardKind.PROTEIN,
        subject_kind=StandardCardSubjectKind.PROTEIN,
        subject_id="P12345",
        subject_label="STAT1",
        claim="Protein STAT1 increases in treatment versus control.",
        evidence_for="log2 fold change 1.8 with three unique peptides.",
        evidence_against="low sequence coverage warning remained attached.",
        confidence=ConfidenceTier.MODERATE,
        warning_codes=("low_sequence_coverage",),
        source_ids=("stat_result:protein_group_1", "row:12"),
    )
    path = tmp_path / "cards.tsv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(STANDARD_CARD_TSV_COLUMNS)
        writer.writerow(render_standard_card_row(entry))

    loaded = load_standard_card_tsv(path)

    assert loaded == (entry,)


def test_shared_card_loader_requires_governed_columns(tmp_path: Path) -> None:
    path = tmp_path / "cards.tsv"
    path.write_text(
        "\t".join(
            (
                "card_id",
                "card_kind",
                "subject_kind",
                "subject_id",
                "subject_label",
                "claim",
                "evidence_for",
                "confidence",
                "warning_codes",
                "source_ids",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing shared card columns"):
        load_standard_card_tsv(path)


def test_shared_card_loader_normalizes_legacy_confidence_aliases(tmp_path: Path) -> None:
    path = tmp_path / "cards.tsv"
    path.write_text(
        "\n".join(
            (
                "\t".join(STANDARD_CARD_TSV_COLUMNS),
                "\t".join(
                    (
                        "sample-card:S1",
                        "sample",
                        "sample",
                        "S1",
                        "sample S1",
                        "Sample S1 stayed within the expected study cluster.",
                        "pairwise correlation with peer replicates remained high.",
                        "no explicit weakening evidence was preserved.",
                        "medium",
                        "",
                        "S1",
                    )
                ),
            )
        )
        + "\n",
        encoding="utf-8",
    )

    loaded = load_standard_card_tsv(path)

    assert loaded[0].confidence is ConfidenceTier.MODERATE
