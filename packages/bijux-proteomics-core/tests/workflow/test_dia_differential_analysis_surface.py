# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.dia import build_diann_protein_matrix_report
from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    parse_experimental_design_table,
)
from bijux_proteomics.study import build_experiment_design
from bijux_proteomics.workflow.dia_differential_analysis import (
    DiaDifferentialSourceKind,
    build_dia_protein_matrix_differential_analysis_report,
    build_diann_differential_analysis_report,
    build_diann_differential_input_report,
    build_spectronaut_differential_analysis_report,
)


def _diann_fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "diann"
        / name
    )


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def _spectronaut_fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "spectronaut"
        / name
    )


def _entry(
    *,
    sample_id: str,
    condition: str,
    spectra_file: str,
    replicate: int = 1,
) -> ExperimentalDesignEntry:
    return ExperimentalDesignEntry(
        sample_id=sample_id,
        condition=condition,
        replicate=replicate,
        fraction=1,
        spectra_file=spectra_file,
    )


def test_build_diann_differential_input_report_preserves_sample_matrix() -> None:
    report = build_diann_differential_input_report(
        _diann_fixture("diann_differential_report.tsv")
    )

    assert report.source_kind is DiaDifferentialSourceKind.DIANN
    assert report.source_name == "DIA-NN"
    assert report.matrix_summary.entity_count == 3
    assert report.matrix_summary.sample_count == 4
    assert report.matrix_summary.observed_cell_count == 12
    assert report.matrix_summary.missing_cell_count == 0
    assert report.table.sample_ids == ("C1", "C2", "T1", "T2")
    assert report.table.entity_ids == ("PG001", "PG002", "PG003")
    assert report.table.entity_protein_refs["PG001"] == ("P11111",)
    assert report.table.entity_member_peptides["PG002"] == ("ACDM[Oxidation]K",)
    values = {
        (value.entity_id, value.sample_id): value for value in report.table.values
    }
    assert values[("PG001", "T2")].abundance == 420000.0
    assert values[("PG001", "T2")].source_feature_count == 1
    assert values[("PG003", "C1")].abundance == 200000.0
    assert "DIA-NN rollup evidence" in report.note


def test_build_diann_differential_analysis_report_preserves_normalization_and_fdr() -> (
    None
):
    design_report = parse_experimental_design_table(
        _format_fixture("diann_differential.design.tsv")
    )
    experiment_design = build_experiment_design(design_report.accepted_entries)

    report = build_diann_differential_analysis_report(
        _diann_fixture("diann_differential_report.tsv"),
        experiment_design,
    )

    assert report.normalized_table.normalization_method.value == "median"
    assert report.design_matrix.sample_count == 4
    assert report.design_matrix.column_count >= 3
    assert report.design_model_fit.fitted_entity_count == 3
    assert report.qc_summary.source_kind is DiaDifferentialSourceKind.DIANN
    assert report.qc_summary.normalization_method.value == "median"
    assert report.qc_summary.entity_count == 3
    assert report.qc_summary.sample_count == 4
    assert report.qc_summary.contrast_count == 1
    assert report.qc_summary.differential_entry_count == 3
    assert report.qc_summary.significant_entry_count == 2
    assert report.differential_abundance_report is not None
    assert report.differential_abundance_multi_condition_report is None
    differential = report.differential_abundance_report
    assert differential.condition_a == "control"
    assert differential.condition_b == "treatment"
    assert differential.entries[0].entity_id == "PG001"
    assert differential.entries[0].log2_fold_change > 1.8
    assert differential.entries[0].adjusted_p_value is not None
    assert differential.entries[0].adjusted_p_value < 0.1
    pg2 = next(entry for entry in differential.entries if entry.entity_id == "PG002")
    pg3 = next(entry for entry in differential.entries if entry.entity_id == "PG003")
    assert pg2.log2_fold_change < -1.4
    assert pg2.adjusted_p_value is not None
    assert pg3.adjusted_p_value == 1.0
    assert "qc summary counts" in report.note


