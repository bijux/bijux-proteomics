# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.workflow import (
    build_silac_label_based_report_bundle,
    build_tmt_label_based_report_bundle,
    export_label_based_report_bundle,
    validate_workflow_artifact_manifest,
)


def _tmt_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def _silac_fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent / "fixtures" / "isotope_labeling" / name
    )


def test_tmt_label_based_report_export_writes_quality_ratio_and_differential_ledgers(
    tmp_path: Path,
) -> None:
    design_entries = tuple(
        parse_experimental_design_table(_tmt_fixture("tmt.design.tsv")).accepted_entries
    )
    report = build_tmt_label_based_report_bundle(
        _tmt_fixture("maxquant_tmt_evidence.tsv"),
        design_entries,
        control_channel="126",
    )

    manifest = export_label_based_report_bundle(report, tmp_path / "tmt_report")
    output_dir = tmp_path / "tmt_report"

    assert manifest.source_kind.value == "tmt"
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "inputs").is_dir()
    assert (output_dir / "qc").is_dir()
    assert (output_dir / "evidence").is_dir()
    assert (output_dir / "matrices").is_dir()
    assert (output_dir / "stats").is_dir()
    assert (output_dir / "biology").is_dir()
    assert (output_dir / "cards").is_dir()
    assert (output_dir / "reports").is_dir()
    assert (output_dir / "reports" / manifest.artifacts.summary_tsv).exists()
    assert (output_dir / "qc" / manifest.artifacts.tmt_validation_summary_tsv).exists()
    assert (
        output_dir / "matrices" / manifest.artifacts.tmt_channel_totals_tsv
    ).exists()
    assert (output_dir / "stats" / manifest.artifacts.differential_results_tsv).exists()
    layout_manifest = validate_workflow_artifact_manifest(output_dir)
    summary_entry = next(
        entry
        for entry in layout_manifest.artifacts
        if entry.legacy_relative_path == manifest.artifacts.summary_tsv
    )
    assert summary_entry.output_table_schema is not None
    assert summary_entry.artifact_schema_version == "2026-05-26"
    assert summary_entry.output_table_schema.schema_version == "2026-05-26"
    assert summary_entry.output_table_schema.columns[0].name == "source_kind"
    assert summary_entry.output_table_schema_sidecar_relative_path == (
        f"reports/{manifest.artifacts.summary_tsv}.schema.json"
    )
    assert (
        output_dir / "reports" / f"{manifest.artifacts.summary_tsv}.schema.json"
    ).exists()
    differential_entry = next(
        entry
        for entry in layout_manifest.artifacts
        if entry.legacy_relative_path == manifest.artifacts.differential_results_tsv
    )
    assert differential_entry.output_table_schema is not None
    assert differential_entry.artifact_schema_version == "2026-05-26"
    assert differential_entry.output_table_schema.schema_version == "2026-05-26"
    assert "adjusted_p_value" in {
        column.name for column in differential_entry.output_table_schema.columns
    }
    assert differential_entry.output_table_schema_sidecar_relative_path == (
        f"stats/{manifest.artifacts.differential_results_tsv}.schema.json"
    )
    assert (output_dir / manifest.artifacts.summary_tsv).exists()
    assert (output_dir / manifest.artifacts.sample_qc_tsv).exists()
    assert (output_dir / manifest.artifacts.tmt_channel_totals_tsv).exists()
    assert (output_dir / manifest.artifacts.tmt_normalization_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.tmt_protein_ratio_tsv).exists()
    assert (output_dir / manifest.artifacts.tmt_validation_channel_tsv).exists()
    assert (output_dir / manifest.artifacts.differential_results_tsv).exists()
    assert "quality_entry_count" in (
        output_dir / manifest.artifacts.summary_tsv
    ).read_text(encoding="utf-8")
    assert "assay_axis" in (output_dir / manifest.artifacts.sample_qc_tsv).read_text(
        encoding="utf-8"
    )
    assert "total_intensity" in (
        output_dir / manifest.artifacts.tmt_channel_totals_tsv
    ).read_text(encoding="utf-8")
    assert "ratio" in (output_dir / manifest.artifacts.tmt_protein_ratio_tsv).read_text(
        encoding="utf-8"
    )
    assert "adjusted_p_value" in (
        output_dir / manifest.artifacts.differential_results_tsv
    ).read_text(encoding="utf-8")


def test_silac_label_based_report_export_writes_quality_ratio_and_differential_ledgers(
    tmp_path: Path,
) -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _silac_fixture("silac_differential.design.tsv")
        ).accepted_entries
    )
    report = build_silac_label_based_report_bundle(
        _silac_fixture("silac_differential_features.tsv"),
        design_entries,
    )

    manifest = export_label_based_report_bundle(report, tmp_path / "silac_report")
    output_dir = tmp_path / "silac_report"

    assert manifest.source_kind.value == "silac"
    assert (output_dir / "manifest.json").exists()
    layout_manifest = validate_workflow_artifact_manifest(output_dir)
    summary_entry = next(
        entry
        for entry in layout_manifest.artifacts
        if entry.legacy_relative_path == manifest.artifacts.summary_tsv
    )
    assert summary_entry.output_table_schema is not None
    assert summary_entry.artifact_schema_version == "2026-05-26"
    assert summary_entry.output_table_schema.schema_version == "2026-05-26"
    assert summary_entry.output_table_schema.columns[0].name == "source_kind"
    assert summary_entry.output_table_schema_sidecar_relative_path == (
        f"reports/{manifest.artifacts.summary_tsv}.schema.json"
    )
    assert (output_dir / manifest.artifacts.summary_tsv).exists()
    assert (output_dir / manifest.artifacts.sample_qc_tsv).exists()
    assert (output_dir / manifest.artifacts.silac_ratio_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.silac_protein_ratio_tsv).exists()
    assert (output_dir / manifest.artifacts.silac_validation_label_tsv).exists()
    assert (output_dir / manifest.artifacts.differential_results_tsv).exists()
    assert "protein_ratio_count" in (
        output_dir / manifest.artifacts.summary_tsv
    ).read_text(encoding="utf-8")
    assert "assay_axis" in (output_dir / manifest.artifacts.sample_qc_tsv).read_text(
        encoding="utf-8"
    )
    assert "reference_label" in (
        output_dir / manifest.artifacts.silac_protein_ratio_tsv
    ).read_text(encoding="utf-8")
    assert "missing_group_count" in (
        output_dir / manifest.artifacts.silac_validation_label_tsv
    ).read_text(encoding="utf-8")
