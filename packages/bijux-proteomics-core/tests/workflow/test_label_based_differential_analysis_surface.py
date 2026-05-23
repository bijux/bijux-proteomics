# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.study import build_experiment_design
from bijux_proteomics.workflow.label_based_differential_analysis import (
    LabelBasedDifferentialSourceKind,
    build_label_based_differential_analysis_report,
    build_tmt_differential_analysis_report,
    build_tmt_differential_input_report,
)


def _multiplex_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_build_tmt_differential_input_report_preserves_bridge_normalized_protein_matrix() -> (
    None
):
    design_report = parse_experimental_design_table(_multiplex_fixture("tmt.design.tsv"))

    report = build_tmt_differential_input_report(
        _multiplex_fixture("maxquant_tmt_evidence.tsv"),
        tuple(design_report.accepted_entries),
    )

    assert report.source_kind is LabelBasedDifferentialSourceKind.TMT
    assert report.measurement_kind.value == "intensity"
    assert report.summary.entity_count == 2
    assert report.summary.sample_count == 4
    assert report.sample_ids == (
        "plex_a_126",
        "plex_a_127N",
        "plex_b_126",
        "plex_b_127N",
    )
    row = next(row for row in report.rows if row.entity_id == "P001")
    values = {value.sample_id: value.abundance for value in row.values}
    assert round(values["plex_a_126"] or 0.0, 6) == round(1200.0 / 6000.0, 6)
    assert round(values["plex_b_127N"] or 0.0, 6) == round(1700.0 / 6500.0, 6)
    assert "bridge-normalized TMT protein matrix" in report.note


def test_build_tmt_differential_analysis_report_preserves_design_and_bh_results() -> None:
    design_report = parse_experimental_design_table(_multiplex_fixture("tmt.design.tsv"))

    report = build_tmt_differential_analysis_report(
        _multiplex_fixture("maxquant_tmt_evidence.tsv"),
        tuple(design_report.accepted_entries),
    )

    assert report.normalization_method.value == "median"
    assert report.design_matrix.sample_count == 4
    assert report.design_matrix.column_count >= 3
    assert report.design_model_fit.fitted_entity_count == 2
    assert report.differential_abundance_report is not None
    assert report.differential_abundance_multi_condition_report is None
    differential = report.differential_abundance_report
    assert differential.condition_a == "control"
    assert differential.condition_b == "treatment"
    assert differential.entries[0].entity_id == "P001"
    assert differential.entries[0].adjusted_p_value is not None
    assert all(entry.adjusted_p_value is not None for entry in differential.entries)
    assert {entry.entity_id for entry in differential.entries} == {"P001", "P002"}
    assert report.volcano_plot is not None
    assert report.volcano_plot.condition_a == "control"
    assert report.volcano_plot.condition_b == "treatment"
    assert "benjamini-hochberg-corrected differential results" in report.note


def test_build_label_based_differential_analysis_report_blocks_missing_plex_channels() -> (
    None
):
    design_report = parse_experimental_design_table(_multiplex_fixture("tmt.design.tsv"))
    valid_entries = tuple(design_report.accepted_entries)
    input_report = build_tmt_differential_input_report(
        _multiplex_fixture("maxquant_tmt_evidence.tsv"),
        valid_entries,
    )
    invalid_design = build_experiment_design(
        tuple(entry for entry in valid_entries if entry.sample_id != "plex_b_127N")
    )

    try:
        build_label_based_differential_analysis_report(
            input_report,
            invalid_design,
        )
    except ValueError as exc:
        assert "missing_multiplex_channels" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected missing plex channels to be rejected")


def test_build_label_based_differential_analysis_report_blocks_longitudinal_designs() -> (
    None
):
    design_report = parse_experimental_design_table(_multiplex_fixture("tmt.design.tsv"))
    valid_entries = tuple(design_report.accepted_entries)
    input_report = build_tmt_differential_input_report(
        _multiplex_fixture("maxquant_tmt_evidence.tsv"),
        valid_entries,
    )
    longitudinal_design = build_experiment_design(
        tuple(
            entry.model_copy(
                update={
                    "metadata": {
                        **entry.metadata,
                        "timepoint": (
                            "T0" if entry.multiplex_group == "plex-a" else "T1"
                        ),
                    }
                }
            )
            for entry in valid_entries
        )
    )

    try:
        build_label_based_differential_analysis_report(
            input_report,
            longitudinal_design,
        )
    except ValueError as exc:
        assert "longitudinal" in str(exc)
        assert "time_course_differential" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected longitudinal labeled design to be rejected")
