# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.multiplex import TmtSearchResultSourceKind
from bijux_proteomics.workflow import (
    LabelFreeWorkflowConfig,
    TmtWorkflowConfig,
    WorkflowMode,
    run_proteomics_workflow,
)


def _fixture_root() -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures"


def _workflow_fixture(name: str) -> Path:
    return _fixture_root() / "workflow" / name


def _multiplex_fixture(name: str) -> Path:
    return _fixture_root() / "multiplex" / name


def test_run_proteomics_workflow_exports_label_free_bundle_assets(
    tmp_path: Path,
) -> None:
    result = run_proteomics_workflow(
        LabelFreeWorkflowConfig(
            input_tsv_path=_workflow_fixture("biological_report_features.tsv"),
            design_tsv_path=_workflow_fixture("biological_report.design.tsv"),
            proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
            condition_a="control",
            condition_b="treatment",
            output_dir=tmp_path / "biological_report",
        )
    )

    assert result.mode is WorkflowMode.LABEL_FREE
    assert result.export_manifest is not None
    assert (tmp_path / "biological_report" / "biological_report_manifest.json").exists()
    assert (tmp_path / "biological_report" / "final_proteins.tsv").exists()
    assert result.outputs["manifest_json"].endswith("biological_report_manifest.json")


def test_run_proteomics_workflow_exports_tmt_bundle_assets(tmp_path: Path) -> None:
    result = run_proteomics_workflow(
        TmtWorkflowConfig(
            result_tsv_path=_multiplex_fixture("maxquant_tmt_evidence.tsv"),
            design_tsv_path=_multiplex_fixture("tmt.design.tsv"),
            control_channel="126",
            source_kind=TmtSearchResultSourceKind.MAXQUANT,
            condition_a="control",
            condition_b="treatment",
            output_dir=tmp_path / "tmt_report",
        )
    )

    assert result.mode is WorkflowMode.TMT
    assert result.export_manifest is not None
    assert (tmp_path / "tmt_report" / "tmt_workflow_manifest.json").exists()
    assert (tmp_path / "tmt_report" / "label_based_report_manifest.json").exists()
    assert result.outputs["workflow_manifest_json"].endswith("tmt_workflow_manifest.json")
