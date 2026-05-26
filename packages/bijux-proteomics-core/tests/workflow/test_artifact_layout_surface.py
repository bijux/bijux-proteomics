# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

import pytest

import bijux_proteomics._atomic_files as atomic_files
from bijux_proteomics.domain.errors import InvalidWorkflowError, ScientificEvidenceError
from bijux_proteomics._output_tables import OutputTableSchema
from bijux_proteomics.workflow import AdvancedDiannWorkflowConfig, run_advanced_diann_workflow
from bijux_proteomics.workflow.artifact_layout import (
    find_workflow_artifact_by_id,
    find_workflow_artifact_by_legacy_path,
    index_workflow_artifact_manifest,
    WorkflowArtifactFolder,
    WorkflowArtifactKind,
    load_workflow_artifact_manifest,
    synchronize_workflow_artifact_layout,
    validate_workflow_artifact_manifest,
)


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


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
    assert entries["tmt_validation_summary.tsv"].artifact_id == (
        "artifact:qc:tsv_table:qc:tmt_validation_summary.tsv"
    )
    assert entries["tmt_validation_summary.tsv"].artifact_kind is WorkflowArtifactKind.TSV_TABLE
    assert entries["tmt_validation_summary.tsv"].artifact_schema == "tsv[placeholder]"
    assert entries["tmt_validation_summary.tsv"].artifact_schema_version == "2026-05-26"
    assert entries["tmt_validation_summary.tsv"].output_table_schema is not None
    assert entries["tmt_validation_summary.tsv"].output_table_schema.schema_version == "2026-05-26"
    assert entries["tmt_validation_summary.tsv"].output_table_schema.table_name == "tmt_validation_summary"
    assert entries["tmt_validation_summary.tsv"].output_table_schema.columns[0].name == "placeholder"
    assert entries["tmt_validation_summary.tsv"].output_table_schema_sidecar_relative_path == (
        "qc/tmt_validation_summary.tsv.schema.json"
    )
    assert (tmp_path / "qc" / "tmt_validation_summary.tsv.schema.json").exists()
    assert entries["tmt_validation_summary.tsv"].row_count == 0
    assert entries["tmt_validation_summary.tsv"].producer_function == "test_workflow_surface"
    assert entries["ptm_evidence_cards.tsv"].folder is WorkflowArtifactFolder.CARDS
    payload = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert payload["layout_name"] == "workflow_artifact_layout"
    assert payload["producer_function"] == "test_workflow_surface"
    assert payload["artifacts"][0]["checksum_sha256"]
    assert len({entry.artifact_id for entry in manifest.artifacts}) == len(
        manifest.artifacts
    )


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
    assert manifest.artifacts[0].artifact_schema_version == "2026-05-26"
    assert manifest.artifacts[0].output_table_schema is not None
    assert manifest.artifacts[0].output_table_schema.schema_version == "2026-05-26"
    assert tuple(
        column.name for column in manifest.artifacts[0].output_table_schema.columns
    ) == ("metric", "value")
    assert (
        tmp_path / "reports" / "biological_report_summary.tsv.schema.json"
    ).exists()


def test_index_workflow_artifact_manifest_resolves_entries_by_id_and_legacy_path(
    tmp_path: Path,
) -> None:
    (tmp_path / "biological_report_summary.tsv").write_text(
        "metric\tvalue\nprotein_count\t4\n",
        encoding="utf-8",
    )
    manifest = synchronize_workflow_artifact_layout(
        tmp_path,
        producer_function="test_workflow_surface",
    )

    artifact_index = index_workflow_artifact_manifest(manifest=manifest)
    artifact = manifest.artifacts[0]

    assert find_workflow_artifact_by_id(artifact_index, artifact.artifact_id) == artifact
    assert (
        find_workflow_artifact_by_legacy_path(
            artifact_index,
            artifact.legacy_relative_path,
        )
        == artifact
    )


def test_synchronize_workflow_artifact_layout_interruption_leaves_no_partial_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "biological_report_summary.tsv").write_text(
        "metric\tvalue\nprotein_count\t4\n",
        encoding="utf-8",
    )
    real_replace = atomic_files.os.replace

    def interrupted_replace(source: Path, destination: Path) -> None:
        if Path(destination).name == "manifest.json":
            raise RuntimeError("interrupted while replacing manifest.json")
        real_replace(source, destination)

    monkeypatch.setattr(atomic_files.os, "replace", interrupted_replace)

    with pytest.raises(RuntimeError, match="interrupted while replacing manifest.json"):
        synchronize_workflow_artifact_layout(
            tmp_path,
            producer_function="test_workflow_surface",
        )

    assert not (tmp_path / "manifest.json").exists()
    assert not tuple(tmp_path.glob(".*.bijux-write-*.tmp"))


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


