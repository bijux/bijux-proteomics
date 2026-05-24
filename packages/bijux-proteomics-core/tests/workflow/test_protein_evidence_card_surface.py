# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification import (
    Ms1FeatureColumnMapping,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    parse_ms1_feature_table,
)
from bijux_proteomics.workflow import (
    ProteinEvidenceCardSelectionPolicy,
    build_biological_result_report_bundle,
    build_biological_result_graph_report,
    build_protein_evidence_card_report,
)
from bijux_proteomics.sequences import parse_protein_region_context_tsv


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_build_protein_evidence_card_report_preserves_one_structured_card_per_final_protein() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    bundle = build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        context_annotation_tsv_path=_fixture("biological_report_context.tsv"),
        pathway_membership_tsv_path=_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_fixture("biological_report_complexes.tsv"),
        condition_a="control",
        condition_b="treatment",
    )
    parse_report = parse_ms1_feature_table(
        _fixture("biological_report_features.tsv"),
        mapping=Ms1FeatureColumnMapping(
            sample_id="sample_id",
            feature_id="feature_id",
            peptide="peptide",
            intensity="intensity",
            protein_refs="proteins",
            charge="charge",
            mz="mz",
            retention_time_seconds="retention_time_seconds",
            missing_reason="missing_reason",
            protein_separator=";",
        ),
    )
    quant_table = build_label_free_intensity_table(
        parse_report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
        top_n=3,
    )

    report = build_protein_evidence_card_report(
        build_biological_result_graph_report(
            quant_table,
            bundle.differential_report,
            design_entries,
            max_adjusted_p_value=0.1,
            min_absolute_log2_fold_change=1.0,
        ),
        quant_table,
        bundle.differential_report,
        bundle.annotation_report,
        protein_sequences={
            "P04637": "MPEPAAAK",
            "Q9Y243": "MPEPDDDK",
            "O14920": "MPEPCCCK",
        },
        selection_policy=ProteinEvidenceCardSelectionPolicy(),
        sample_conditions={entry.sample_id: entry.condition for entry in design_entries},
        context_mapping_report=bundle.context_mapping_report,
        pathway_enrichment_report=bundle.pathway_enrichment_report,
        complex_enrichment_report=bundle.complex_enrichment_report,
        protein_region_context_records=parse_protein_region_context_tsv(
            _fixture("biological_report_regions.tsv")
        ).accepted_records,
    )

    assert report.summary.protein_result_count == len(bundle.differential_report.entries)
    assert len(report.cards) == bundle.summary.protein_count
    assert all(card.card_id.startswith("protein-card-") for card in report.cards)
    assert all(card.graph_claim_node_id.startswith("statistical_result:") for card in report.cards)
    assert all(card.graph_subject_node_id.startswith("protein:") for card in report.cards)
    assert all(card.peptide_count == len(card.peptides) for card in report.cards)
    assert any(card.pathways for card in report.cards)
    assert any(card.context_terms for card in report.cards)
    assert any(card.identity_level.value == "protein_level" for card in report.cards)
    assert any(card.functional_regions for card in report.cards)
    assert any(
        region.supporting_evidence_refs == ("PEPAAA",)
        for card in report.cards
        for region in card.functional_regions
        if card.representative_protein_ref == "P04637"
    )
    assert any(card.warnings for card in report.cards)
