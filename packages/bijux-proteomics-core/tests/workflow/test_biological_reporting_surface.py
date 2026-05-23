# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    MissingValueKind,
    NormalizationMethod,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
    QuantValue,
)
from bijux_proteomics.workflow import build_biological_result_report_bundle
from bijux_proteomics.workflow.biological_reporting import (
    build_biological_result_report_bundle_from_quant_table,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_build_biological_result_report_bundle_preserves_differential_and_review_surfaces() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    report = build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        context_annotation_tsv_path=_fixture("biological_report_context.tsv"),
        condition_a="control",
        condition_b="treatment",
    )

    assert report.summary.protein_count == 5
    assert report.summary.significant_protein_count >= 3
    assert report.summary.sample_count == 6
    assert report.summary.annotation_entry_count == 5
    assert report.summary.protein_card_count == 5
    assert report.summary.warning_card_count >= 1
    assert report.graph_report.protein_claim_count == report.summary.protein_count
    assert report.summary.context_entry_count == 3
    assert report.summary.context_unmapped_count == 2
    assert report.summary.context_term_count == 3
    assert report.summary.heatmap_entity_count >= 3
    assert report.volcano_review.source_kind.value == "quantification"
    assert report.volcano_review.significant_point_count >= 3
    assert report.sample_exploration_report.summary.sample_count == 6
    assert report.heatmap_report.summary.output_entity_count >= 3
    assert report.protein_cards.summary.protein_result_count == 5
    assert any(card.card_id.startswith("protein-card-") for card in report.protein_cards.cards)
    assert all(card.graph_claim_node_id.startswith("statistical_result:") for card in report.protein_cards.cards)
    assert all(card.graph_subject_node_id.startswith("protein:") for card in report.protein_cards.cards)
    assert report.context_import_report is not None
    assert report.context_mapping_report is not None
    assert any(
        entry.context_id == "DB0001"
        for entry in report.context_mapping_report.mapped_entries
    )
    assert any(
        entry.protein_ref == "Q9Y243"
        for entry in report.context_mapping_report.unmapped_entries
    )


def test_build_biological_result_report_bundle_from_quant_table_uses_entity_protein_refs_for_annotation() -> (
    None
):
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    values: list[QuantValue] = []
    abundances = {
        "PG001": {"C1": 200.0, "C2": 220.0, "C3": 210.0, "T1": 1600.0, "T2": 1550.0, "T3": 1650.0},
        "PG002": {"C1": 1800.0, "C2": 1750.0, "C3": 1850.0, "T1": 200.0, "T2": 220.0, "T3": 210.0},
        "PG003": {"C1": 150.0, "C2": 160.0, "C3": 140.0, "T1": 1400.0, "T2": 1450.0, "T3": 1500.0},
    }
    for entity_id, entity_values in abundances.items():
        for sample_id, abundance in entity_values.items():
            values.append(
                QuantValue(
                    sample_id=sample_id,
                    entity_id=entity_id,
                    abundance=abundance,
                    missing_value_kind=MissingValueKind.OBSERVED,
                    source_feature_count=1,
                )
            )
    table = LabelFreeQuantTable(
        entity_level=QuantEntityLevel.PROTEIN,
        measure_kind=QuantMeasureKind.INTENSITY,
        aggregation_method=QuantRollupMethod.SUM,
        normalization_method=NormalizationMethod.NONE,
        sample_ids=("C1", "C2", "C3", "T1", "T2", "T3"),
        entity_ids=("PG001", "PG002", "PG003"),
        values=tuple(values),
        entity_protein_refs={
            "PG001": ("P04637",),
            "PG002": ("Q9Y243",),
            "PG003": ("O14920",),
        },
        entity_member_peptides={
            "PG001": ("PEPAAA",),
            "PG002": ("PEPBBB",),
            "PG003": ("PEPCCC",),
        },
    )

    report = build_biological_result_report_bundle_from_quant_table(
        table,
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        condition_a="control",
        condition_b="treatment",
    )

    mapped_refs = {entry.protein_ref for entry in report.annotation_report.mapped_entries}
    assert mapped_refs == {"P04637", "Q9Y243", "O14920"}
    assert report.summary.annotation_entry_count == 3


def test_biological_result_report_bundle_keeps_unmapped_proteins_in_annotation_results() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    values: list[QuantValue] = []
    abundances = {
        "PG001": {"C1": 200.0, "C2": 220.0, "C3": 210.0, "T1": 1600.0, "T2": 1550.0, "T3": 1650.0},
        "PG999": {"C1": 300.0, "C2": 320.0, "C3": 310.0, "T1": 350.0, "T2": 360.0, "T3": 340.0},
    }
    for entity_id, entity_values in abundances.items():
        for sample_id, abundance in entity_values.items():
            values.append(
                QuantValue(
                    sample_id=sample_id,
                    entity_id=entity_id,
                    abundance=abundance,
                    missing_value_kind=MissingValueKind.OBSERVED,
                    source_feature_count=1,
                )
            )
    table = LabelFreeQuantTable(
        entity_level=QuantEntityLevel.PROTEIN,
        measure_kind=QuantMeasureKind.INTENSITY,
        aggregation_method=QuantRollupMethod.SUM,
        normalization_method=NormalizationMethod.NONE,
        sample_ids=("C1", "C2", "C3", "T1", "T2", "T3"),
        entity_ids=("PG001", "PG999"),
        values=tuple(values),
        entity_protein_refs={
            "PG001": ("P04637",),
            "PG999": ("UNKNOWN123",),
        },
        entity_member_peptides={
            "PG001": ("PEPAAA",),
            "PG999": ("PEPMISS",),
        },
    )

    report = build_biological_result_report_bundle_from_quant_table(
        table,
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        condition_a="control",
        condition_b="treatment",
    )

    assert report.summary.annotation_entry_count == 2
    assert report.summary.annotation_unmapped_count == 1
    assert any(
        entry.annotation_status.value == "unmapped"
        and entry.protein_ref == "UNKNOWN123"
        for entry in report.annotation_report.result_entries
    )
