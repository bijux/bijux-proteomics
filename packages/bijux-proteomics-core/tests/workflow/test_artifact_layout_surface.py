# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_proteomics.domain.errors import InvalidWorkflowError, ScientificEvidenceError
from bijux_proteomics.workflow.artifact_layout import (
    WorkflowArtifactFolder,
    WorkflowArtifactKind,
    load_workflow_artifact_manifest,
    synchronize_workflow_artifact_layout,
    validate_workflow_artifact_manifest,
)


def test_synchronize_workflow_artifact_layout_places_representative_outputs_in_fixed_folders(
    tmp_path: Path,
) -> None:
    for name in (
        "biological_report_summary.tsv",
        "tmt_validation_summary.tsv",
        "ptm_evidence_cards.tsv",
        "label_based_differential_results.tsv",
        "pathway_activity_matrix.tsv",
    ):
        (tmp_path / name).write_text("placeholder\n", encoding="utf-8")
    (tmp_path / "advanced_targeted_workflow_manifest.json").write_text(
        json.dumps({"workflow": "advanced_targeted"}) + "\n",
        encoding="utf-8",
    )

    manifest = synchronize_workflow_artifact_layout(
        tmp_path,
        producer_function="test_workflow_surface",
    )

    assert (tmp_path / "inputs").is_dir()
    assert (tmp_path / "qc").is_dir()
    assert (tmp_path / "evidence").is_dir()
    assert (tmp_path / "matrices").is_dir()
    assert (tmp_path / "stats").is_dir()
    assert (tmp_path / "biology").is_dir()
    assert (tmp_path / "cards").is_dir()
    assert (tmp_path / "reports").is_dir()
    assert (tmp_path / "manifest.json").exists()
    assert (tmp_path / "reports" / "biological_report_summary.tsv").exists()
    assert (tmp_path / "qc" / "tmt_validation_summary.tsv").exists()
    assert (tmp_path / "cards" / "ptm_evidence_cards.tsv").exists()
    assert (tmp_path / "stats" / "label_based_differential_results.tsv").exists()
    assert (tmp_path / "matrices" / "pathway_activity_matrix.tsv").exists()
    assert (tmp_path / "reports" / "advanced_targeted_workflow_manifest.json").exists()

    assert manifest.artifacts
    entries = {
        entry.legacy_relative_path: entry
        for entry in manifest.artifacts
    }
    assert entries["tmt_validation_summary.tsv"].folder is WorkflowArtifactFolder.QC
    assert entries["tmt_validation_summary.tsv"].artifact_kind is WorkflowArtifactKind.TSV_TABLE
    assert entries["tmt_validation_summary.tsv"].artifact_schema == "tsv[placeholder]"
    assert entries["tmt_validation_summary.tsv"].output_table_schema is not None
    assert entries["tmt_validation_summary.tsv"].output_table_schema.table_name == "tmt_validation_summary"
    assert entries["tmt_validation_summary.tsv"].output_table_schema.columns[0].name == "placeholder"
    assert entries["tmt_validation_summary.tsv"].row_count == 0
    assert entries["tmt_validation_summary.tsv"].producer_function == "test_workflow_surface"
    assert entries["ptm_evidence_cards.tsv"].folder is WorkflowArtifactFolder.CARDS
    payload = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert payload["layout_name"] == "workflow_artifact_layout"
    assert payload["producer_function"] == "test_workflow_surface"
    assert payload["artifacts"][0]["checksum_sha256"]


def test_validate_workflow_artifact_manifest_accepts_fresh_layout_manifest(
    tmp_path: Path,
) -> None:
    (tmp_path / "biological_report_summary.tsv").write_text(
        "metric\tvalue\nprotein_count\t4\n",
        encoding="utf-8",
    )

    synchronize_workflow_artifact_layout(
        tmp_path,
        producer_function="test_workflow_surface",
    )

    manifest = validate_workflow_artifact_manifest(tmp_path)

    assert load_workflow_artifact_manifest(tmp_path).producer_function == "test_workflow_surface"
    assert manifest.artifacts[0].row_count == 1
    assert manifest.artifacts[0].artifact_schema == "tsv[metric,value]"
    assert manifest.artifacts[0].output_table_schema is not None
    assert tuple(
        column.name for column in manifest.artifacts[0].output_table_schema.columns
    ) == ("metric", "value")


def test_validate_workflow_artifact_manifest_rejects_checksum_drift(
    tmp_path: Path,
) -> None:
    (tmp_path / "biological_report_summary.tsv").write_text(
        "metric\tvalue\nprotein_count\t4\n",
        encoding="utf-8",
    )
    synchronize_workflow_artifact_layout(
        tmp_path,
        producer_function="test_workflow_surface",
    )
    (tmp_path / "reports" / "biological_report_summary.tsv").write_text(
        "metric\tvalue\nprotein_count\t9\n",
        encoding="utf-8",
    )

    with pytest.raises(InvalidWorkflowError, match="checksum mismatch"):
        validate_workflow_artifact_manifest(tmp_path)


def test_validate_workflow_artifact_manifest_rejects_tsv_header_drift(
    tmp_path: Path,
) -> None:
    (tmp_path / "biological_report_summary.tsv").write_text(
        "metric\tvalue\nprotein_count\t4\n",
        encoding="utf-8",
    )
    synchronize_workflow_artifact_layout(
        tmp_path,
        producer_function="test_workflow_surface",
    )
    (tmp_path / "reports" / "biological_report_summary.tsv").write_text(
        "metric\nprotein_count\n",
        encoding="utf-8",
    )

    with pytest.raises(InvalidWorkflowError, match="table-schema mismatch"):
        validate_workflow_artifact_manifest(tmp_path)


def test_validate_workflow_artifact_manifest_rejects_tsv_type_drift(
    tmp_path: Path,
) -> None:
    (tmp_path / "biological_report_summary.tsv").write_text(
        "metric\tvalue\nprotein_count\t4\n",
        encoding="utf-8",
    )
    synchronize_workflow_artifact_layout(
        tmp_path,
        producer_function="test_workflow_surface",
    )
    (tmp_path / "reports" / "biological_report_summary.tsv").write_text(
        "metric\tvalue\nprotein_count\tnot_a_number\n",
        encoding="utf-8",
    )

    with pytest.raises(InvalidWorkflowError, match="invalid integer value"):
        validate_workflow_artifact_manifest(tmp_path)


def test_validate_workflow_artifact_manifest_rejects_missing_artifact(
    tmp_path: Path,
) -> None:
    (tmp_path / "advanced_targeted_workflow_manifest.json").write_text(
        json.dumps({"status": "ok"}) + "\n",
        encoding="utf-8",
    )
    synchronize_workflow_artifact_layout(
        tmp_path,
        producer_function="test_workflow_surface",
    )
    (tmp_path / "reports" / "advanced_targeted_workflow_manifest.json").unlink()

    with pytest.raises(ScientificEvidenceError, match="missing file"):
        validate_workflow_artifact_manifest(tmp_path)
