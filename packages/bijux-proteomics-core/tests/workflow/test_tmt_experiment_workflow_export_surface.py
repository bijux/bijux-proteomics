# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.multiplex import TmtSearchResultSourceKind
from bijux_proteomics.workflow import (
    build_tmt_experiment_workflow_bundle,
    export_tmt_experiment_workflow_bundle,
    validate_workflow_artifact_manifest,
)


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _multiplex_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_tmt_experiment_workflow_export_writes_import_metadata_and_report_assets(
    tmp_path: Path,
) -> None:
    report = build_tmt_experiment_workflow_bundle(
        _multiplex_fixture("maxquant_tmt_interference.tsv"),
        _multiplex_fixture("tmt.design.tsv"),
        control_channel="126",
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )

    manifest = export_tmt_experiment_workflow_bundle(report, tmp_path / "tmt_workflow")
    output_dir = tmp_path / "tmt_workflow"

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
    assert (
        output_dir / "inputs" / manifest.artifacts.accepted_reporter_rows_tsv
    ).exists()
    assert (output_dir / "qc" / manifest.artifacts.interference_summary_tsv).exists()
    assert (
        output_dir / "reports" / manifest.artifacts.label_based_report_manifest_json
    ).exists()
    layout_manifest = validate_workflow_artifact_manifest(output_dir)
    summary_entry = next(
        entry
        for entry in layout_manifest.artifacts
        if entry.legacy_relative_path == manifest.artifacts.summary_tsv
    )
    assert summary_entry.producer_function == "write_tmt_experiment_workflow_bundle"
    assert summary_entry.artifact_schema_version == "2026-05-26"
    assert summary_entry.output_table_schema is not None
    assert summary_entry.output_table_schema.schema_version == "2026-05-26"
    assert tuple(
        column.name for column in summary_entry.output_table_schema.columns
    ) == ("field", "value")
    assert summary_entry.output_table_schema_sidecar_relative_path == (
        f"reports/{manifest.artifacts.summary_tsv}.schema.json"
    )
    assert (
        output_dir / "reports" / f"{manifest.artifacts.summary_tsv}.schema.json"
    ).exists()
    assert (output_dir / manifest.artifacts.summary_tsv).exists()
    assert (output_dir / manifest.artifacts.reporter_import_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.accepted_reporter_rows_tsv).exists()
    assert (output_dir / manifest.artifacts.rejected_reporter_rows_tsv).exists()
    assert (output_dir / manifest.artifacts.rejected_evidence_tsv).exists()
    assert (output_dir / manifest.artifacts.metadata_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.channel_assignments_tsv).exists()
    assert (output_dir / manifest.artifacts.duplicate_assignments_tsv).exists()
    assert (output_dir / manifest.artifacts.missing_conditions_tsv).exists()
    assert (output_dir / manifest.artifacts.interference_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.interference_observations_tsv).exists()
    assert (output_dir / manifest.artifacts.filtered_interference_tsv).exists()
    assert (output_dir / manifest.artifacts.interference_channel_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.label_based_report_manifest_json).exists()
    assert "accepted_input_row_count" in (
        output_dir / manifest.artifacts.summary_tsv
    ).read_text(encoding="utf-8")
    assert "reporter_channel_count" in (
        output_dir / manifest.artifacts.reporter_import_summary_tsv
    ).read_text(encoding="utf-8")
    assert "channel_intensities" in (
        output_dir / manifest.artifacts.accepted_reporter_rows_tsv
    ).read_text(encoding="utf-8")
    assert (output_dir / manifest.artifacts.rejected_reporter_rows_tsv).read_text(
        encoding="utf-8"
    ).splitlines()[0] == "row_number\tissue_codes\tissue_messages\traw_fields"
    assert (output_dir / manifest.artifacts.rejected_evidence_tsv).read_text(
        encoding="utf-8"
    ).splitlines()[0] == (
        "rejected_evidence_id\tsource_surface\tsource_file\trow_number\t"
        "entity_type\tentity_id\treason_code\tdetail\trelated_artifact"
    )
    assert "assigned_channel_count" in (
        output_dir / manifest.artifacts.metadata_summary_tsv
    ).read_text(encoding="utf-8")
    assert "threshold_exceeded_count" in (
        output_dir / manifest.artifacts.interference_summary_tsv
    ).read_text(encoding="utf-8")
    assert "isolation_interference_fraction" in (
        output_dir / manifest.artifacts.interference_observations_tsv
    ).read_text(encoding="utf-8")
    assert "threshold and should be considered unreliable" in (
        output_dir / manifest.artifacts.filtered_interference_tsv
    ).read_text(encoding="utf-8")
    assert "mean_interference_fraction" in (
        output_dir / manifest.artifacts.interference_channel_summary_tsv
    ).read_text(encoding="utf-8")
    assert (
        output_dir / manifest.label_based_report_manifest.artifacts.summary_tsv
    ).exists()
    assert (
        output_dir
        / manifest.label_based_report_manifest.artifacts.tmt_channel_totals_tsv
    ).exists()
    assert (
        output_dir
        / manifest.label_based_report_manifest.artifacts.differential_results_tsv
    ).exists()
