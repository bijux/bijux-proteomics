# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics.workflow.artifact_layout import (
    WorkflowArtifactFolder,
    synchronize_workflow_artifact_layout,
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
        "advanced_targeted_workflow_manifest.json",
    ):
        (tmp_path / name).write_text("placeholder\n", encoding="utf-8")

    manifest = synchronize_workflow_artifact_layout(tmp_path)

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
    assert entries["ptm_evidence_cards.tsv"].folder is WorkflowArtifactFolder.CARDS
    assert json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))[
        "layout_name"
    ] == "workflow_artifact_layout"