def test_validate_workflow_artifact_manifest_rejects_missing_tsv_schema_sidecar(
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
    (tmp_path / "reports" / "biological_report_summary.tsv.schema.json").unlink()

    with pytest.raises(ScientificEvidenceError, match="missing table-schema sidecar"):
        validate_workflow_artifact_manifest(tmp_path)


def test_validate_workflow_artifact_manifest_rejects_tsv_schema_sidecar_version_drift(
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
    sidecar_path = tmp_path / "reports" / "biological_report_summary.tsv.schema.json"
    sidecar = OutputTableSchema.model_validate_json(sidecar_path.read_text(encoding="utf-8"))
    drifted_sidecar = sidecar.model_copy(update={"schema_version": "2026-05-99"})
    sidecar_path.write_text(drifted_sidecar.to_stable_json() + "\n", encoding="utf-8")

    with pytest.raises(InvalidWorkflowError, match="sidecar mismatch"):
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


def test_validate_workflow_artifact_manifest_rejects_duplicate_artifact_ids(
    tmp_path: Path,
) -> None:
    (tmp_path / "biological_report_summary.tsv").write_text(
        "metric\tvalue\nprotein_count\t4\n",
        encoding="utf-8",
    )
    (tmp_path / "advanced_targeted_workflow_manifest.json").write_text(
        json.dumps({"status": "ok"}) + "\n",
        encoding="utf-8",
    )
    synchronize_workflow_artifact_layout(
        tmp_path,
        producer_function="test_workflow_surface",
    )
    manifest = load_workflow_artifact_manifest(tmp_path)
    duplicated = manifest.artifacts[0].artifact_id
    drifted_manifest = manifest.model_copy(
        update={
            "artifacts": (
                manifest.artifacts[0],
                manifest.artifacts[1].model_copy(update={"artifact_id": duplicated}),
            )
        }
    )
    (tmp_path / "manifest.json").write_text(
        drifted_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )

    with pytest.raises(InvalidWorkflowError, match="duplicate artifact_id"):
        validate_workflow_artifact_manifest(tmp_path)


def test_validate_workflow_artifact_manifest_rejects_missing_advanced_diann_belief_audit_declared_by_workflow_manifest(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "advanced_diann_incomplete_belief_audit"
    report = run_advanced_diann_workflow(
        AdvancedDiannWorkflowConfig(
            result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
            output_dir=output_dir,
            condition_a="control",
            condition_b="treatment",
        )
    )

    missing_name = report.manifest.artifacts.belief_audit_tsv
    (output_dir / missing_name).unlink()
    (output_dir / "qc" / missing_name).unlink()

    manifest = load_workflow_artifact_manifest(output_dir)
    drifted_manifest = manifest.model_copy(
        update={
            "artifacts": tuple(
                artifact
                for artifact in manifest.artifacts
                if artifact.legacy_relative_path != missing_name
            )
        }
    )
    (output_dir / "manifest.json").write_text(
        drifted_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ScientificEvidenceError,
        match="missing advanced_diann_belief_audit.tsv declared at manifest.artifacts.belief_audit_tsv",
    ):
        validate_workflow_artifact_manifest(output_dir)


def test_validate_workflow_artifact_manifest_rejects_missing_advanced_diann_rejected_evidence_declared_by_workflow_manifest(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "advanced_diann_incomplete_rejected_evidence"
    report = run_advanced_diann_workflow(
        AdvancedDiannWorkflowConfig(
            result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
            output_dir=output_dir,
            condition_a="control",
            condition_b="treatment",
        )
    )

    missing_name = report.manifest.artifacts.rejected_evidence_tsv
    (output_dir / missing_name).unlink()
    (output_dir / "evidence" / missing_name).unlink()

    manifest = load_workflow_artifact_manifest(output_dir)
    drifted_manifest = manifest.model_copy(
        update={
            "artifacts": tuple(
                artifact
                for artifact in manifest.artifacts
                if artifact.legacy_relative_path != missing_name
            )
        }
    )
    (output_dir / "manifest.json").write_text(
        drifted_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ScientificEvidenceError,
        match="missing rejected_evidence.tsv declared at manifest.artifacts.rejected_evidence_tsv",
    ):
        validate_workflow_artifact_manifest(output_dir)
