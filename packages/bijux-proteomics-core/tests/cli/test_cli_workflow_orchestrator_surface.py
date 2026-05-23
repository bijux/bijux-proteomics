# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import bijux_proteomics.interfaces.cli.app as cli_app
from click.testing import CliRunner

from bijux_proteomics.interfaces.cli.app import cli
from bijux_proteomics.workflow.orchestrator import (
    DdaWorkflowConfig,
    DiannWorkflowConfig,
    LabelFreeWorkflowConfig,
    MaxquantWorkflowConfig,
    PtmWorkflowConfig,
    SilacWorkflowConfig,
    TargetedWorkflowConfig,
    TargetedWorkflowStage,
    TmtWorkflowConfig,
    WorkflowMode,
)


def _fixture_root() -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures"


def _workflow_fixture(name: str) -> Path:
    return _fixture_root() / "workflow" / name


def _multiplex_fixture(name: str) -> Path:
    return _fixture_root() / "multiplex" / name


def _silac_fixture(name: str) -> Path:
    return _fixture_root() / "isotope_labeling" / name


def _ptm_fixture(name: str) -> Path:
    return _fixture_root() / "ptm" / name


def _targeted_fixture(name: str) -> Path:
    return _fixture_root() / "formats" / name


def test_biological_report_command_routes_through_core_workflow_orchestrator(
    monkeypatch, tmp_path: Path
) -> None:
    captured = {}

    def _fake_run(config):
        captured["config"] = config
        raise RuntimeError("orchestrator sentinel")

    monkeypatch.setattr(cli_app, "run_proteomics_workflow", _fake_run)

    result = CliRunner().invoke(
        cli,
        [
            "biological-report",
            str(_workflow_fixture("biological_report_features.tsv")),
            str(_workflow_fixture("biological_report.design.tsv")),
            str(_workflow_fixture("biological_report_reference.fasta")),
            "--output-dir",
            str(tmp_path / "biological"),
        ],
    )

    assert result.exit_code == 1
    assert "orchestrator sentinel" in result.output
    assert isinstance(captured["config"], LabelFreeWorkflowConfig)


def test_dda_biological_report_command_routes_through_core_workflow_orchestrator(
    monkeypatch, tmp_path: Path
) -> None:
    captured = {}

    def _fake_run(config):
        captured["config"] = config
        raise RuntimeError("orchestrator sentinel")

    monkeypatch.setattr(cli_app, "run_proteomics_workflow", _fake_run)

    result = CliRunner().invoke(
        cli,
        [
            "dda-biological-report",
            str(_workflow_fixture("dda_biological_results.tsv")),
            str(_workflow_fixture("biological_report.design.tsv")),
            str(_workflow_fixture("biological_report_reference.fasta")),
            "--mapping-path",
            str(_workflow_fixture("dda_biological_mapping.json")),
            "--output-dir",
            str(tmp_path / "dda"),
        ],
    )

    assert result.exit_code == 1
    assert "orchestrator sentinel" in result.output
    assert isinstance(captured["config"], DdaWorkflowConfig)
    assert captured["config"].mode is WorkflowMode.GENERIC_PSM


def test_diann_biological_report_command_routes_through_core_workflow_orchestrator(
    monkeypatch, tmp_path: Path
) -> None:
    captured = {}

    def _fake_run(config):
        captured["config"] = config
        raise RuntimeError("orchestrator sentinel")

    monkeypatch.setattr(cli_app, "run_proteomics_workflow", _fake_run)

    result = CliRunner().invoke(
        cli,
        [
            "diann-biological-report",
            str(_workflow_fixture("diann_biological_report.tsv")),
            str(_workflow_fixture("diann_biological.design.tsv")),
            str(_workflow_fixture("biological_report_reference.fasta")),
            "--output-dir",
            str(tmp_path / "diann"),
        ],
    )

    assert result.exit_code == 1
    assert "orchestrator sentinel" in result.output
    assert isinstance(captured["config"], DiannWorkflowConfig)


def test_maxquant_biological_report_command_routes_through_core_workflow_orchestrator(
    monkeypatch, tmp_path: Path
) -> None:
    captured = {}
    maxquant_dir = _workflow_fixture("maxquant_biological")

    def _fake_run(config):
        captured["config"] = config
        raise RuntimeError("orchestrator sentinel")

    monkeypatch.setattr(cli_app, "run_proteomics_workflow", _fake_run)

    result = CliRunner().invoke(
        cli,
        [
            "maxquant-biological-report",
            str(maxquant_dir / "evidence.txt"),
            str(maxquant_dir / "peptides.txt"),
            str(maxquant_dir / "proteinGroups.txt"),
            str(maxquant_dir / "design.tsv"),
            str(_workflow_fixture("biological_report_reference.fasta")),
            "--output-dir",
            str(tmp_path / "maxquant"),
        ],
    )

    assert result.exit_code == 1
    assert "orchestrator sentinel" in result.output
    assert isinstance(captured["config"], MaxquantWorkflowConfig)


