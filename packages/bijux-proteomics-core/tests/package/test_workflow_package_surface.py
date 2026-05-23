# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics import workflow
from bijux_proteomics.io.formats import parse_experimental_design_table


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_workflow_package_exports_protein_evidence_card_surface() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    report = workflow.build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        condition_a="control",
        condition_b="treatment",
    )

    assert hasattr(workflow, "build_protein_evidence_card_report")
    assert "card_id" in workflow.render_protein_evidence_card_tsv(report.protein_cards)
    assert report.protein_cards.summary.protein_result_count == report.summary.protein_count
