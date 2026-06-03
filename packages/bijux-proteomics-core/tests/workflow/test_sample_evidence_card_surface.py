# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.domain import StandardCardKind, load_standard_card_tsv
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.workflow import (
    build_biological_result_report_bundle,
    render_sample_evidence_card_tsv,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_sample_evidence_cards_project_sample_exploration_into_shared_card_schema(
    tmp_path: Path,
) -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    report = build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        condition_a="control",
        condition_b="treatment",
    )
    path = tmp_path / "biological_sample_cards.tsv"
    path.write_text(
        render_sample_evidence_card_tsv(report.sample_exploration_report),
        encoding="utf-8",
    )

    loaded = load_standard_card_tsv(path)

    assert loaded
    assert all(entry.card_kind is StandardCardKind.SAMPLE for entry in loaded)
    assert all(entry.claim for entry in loaded)
    assert all(entry.evidence_for for entry in loaded)
