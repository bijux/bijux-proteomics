# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
from typing import NoReturn

from click.testing import CliRunner
import pytest

from bijux_proteomics.interfaces.cli.app import cli
import bijux_proteomics.interfaces.support.output_protocol.workflow_execution as workflow_execution
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
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, object] = {}
    protocol_path = tmp_path / "protocol.tsv"
    protocol_path.write_text(
        "\n".join(
            (
                "protocol_id\tdigestion_enzyme\tacquisition_type\tlabeling_method\tenrichment_type\tfractionation_mode\tdepletion_mode\tinstrument_platform",
                "prot-001\ttrypsin\tdia\tlabel_free\tnone\tnone\tnone\tOrbitrap Astral",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    def _fake_run(config: object) -> NoReturn:
        captured["config"] = config
        raise RuntimeError("orchestrator sentinel")

    monkeypatch.setattr(workflow_execution, "run_proteomics_workflow", _fake_run)

    result = CliRunner().invoke(
        cli,
        [
            "biological-report",
            str(_workflow_fixture("biological_report_features.tsv")),
            str(_workflow_fixture("biological_report.design.tsv")),
            str(_workflow_fixture("biological_report_reference.fasta")),
            "--protocol-context-tsv",
            str(protocol_path),
            "--output-dir",
            str(tmp_path / "biological"),
        ],
    )

    assert result.exit_code == 1
    assert "orchestrator sentinel" in result.output
    config = captured["config"]
    assert isinstance(config, LabelFreeWorkflowConfig)
    assert config.protocol_context_tsv_path == protocol_path


def test_dda_biological_report_command_routes_through_core_workflow_orchestrator(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, object] = {}

    def _fake_run(config: object) -> NoReturn:
        captured["config"] = config
        raise RuntimeError("orchestrator sentinel")

    monkeypatch.setattr(workflow_execution, "run_proteomics_workflow", _fake_run)

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
    config = captured["config"]
    assert isinstance(config, DdaWorkflowConfig)
    assert config.mode is WorkflowMode.GENERIC_PSM


def test_diann_biological_report_command_routes_through_core_workflow_orchestrator(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, object] = {}

    def _fake_run(config: object) -> NoReturn:
        captured["config"] = config
        raise RuntimeError("orchestrator sentinel")

    monkeypatch.setattr(workflow_execution, "run_proteomics_workflow", _fake_run)

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
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, object] = {}
    maxquant_dir = _workflow_fixture("maxquant_biological")

    def _fake_run(config: object) -> NoReturn:
        captured["config"] = config
        raise RuntimeError("orchestrator sentinel")

    monkeypatch.setattr(workflow_execution, "run_proteomics_workflow", _fake_run)

    result = CliRunner().invoke(
        cli,
        [
            "maxquant-biological-report",
            str(maxquant_dir / "evidence.txt"),
            str(maxquant_dir / "peptides.txt"),
            str(maxquant_dir / "proteinGroups.txt"),
            str(maxquant_dir / "design.tsv"),
            str(_workflow_fixture("biological_report_reference.fasta")),
            "--annotation-tsv",
            str(_fixture_root() / "interpretation" / "protein_annotation_custom.tsv"),
            "--context-annotation-tsv",
            str(_workflow_fixture("biological_report_context.tsv")),
            "--output-dir",
            str(tmp_path / "maxquant"),
        ],
    )

    assert result.exit_code == 1
    assert "orchestrator sentinel" in result.output
    config = captured["config"]
    assert isinstance(config, MaxquantWorkflowConfig)
    assert (
        config.annotation_tsv_path
        == _fixture_root() / "interpretation" / "protein_annotation_custom.tsv"
    )
    assert config.context_annotation_tsv_path == _workflow_fixture(
        "biological_report_context.tsv"
    )


def test_tmt_report_command_routes_through_core_workflow_orchestrator(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, object] = {}

    def _fake_run(config: object) -> NoReturn:
        captured["config"] = config
        raise RuntimeError("orchestrator sentinel")

    monkeypatch.setattr(workflow_execution, "run_proteomics_workflow", _fake_run)

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
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, object] = {}

    def _fake_run(config: object) -> NoReturn:
        captured["config"] = config
        raise RuntimeError("orchestrator sentinel")

    monkeypatch.setattr(workflow_execution, "run_proteomics_workflow", _fake_run)

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
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, object] = {}

    def _fake_run(config: object) -> NoReturn:
        captured["config"] = config
        raise RuntimeError("orchestrator sentinel")

    monkeypatch.setattr(workflow_execution, "run_proteomics_workflow", _fake_run)

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
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def _fake_run(config: object) -> NoReturn:
        captured["config"] = config
        raise RuntimeError("orchestrator sentinel")

    monkeypatch.setattr(workflow_execution, "run_proteomics_workflow", _fake_run)

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
    config = captured["config"]
    assert isinstance(config, TargetedWorkflowConfig)
    assert config.stage is TargetedWorkflowStage.MATRIX


def test_targeted_assay_qc_command_routes_through_core_workflow_orchestrator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def _fake_run(config: object) -> NoReturn:
        captured["config"] = config
        raise RuntimeError("orchestrator sentinel")

    monkeypatch.setattr(workflow_execution, "run_proteomics_workflow", _fake_run)

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
    config = captured["config"]
    assert isinstance(config, TargetedWorkflowConfig)
    assert config.stage is TargetedWorkflowStage.ASSAY_QC
