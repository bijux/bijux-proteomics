# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation.biological_context_mapping import (
    parse_biological_context_table,
)
from bijux_proteomics.interpretation.compartment_biology import (
    CompartmentBiologyPolicy,
    CompartmentLocalizationScope,
    build_compartment_biology_report,
    render_compartment_activity_matrix_tsv,
    render_compartment_enrichment_tsv,
    render_unknown_compartment_localization_tsv,
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


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _build_fixture_table():
    parse_report = parse_ms1_feature_table(
        _workflow_fixture("biological_report_features.tsv"),
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
    return normalize_label_free_table(
        protein_table,
        method=NormalizationMethod.MEDIAN,
    )


def test_build_compartment_biology_report_preserves_unknown_localization_and_activity() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _workflow_fixture("biological_report.design.tsv")
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
        _workflow_fixture("biological_report_compartments.tsv")
    )

    report = build_compartment_biology_report(
        protein_table,
        differential_report,
        context_report.accepted_records,
        design_entries=design_entries,
        policy=CompartmentBiologyPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=1.0,
            min_enrichment_ratio=1.0,
            minimum_observed_member_count=2,
        ),
    )

    assert report.summary.compartment_count == 2
    assert report.summary.foreground_protein_count >= 3
    assert report.summary.background_protein_count == 5
    assert report.summary.unknown_foreground_protein_count == 1
    assert report.summary.unknown_background_protein_count == 2
    assert any(
        entry.localization_scope is CompartmentLocalizationScope.FOREGROUND
        and entry.protein_ref == "Q9Y243"
        for entry in report.unknown_localization_entries
    )
    assert any(
        entry.localization_scope is CompartmentLocalizationScope.BACKGROUND
        and entry.protein_ref == "Q8N158"
        for entry in report.unknown_localization_entries
    )
    nucleus_enrichment = next(
        entry
        for entry in report.enrichment_report.entries
        if entry.set_id == "GO:0005634"
    )
    assert nucleus_enrichment.set_name == "nucleus"
    assert set(nucleus_enrichment.supporting_protein_refs) == {"O14920", "P04637"}
    assert nucleus_enrichment.adjusted_p_value is not None
    nucleus_scores = {
        entry.sample_id: entry
        for entry in report.activity_report.sample_scores
        if entry.set_id == "GO:0005634"
    }
    assert nucleus_scores["T1"].activity_score is not None
    assert nucleus_scores["C1"].activity_score is not None
    assert nucleus_scores["T1"].activity_score > nucleus_scores["C1"].activity_score
    assert nucleus_scores["T1"].confidence_status.value == "high"
    cytosol_scores = {
        entry.sample_id: entry
        for entry in report.activity_report.sample_scores
        if entry.set_id == "GO:0005829"
    }
    assert cytosol_scores["C1"].confidence_status.value == "low"
    assert cytosol_scores["C1"].confidence_reason == (
        "observed member count 1 was below minimum 2"
    )


def test_compartment_biology_renderers_expose_compartment_and_unknown_outputs() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _workflow_fixture("biological_report.design.tsv")
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
        _workflow_fixture("biological_report_compartments.tsv")
    )
    report = build_compartment_biology_report(
        protein_table,
        differential_report,
        context_report.accepted_records,
        design_entries=design_entries,
        policy=CompartmentBiologyPolicy(max_adjusted_p_value=1.0),
    )

    enrichment_tsv = render_compartment_enrichment_tsv(report)
    matrix_tsv = render_compartment_activity_matrix_tsv(report)
    unknown_tsv = render_unknown_compartment_localization_tsv(report)

    assert enrichment_tsv.splitlines()[0].startswith(
        "compartment_id\tcompartment_name\tsource_name"
    )
    assert "passes_enrichment_filter" in enrichment_tsv.splitlines()[0]
    assert "GO:0005634" in enrichment_tsv
    assert matrix_tsv.splitlines()[0].startswith(
        "compartment_id\tcompartment_name\tsource_name\tsource_accession\tC1\tC2\tC3\tT1\tT2\tT3"
    )
    assert "localization_scope\tprotein_ref\treason" == unknown_tsv.splitlines()[0]
    assert "foreground\tQ9Y243\t" in unknown_tsv
