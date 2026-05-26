# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.study import build_experiment_design
from bijux_proteomics.workflow import (
    MechanismCardKind,
    build_biological_result_report_bundle,
    build_mechanism_cards,
    build_proteomics_study_result,
    render_mechanism_card_summary_tsv,
    render_mechanism_cards_tsv,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _mechanism_ready_report():
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    return build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        build_experiment_design(design_entries),
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        pathway_membership_tsv_path=_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_fixture("biological_report_complexes.tsv"),
        context_annotation_tsv_path=_fixture("biological_report_compartments.tsv"),
        regulator_evidence_tsv_path=_fixture("biological_report_regulator_evidence.tsv"),
        regulator_site_signal_tsv_path=_fixture("biological_report_regulator_sites.tsv"),
        condition_a="control",
        condition_b="treatment",
    )


def test_build_mechanism_cards_emits_all_required_card_classes_with_complete_evidence_fields() -> (
    None
):
    report = build_mechanism_cards(_mechanism_ready_report())

    assert {card.mechanism_kind for card in report.cards} == {
        MechanismCardKind.PATHWAY_SHIFT,
        MechanismCardKind.KINASE_CANDIDATE,
        MechanismCardKind.COMPLEX_CHANGE,
        MechanismCardKind.COMPARTMENT_SIGNAL,
        MechanismCardKind.BIOMARKER_CANDIDATE,
    }
    assert all(card.evidence_for for card in report.cards)
    assert all(card.evidence_against for card in report.cards)
    assert all(card.missing_evidence for card in report.cards)
    assert all(card.confidence.value in {"high", "moderate", "low"} for card in report.cards)
    assert all(card.source_row_refs or card.derived_no_source_reason for card in report.cards)
    assert report.summary.pathway_shift_count == 1
    assert report.summary.kinase_candidate_count == 1
    assert report.summary.complex_change_count == 1
    assert report.summary.compartment_signal_count == 2
    assert report.summary.biomarker_candidate_count == 3
    assert "kinase_candidate_count" in render_mechanism_card_summary_tsv(report)
    card_tsv = render_mechanism_cards_tsv(report)
    assert "evidence_for" in card_tsv
    assert "evidence_against" in card_tsv
    assert "missing_evidence" in card_tsv
    assert "derived_no_source_reason" in card_tsv
    assert any(card.card_id.startswith("pathway-shift-card:") for card in report.cards)
    assert any(card.card_id.startswith("kinase-candidate-card:") for card in report.cards)
    assert any(card.card_id.startswith("complex-change-card:") for card in report.cards)
    assert any(card.card_id.startswith("compartment-signal-card:") for card in report.cards)
    assert any(card.card_id.startswith("biomarker-candidate-card:") for card in report.cards)
    assert "MAPK14" in card_tsv
    assert "custom:response" in card_tsv


def test_build_mechanism_cards_accepts_study_result_inputs() -> None:
    study_result = build_proteomics_study_result(_mechanism_ready_report())

    report = build_mechanism_cards(study_result)

    assert report.summary.card_count >= 8
    assert any(card.subject_id == "GO:0005634" for card in report.cards)
    assert any(card.subject_id == "custom:triad" for card in report.cards)
