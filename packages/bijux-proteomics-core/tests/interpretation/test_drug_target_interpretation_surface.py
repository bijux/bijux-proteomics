# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation.biological_context_mapping import (
    parse_biological_context_table,
)
from bijux_proteomics.interpretation.drug_target_interpretation import (
    DrugTargetEvidenceTier,
    DrugTargetInterpretationPolicy,
    DrugTargetRelationship,
    build_drug_target_interpretation_report,
    render_drug_target_interpretation_summary_tsv,
    render_drug_target_interpretation_tsv,
)
from bijux_proteomics.interpretation.pathway_enrichment import (
    parse_pathway_membership_table,
)
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinReferenceEntry,
    build_protein_annotation_mapping_report,
)
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification import (
    Ms1FeatureColumnMapping,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    apply_benjamini_hochberg,
    build_differential_abundance_report,
    build_label_free_intensity_table,
    normalize_label_free_table,
    parse_ms1_feature_table,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _build_fixture_table():
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
        ),
    )
    protein_table = build_label_free_intensity_table(
        parse_report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    return normalize_label_free_table(protein_table, method=NormalizationMethod.MEDIAN)


def _build_annotation_report(protein_table, differential_report):
    fasta_report = parse_fasta_document(
        _fixture("biological_report_reference.fasta").read_text(encoding="utf-8"),
        mode=FastaParseMode.STRICT,
    )
    reference_entries = tuple(
        ProteinReferenceEntry(
            row_number=index + 2,
            source_row_id=entry.entity_id,
            input_protein_ref=protein_ref,
            protein_ref=protein_ref,
        )
        for index, entry in enumerate(differential_report.entries)
        for protein_ref in protein_table.entity_protein_refs.get(
            entry.entity_id, (entry.entity_id,)
        )
    )
    return build_protein_annotation_mapping_report(
        reference_entries,
        fasta_report.accepted_records,
    )


def test_build_drug_target_interpretation_report_separates_direct_and_indirect_rows() -> (
    None
):
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    protein_table = _build_fixture_table()
    differential_report = apply_benjamini_hochberg(
        build_differential_abundance_report(
            protein_table,
            design_entries,
            condition_a="control",
            condition_b="treatment",
        )
    )
    context_report = parse_biological_context_table(
        _fixture("biological_report_drug_targets.tsv")
    )
    pathway_report = parse_pathway_membership_table(
        _fixture("biological_report_pathways.tsv")
    )
    annotation_report = _build_annotation_report(protein_table, differential_report)

    report = build_drug_target_interpretation_report(
        protein_table,
        differential_report,
        context_report.accepted_records,
        pathway_records=pathway_report.accepted_records,
        annotation_report=annotation_report,
        policy=DrugTargetInterpretationPolicy(max_adjusted_p_value=1.0),
    )

    assert report.summary.drug_count == 1
    assert report.summary.entry_count == 3
    assert report.summary.direct_target_entry_count == 1
    assert report.summary.indirect_pathway_neighbor_entry_count == 2
    direct_entry = next(
        entry
        for entry in report.entries
        if entry.relationship is DrugTargetRelationship.DIRECT_TARGET
    )
    assert direct_entry.drug_id == "DB0001"
    assert direct_entry.protein_ref == "P04637"
    assert direct_entry.evidence_tier is DrugTargetEvidenceTier.HIGH_EVIDENCE
    indirect_entry = next(
        entry
        for entry in report.entries
        if entry.protein_ref == "Q9Y243"
        and entry.relationship is DrugTargetRelationship.INDIRECT_PATHWAY_NEIGHBOR
    )
    assert indirect_entry.supporting_direct_target_refs == ("P04637",)
    assert indirect_entry.supporting_pathway_ids == ("custom:response",)
    assert indirect_entry.evidence_tier is DrugTargetEvidenceTier.MODERATE_EVIDENCE
    assert all(
        not (
            entry.protein_ref == "Q9Y243"
            and entry.relationship is DrugTargetRelationship.DIRECT_TARGET
        )
        for entry in report.entries
    )


def test_drug_target_interpretation_renderers_expose_direct_and_indirect_support() -> (
    None
):
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    protein_table = _build_fixture_table()
    differential_report = apply_benjamini_hochberg(
        build_differential_abundance_report(
            protein_table,
            design_entries,
            condition_a="control",
            condition_b="treatment",
        )
    )
    context_report = parse_biological_context_table(
        _fixture("biological_report_drug_targets.tsv")
    )
    pathway_report = parse_pathway_membership_table(
        _fixture("biological_report_pathways.tsv")
    )
    annotation_report = _build_annotation_report(protein_table, differential_report)
    report = build_drug_target_interpretation_report(
        protein_table,
        differential_report,
        context_report.accepted_records,
        pathway_records=pathway_report.accepted_records,
        annotation_report=annotation_report,
        policy=DrugTargetInterpretationPolicy(max_adjusted_p_value=1.0),
    )

    summary_tsv = render_drug_target_interpretation_summary_tsv(report)
    interpretation_tsv = render_drug_target_interpretation_tsv(report)

    assert summary_tsv.splitlines()[0].startswith(
        "condition_a\tcondition_b\tdrug_count\tentry_count"
    )
    assert interpretation_tsv.splitlines()[0].startswith(
        "drug_id\tdrug_name\tsource_name\tsource_accession\tprotein_ref"
    )
    assert "direct_target" in interpretation_tsv
    assert "indirect_pathway_neighbor" in interpretation_tsv
    assert "custom:response" in interpretation_tsv
