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
from bijux_proteomics.study import build_experiment_design
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
        build_experiment_design(design_entries),
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
    assert report.summary.experiment_confidence_score > 0.0
    assert report.summary.experiment_confidence_tier in {
        "high_confidence",
        "moderate_confidence",
        "low_confidence",
    }
    assert report.experiment_confidence_report.summary.component_count == 7
    assert report.experiment_confidence_report.summary.overall_tier.value == (
        report.summary.experiment_confidence_tier
    )
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
            "PG002": ("PEPDDD",),
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
    assert report.experiment_confidence_report.summary.component_count == 7


def test_biological_result_report_bundle_from_quant_table_preserves_functional_regions_on_cards(
    tmp_path: Path,
) -> None:
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
            "PG002": ("PEPDDD",),
            "PG003": ("PEPCCC",),
        },
    )
    fasta_path = tmp_path / "matching_regions.fasta"
    fasta_path.write_text(
        (
            ">sp|P04637|SIGA_HUMAN Signaling protein A\nMPEPAAAK\n"
            ">sp|Q9Y243|SIGB_HUMAN Signaling protein B\nMPEPDDDK\n"
            ">sp|O14920|SIGC_HUMAN Signaling protein C\nMPEPCCCK\n"
        ),
        encoding="utf-8",
    )

    report = build_biological_result_report_bundle_from_quant_table(
        table,
        design_entries,
        proteins_fasta_path=fasta_path,
        protein_region_context_tsv_path=_fixture("biological_report_regions.tsv"),
        condition_a="control",
        condition_b="treatment",
    )

    assert report.protein_cards.summary.functional_region_annotated_card_count >= 1
    assert any(card.functional_regions for card in report.protein_cards.cards)
    assert any(
        region.label == "cell_cycle_core"
        for card in report.protein_cards.cards
        for region in card.functional_regions
    )


def test_biological_result_report_bundle_from_quant_table_does_not_call_exact_isoform_without_unique_peptide(
    tmp_path: Path,
) -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    values: list[QuantValue] = []
    abundances = {
        "PGISO": {
            "C1": 200.0,
            "C2": 220.0,
            "C3": 210.0,
            "T1": 1600.0,
            "T2": 1550.0,
            "T3": 1650.0,
        },
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
        entity_ids=("PGISO",),
        values=tuple(values),
        entity_protein_refs={
            "PGISO": ("P11111-2", "P11111"),
        },
        entity_member_peptides={
            "PGISO": ("PEPTIDEK",),
        },
    )
    fasta_path = tmp_path / "shared_isoform.fasta"
    fasta_path.write_text(
        (
            ">sp|P11111|GENE1_HUMAN Canonical GN=GENE1\nMPEPTIDEK\n"
            ">sp|P11111-2|GENE1_HUMAN Isoform GN=GENE1\nMPEPTIDEK\n"
        ),
        encoding="utf-8",
    )

    report = build_biological_result_report_bundle_from_quant_table(
        table,
        design_entries,
        proteins_fasta_path=fasta_path,
        condition_a="control",
        condition_b="treatment",
    )

    card = report.protein_cards.cards[0]

    assert card.identity_level.value == "protein_level"
    assert "do not isolate one exact isoform" in card.identity_reason


def test_biological_result_report_bundle_from_quant_table_preserves_proteogenomic_variant_support(
    tmp_path: Path,
) -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    values: list[QuantValue] = []
    abundances = {
        "PGREF": {
            "C1": 200.0,
            "C2": 220.0,
            "C3": 210.0,
            "T1": 300.0,
            "T2": 320.0,
            "T3": 310.0,
        },
        "PGVAR": {
            "C1": 100.0,
            "C2": 95.0,
            "C3": 105.0,
            "T1": 800.0,
            "T2": 820.0,
            "T3": 810.0,
        },
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
        entity_ids=("PGREF", "PGVAR"),
        values=tuple(values),
        entity_protein_refs={
            "PGREF": ("P12345",),
            "PGVAR": ("Q9AAA1",),
        },
        entity_member_peptides={
            "PGREF": ("REFPEPTIDEK",),
            "PGVAR": ("ALTPEPTIDEK",),
        },
    )
    reference_fasta_path = tmp_path / "reference.fasta"
    reference_fasta_path.write_text(
        ">sp|P12345|REF1_HUMAN Reference 1 GN=REF1\nMREFPEPTIDEKAA\n",
        encoding="utf-8",
    )
    variant_fasta_path = tmp_path / "variant.fasta"
    variant_fasta_path.write_text(
        ">sp|Q9AAA1|VAR1_HUMAN Variant 1 GN=VAR1\nMALTPEPTIDEKAA\n",
        encoding="utf-8",
    )
    variant_peptide_tsv_path = tmp_path / "variant_peptides.tsv"
    variant_peptide_tsv_path.write_text(
        (
            "peptide_sequence\tvariant_protein_ref\treference_protein_ref\tvariant_label\n"
            "ALTPEPTIDEK\tQ9AAA1\tP12345\tp.G12V\n"
        ),
        encoding="utf-8",
    )

    report = build_biological_result_report_bundle_from_quant_table(
        table,
        design_entries,
        proteins_fasta_path=reference_fasta_path,
        variant_proteins_fasta_path=variant_fasta_path,
        variant_peptide_tsv_path=variant_peptide_tsv_path,
        condition_a="control",
        condition_b="treatment",
    )

    support_by_group = {
        card.protein_group_id: card.proteogenomic_support
        for card in report.protein_cards.cards
    }
    assert support_by_group["PGREF"] is not None
    assert support_by_group["PGREF"].support_class.value == "reference_only"
    assert support_by_group["PGVAR"] is not None
    assert support_by_group["PGVAR"].support_class.value == "variant_only"
    assert support_by_group["PGVAR"].variant_only_peptides == ("ALTPEPTIDEK",)
    assert report.protein_cards.summary.proteogenomic_annotated_card_count == 2


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
    assert report.summary.experiment_confidence_score > 0.0
    assert any(
        entry.annotation_status.value == "unmapped"
        and entry.protein_ref == "UNKNOWN123"
        for entry in report.annotation_report.result_entries
    )


def test_biological_result_report_bundle_adapts_selection_policy_to_protocol_context(
    tmp_path: Path,
) -> None:
    protocol_path = tmp_path / "protocol.tsv"
    protocol_path.write_text(
        "\n".join(
            (
                "protocol_id\tdigestion_enzyme\tacquisition_type\tlabeling_method\tenrichment_type\tfractionation_mode\tdepletion_mode\tinstrument_platform",
                "prot-001\ttrypsin\tdda\ttmt\tnone\tnone\tnone\tOrbitrap Exploris",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )

    report = build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        build_experiment_design(design_entries),
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        protocol_context_tsv_path=protocol_path,
        condition_a="control",
        condition_b="treatment",
    )

    assert report.selection_policy.min_absolute_log2_fold_change == 0.58
    assert report.selection_policy.heatmap_max_entity_count == 80
    assert any(
        "protocol_consistency_caution" in component.reason_codes
        for component in report.experiment_confidence_report.components
    )