def test_tmt_report_command_routes_through_core_workflow_orchestrator(
    monkeypatch, tmp_path: Path
) -> None:
    captured = {}

    def _fake_run(config):
        captured["config"] = config
        raise RuntimeError("orchestrator sentinel")

    monkeypatch.setattr(cli_app, "run_proteomics_workflow", _fake_run)

    result = CliRunner().invoke(
        cli,
        [
            "multiplex",
            "tmt-report",
            str(_multiplex_fixture("maxquant_tmt_evidence.tsv")),
            str(_multiplex_fixture("tmt.design.tsv")),
            "--control-channel",
            "126",
            "--output-dir",
            str(tmp_path / "tmt"),
        ],
    )

    assert result.exit_code == 1
    assert "orchestrator sentinel" in result.output
    assert isinstance(captured["config"], TmtWorkflowConfig)


def test_silac_report_command_routes_through_core_workflow_orchestrator(
    monkeypatch, tmp_path: Path
) -> None:
    captured = {}

    def _fake_run(config):
        captured["config"] = config
        raise RuntimeError("orchestrator sentinel")

    monkeypatch.setattr(cli_app, "run_proteomics_workflow", _fake_run)

    result = CliRunner().invoke(
        cli,
        [
            "isotope-labeling",
            "silac-report",
            str(_silac_fixture("silac_differential_features.tsv")),
            str(_silac_fixture("silac_differential.design.tsv")),
            "--output-dir",
            str(tmp_path / "silac"),
        ],
    )

    assert result.exit_code == 1
    assert "orchestrator sentinel" in result.output
    assert isinstance(captured["config"], SilacWorkflowConfig)


def test_ptm_report_command_routes_through_core_workflow_orchestrator(
    monkeypatch, tmp_path: Path
) -> None:
    captured = {}

    def _fake_run(config):
        captured["config"] = config
        raise RuntimeError("orchestrator sentinel")

    monkeypatch.setattr(cli_app, "run_proteomics_workflow", _fake_run)

    result = CliRunner().invoke(
        cli,
        [
            "ptm",
            "report",
            str(_ptm_fixture("localization_results.tsv")),
            str(_fixture_root() / "fasta" / "ptm_sites.fasta"),
            str(_ptm_fixture("ptm_features.tsv")),
            str(_ptm_fixture("ptm.design.tsv")),
            "--output-dir",
            str(tmp_path / "ptm"),
        ],
    )

    assert result.exit_code == 1
    assert "orchestrator sentinel" in result.output
    assert isinstance(captured["config"], PtmWorkflowConfig)


def test_targeted_target_matrix_command_routes_through_core_workflow_orchestrator(
    monkeypatch,
) -> None:
    captured = {}

    def _fake_run(config):
        captured["config"] = config
        raise RuntimeError("orchestrator sentinel")

    monkeypatch.setattr(cli_app, "run_proteomics_workflow", _fake_run)

    result = CliRunner().invoke(
        cli,
        [
            "targeted-target-matrix",
            str(_targeted_fixture("skyline_targeted_results.tsv")),
            "--source-kind",
            "skyline_export",
        ],
    )

    assert result.exit_code == 1
    assert "orchestrator sentinel" in result.output
    assert isinstance(captured["config"], TargetedWorkflowConfig)
    assert captured["config"].stage is TargetedWorkflowStage.MATRIX


def test_targeted_assay_qc_command_routes_through_core_workflow_orchestrator(
    monkeypatch,
) -> None:
    captured = {}

    def _fake_run(config):
        captured["config"] = config
        raise RuntimeError("orchestrator sentinel")

    monkeypatch.setattr(cli_app, "run_proteomics_workflow", _fake_run)

    result = CliRunner().invoke(
        cli,
        [
            "targeted-assay-qc",
            str(_targeted_fixture("skyline_targeted_qc_results.tsv")),
            str(_targeted_fixture("skyline_targeted_qc.design.tsv")),
            "--source-kind",
            "skyline_export",
        ],
    )

    assert result.exit_code == 1
    assert "orchestrator sentinel" in result.output
    assert isinstance(captured["config"], TargetedWorkflowConfig)
    assert captured["config"].stage is TargetedWorkflowStage.ASSAY_QC