def test_build_dia_protein_matrix_differential_analysis_report_runs_from_core_api() -> (
    None
):
    design_report = parse_experimental_design_table(
        _format_fixture("diann_differential.design.tsv")
    )
    protein_matrix = build_diann_protein_matrix_report(
        _diann_fixture("diann_differential_report.tsv")
    )
    experiment_design = build_experiment_design(design_report.accepted_entries)

    report = build_dia_protein_matrix_differential_analysis_report(
        protein_matrix,
        experiment_design,
        source_kind=DiaDifferentialSourceKind.DIANN,
    )

    assert report.input_report.source_kind is DiaDifferentialSourceKind.DIANN
    assert report.input_report.table.entity_ids == ("PG001", "PG002", "PG003")
    assert report.qc_summary.entity_count == 3
    assert report.qc_summary.sample_count == 4
    assert report.qc_summary.fitted_entity_count == 3
    assert report.qc_summary.significant_entry_count == 2


def test_build_spectronaut_differential_analysis_report_preserves_the_same_result_shape() -> (
    None
):
    design_report = parse_experimental_design_table(
        _format_fixture("spectronaut_differential.design.tsv")
    )
    experiment_design = build_experiment_design(design_report.accepted_entries)

    report = build_spectronaut_differential_analysis_report(
        _spectronaut_fixture("spectronaut_differential_report.tsv"),
        experiment_design,
        config_path=_spectronaut_fixture("spectronaut_settings.txt"),
    )

    assert report.input_report.source_kind is DiaDifferentialSourceKind.SPECTRONAUT
    assert report.input_report.source_name == "Spectronaut"
    assert report.input_report.matrix_summary.entity_count == 3
    assert report.input_report.table.entity_member_peptides["PG002"] == (
        "ACDM[Oxidation]K",
    )
    assert report.normalized_table.sample_ids == ("C1", "C2", "T1", "T2")
    assert report.design_model_fit.fitted_entity_count == 3
    assert report.qc_summary.source_kind is DiaDifferentialSourceKind.SPECTRONAUT
    assert report.qc_summary.contrast_count == 1
    assert report.qc_summary.differential_entry_count == 3
    assert report.qc_summary.significant_entry_count == 2
    assert report.differential_abundance_report is not None
    differential = report.differential_abundance_report
    assert differential.entries[0].entity_id == "PG001"
    assert differential.entries[0].log2_fold_change > 1.8
    pg2 = next(entry for entry in differential.entries if entry.entity_id == "PG002")
    pg3 = next(entry for entry in differential.entries if entry.entity_id == "PG003")
    assert pg2.log2_fold_change < -1.4
    assert pg3.adjusted_p_value == 1.0


def test_build_diann_differential_analysis_report_blocks_invalid_contrasts() -> None:
    design_report = parse_experimental_design_table(
        _format_fixture("diann_differential.design.tsv")
    )
    experiment_design = build_experiment_design(design_report.accepted_entries)

    try:
        build_diann_differential_analysis_report(
            _diann_fixture("diann_differential_report.tsv"),
            experiment_design,
            condition_a="control",
            condition_b="missing",
        )
    except ValueError as exc:
        assert "invalid_contrast_unknown_condition" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected invalid contrast to be rejected")


def test_build_diann_differential_analysis_report_blocks_paired_design_methods() -> (
    None
):
    design_report = parse_experimental_design_table(
        _format_fixture("diann_differential.design.tsv")
    )
    paired_design = build_experiment_design(
        tuple(
            entry.model_copy(update={"pair_id": f"pair-{entry.replicate}"})
            for entry in design_report.accepted_entries
        )
    )

    try:
        build_diann_differential_analysis_report(
            _diann_fixture("diann_differential_report.tsv"),
            paired_design,
        )
    except ValueError as exc:
        assert "paired" in str(exc)
        assert "paired_differential" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected paired DIA design to be rejected")


def test_build_diann_differential_analysis_report_blocks_underpowered_designs() -> None:
    underpowered_design = build_experiment_design(
        (
            _entry(sample_id="C1", condition="control", spectra_file="c1.raw"),
            _entry(sample_id="T1", condition="treatment", spectra_file="t1.raw"),
            _entry(
                sample_id="T2",
                condition="treatment",
                spectra_file="t2.raw",
                replicate=2,
            ),
        )
    )

    try:
        build_diann_differential_analysis_report(
            _diann_fixture("diann_differential_report.tsv"),
            underpowered_design,
            condition_a="control",
            condition_b="treatment",
        )
    except ValueError as exc:
        assert "not feasible" in str(exc)
        assert "insufficient_group_size" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected underpowered DIA design to be rejected")
