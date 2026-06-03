# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import (
    build_protein_set_scoring_report,
    parse_protein_set_table,
    render_protein_set_condition_comparison_tsv,
    render_protein_set_condition_score_tsv,
    render_protein_set_sample_score_tsv,
    render_protein_set_score_matrix_tsv,
    render_protein_set_scoring_summary_tsv,
    render_protein_set_unresolved_member_tsv,
    render_rejected_protein_set_tsv,
)
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification import (
    Ms1FeatureColumnMapping,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    normalize_label_free_table,
    parse_ms1_feature_table,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def _quant_fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "quant" / name


def _build_fixture_table():
    parse_report = parse_ms1_feature_table(
        _quant_fixture_path("ms1_features.tsv"),
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
        aggregation_method=QuantRollupMethod.TOP_N,
        top_n=2,
    )
    return normalize_label_free_table(
        protein_table,
        method=NormalizationMethod.MEDIAN,
    )


def test_protein_set_renderers_emit_summary_matrix_condition_and_unresolved_ledgers() -> (
    None
):
    design_report = parse_experimental_design_table(
        _quant_fixture_path("quant.design.tsv")
    )
    protein_sets = parse_protein_set_table(_fixture_path("protein_sets.tsv"))
    invalid_sets = parse_protein_set_table(_fixture_path("protein_sets_invalid.tsv"))
    report = build_protein_set_scoring_report(
        _build_fixture_table(),
        protein_sets.accepted_records,
        design_entries=design_report.accepted_entries,
    )

    summary_tsv = render_protein_set_scoring_summary_tsv(report)
    matrix_tsv = render_protein_set_score_matrix_tsv(report)
    sample_tsv = render_protein_set_sample_score_tsv(report)
    condition_tsv = render_protein_set_condition_score_tsv(report)
    comparison_tsv = render_protein_set_condition_comparison_tsv(report)
    unresolved_tsv = render_protein_set_unresolved_member_tsv(report)
    rejected_tsv = render_rejected_protein_set_tsv(invalid_sets)

    assert summary_tsv.splitlines()[0].startswith("entity_level\tmeasure_kind")
    assert (
        "set_id\tset_name\tset_category\tsource_name\tsource_accession\tC1\tC2\tT1\tT2"
        in matrix_tsv
    )
    assert "activation\tActivation program\t\tcurated\t" in matrix_tsv
    assert "sample_id\tcondition\tbatch\tactivity_score" in sample_tsv
    assert "confidence_status" in sample_tsv.splitlines()[0]
    assert "\tlow\t" in sample_tsv
    assert "confidence_status" in condition_tsv.splitlines()[0]
    assert "condition_a_confidence_status" in comparison_tsv.splitlines()[0]
    assert "P999" in unresolved_tsv
    assert (
        "duplicate protein set membership for activation and protein P001"
        in rejected_tsv
    )
