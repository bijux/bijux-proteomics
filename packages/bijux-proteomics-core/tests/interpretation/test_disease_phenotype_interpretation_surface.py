# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation.biological_context_mapping import (
    parse_biological_context_table,
)
from bijux_proteomics.interpretation.disease_phenotype_interpretation import (
    DiseasePhenotypeAnnotationScope,
    DiseasePhenotypeConfidenceStatus,
    DiseasePhenotypeInterpretationPolicy,
    build_disease_phenotype_interpretation_report,
    render_disease_phenotype_interpretation_summary_tsv,
    render_disease_phenotype_interpretation_tsv,
    render_unknown_disease_phenotype_annotation_tsv,
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


def test_build_disease_phenotype_interpretation_report_preserves_explicit_term_support() -> (
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
        _fixture("biological_report_disease_phenotype.tsv")
    )

    report = build_disease_phenotype_interpretation_report(
        protein_table,
        differential_report,
        context_report.accepted_records,
        policy=DiseasePhenotypeInterpretationPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=1.0,
            min_enrichment_ratio=1.0,
            high_confidence_min_supporting_protein_count=2,
        ),
    )

    assert report.summary.term_count == 4
    assert report.summary.disease_term_count == 2
    assert report.summary.phenotype_term_count == 2
    assert report.summary.foreground_protein_count == 3
    assert report.summary.background_protein_count == 5
    assert report.summary.evaluated_term_count == 4
    assert report.summary.filter_passing_term_count >= 1
    assert report.summary.high_confidence_term_count >= 1
    disease_entry = next(
        entry for entry in report.entries if entry.term_id == "DOID:162"
    )
    assert disease_entry.context_kind.value == "disease_term"
    assert disease_entry.source_name == "Disease Ontology"
    assert disease_entry.supporting_protein_refs == ("O14920", "P04637")
    assert (
        disease_entry.confidence_status
        is DiseasePhenotypeConfidenceStatus.HIGH_CONFIDENCE
    )
    phenotype_entry = next(
        entry for entry in report.entries if entry.term_id == "HP:0001250"
    )
    assert phenotype_entry.context_kind.value == "phenotype_term"
    assert phenotype_entry.supporting_protein_refs == ("O14920",)
    assert (
        phenotype_entry.confidence_status
        is DiseasePhenotypeConfidenceStatus.LOW_CONFIDENCE
    )
    assert any(
        entry.annotation_scope is DiseasePhenotypeAnnotationScope.BACKGROUND
        and entry.protein_ref == "P62993"
        for entry in report.unknown_annotation_entries
    )


def test_disease_phenotype_interpretation_renderers_expose_terms_and_unknown_annotations() -> (
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
        _fixture("biological_report_disease_phenotype.tsv")
    )
    report = build_disease_phenotype_interpretation_report(
        protein_table,
        differential_report,
        context_report.accepted_records,
        policy=DiseasePhenotypeInterpretationPolicy(max_adjusted_p_value=1.0),
    )

    summary_tsv = render_disease_phenotype_interpretation_summary_tsv(report)
    interpretation_tsv = render_disease_phenotype_interpretation_tsv(report)
    unknown_tsv = render_unknown_disease_phenotype_annotation_tsv(report)

    assert summary_tsv.splitlines()[0].startswith(
        "term_count\tdisease_term_count\tphenotype_term_count"
    )
    assert interpretation_tsv.splitlines()[0].startswith(
        "context_kind\tterm_id\tterm_name\tsource_name"
    )
    assert "passes_interpretation_filter" in interpretation_tsv.splitlines()[0]
    assert "DOID:162" in interpretation_tsv
    assert "HP:0001250" in interpretation_tsv
    assert unknown_tsv.splitlines()[0] == "annotation_scope\tprotein_ref\treason"
    assert "background\tP62993\t" in unknown_tsv
