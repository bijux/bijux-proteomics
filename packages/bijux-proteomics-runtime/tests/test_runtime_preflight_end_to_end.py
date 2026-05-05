from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics_runtime.runs import RunConfig
from bijux_proteomics_runtime.runs import RunManager
from bijux_proteomics_runtime.runs.context import create_run_context
from bijux_proteomics_runtime.runs.failure_reports import RuntimeFailureReport
from bijux_proteomics_runtime.runs.preflight import (
    PreflightCheck,
    PreflightCheckState,
    RuntimePreflightReport,
    build_runtime_preflight_report,
)

from .runtime_fixture_data import load_fixture


def _check_by_id(
    report: RuntimePreflightReport,
    check_id: str,
) -> PreflightCheck:
    return next(check for check in report.checks if check.check_id == check_id)


def test_runtime_preflight_reports_missing_tools_and_wrong_versions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = load_fixture("execution", "preflight_failure_cases.json")
    missing_tool_case = fixture["missing_tool_case"]
    wrong_version_case = fixture["wrong_version_case"]
    context, _ = create_run_context(tmp_path, run_id="preflight-versions-1")
    monkeypatch.setattr(
        "bijux_proteomics_runtime.runs.preflight.provider_requirements",
        lambda _name: list(missing_tool_case["detail_codes"]),
    )

    report = build_runtime_preflight_report(
        context.workspace,
        run_id=context.run_id,
        provider_name=str(missing_tool_case["provider_name"]),
        required_tool_versions={
            str(key): str(value)
            for key, value in wrong_version_case["required_tool_versions"].items()
        },
        available_tool_versions={
            str(key): str(value)
            for key, value in wrong_version_case["available_tool_versions"].items()
        },
    )

    provider_check = _check_by_id(report, "provider_requirements")
    version_check = _check_by_id(report, "tool_versions")

    assert report.passed is False
    assert provider_check.state is PreflightCheckState.FAIL
    assert "missing_dependency:transformers" in provider_check.detail_codes
    assert version_check.state is PreflightCheckState.FAIL
    assert version_check.detail_codes == ("spectronaut:expected=19.0:actual=18.5",)


def test_runtime_preflight_reports_missing_dataset_and_invalid_layout(
    tmp_path: Path,
) -> None:
    fixture = load_fixture("execution", "preflight_failure_cases.json")
    missing_dataset_case = fixture["missing_dataset_case"]
    invalid_layout_case = fixture["invalid_layout_case"]
    context, _ = create_run_context(tmp_path, run_id="preflight-dataset-1")

    missing_report = build_runtime_preflight_report(
        context.workspace,
        run_id=context.run_id,
        provider_name=str(missing_dataset_case["provider_name"]),
        source_path=tmp_path / str(missing_dataset_case["source_filename"]),
    )

    invalid_source_path = tmp_path / str(invalid_layout_case["source_filename"])
    invalid_source_path.write_text(
        str(invalid_layout_case["source_payload"]),
        encoding="utf-8",
    )
    invalid_report = build_runtime_preflight_report(
        context.workspace,
        run_id=context.run_id,
        provider_name=str(invalid_layout_case["provider_name"]),
        source_path=invalid_source_path,
    )

    missing_dataset_check = _check_by_id(missing_report, "source_dataset")
    invalid_layout_check = _check_by_id(invalid_report, "source_dataset_layout")

    assert missing_report.passed is False
    assert missing_dataset_check.state is PreflightCheckState.FAIL
    assert missing_dataset_check.detail_codes == ("source_dataset_missing",)
    assert invalid_report.passed is False
    assert invalid_layout_check.state is PreflightCheckState.FAIL
    assert invalid_layout_check.detail_codes == ("source_dataset_layout_invalid",)


def test_runtime_import_preflight_blocks_missing_dataset_and_invalid_layout(
    tmp_path: Path,
) -> None:
    fixture = load_fixture("execution", "preflight_failure_cases.json")
    missing_dataset_case = fixture["missing_dataset_case"]
    invalid_layout_case = fixture["invalid_layout_case"]
    manager = RunManager(tmp_path)

    missing_result = manager.import_result(
        sequence="MPEPTIDE",
        source_path=tmp_path / str(missing_dataset_case["source_filename"]),
        imported_payload={"peptides": ["PEPTIDE"]},
        engine_name=str(missing_dataset_case["provider_name"]),
        engine_version="19.0",
        run_id="preflight-import-missing-dataset-1",
    )
    missing_report = RuntimeFailureReport.load_json(
        tmp_path
        / "artifacts"
        / "preflight-import-missing-dataset-1"
        / "failure_report.json"
    )

    invalid_source_path = tmp_path / str(invalid_layout_case["source_filename"])
    invalid_source_path.write_text(
        str(invalid_layout_case["source_payload"]),
        encoding="utf-8",
    )
    invalid_result = manager.import_result(
        sequence="MPEPTIDE",
        source_path=invalid_source_path,
        imported_payload={"proteins": ["P12345"]},
        engine_name=str(invalid_layout_case["provider_name"]),
        engine_version="2.1.0",
        run_id="preflight-import-invalid-layout-1",
    )
    invalid_report = RuntimeFailureReport.load_json(
        tmp_path
        / "artifacts"
        / "preflight-import-invalid-layout-1"
        / "failure_report.json"
    )

    assert missing_result["status"] == "failure"
    assert missing_result["failure_type"] == "invalid_output"
    assert missing_report.detail_codes == ("source_dataset_missing",)
    assert invalid_result["status"] == "failure"
    assert invalid_result["failure_type"] == "invalid_output"
    assert invalid_report.detail_codes == ("source_dataset_layout_invalid",)


def test_runtime_run_preflight_blocks_wrong_tool_versions(
    tmp_path: Path,
) -> None:
    fixture = load_fixture("execution", "preflight_failure_cases.json")
    wrong_version_case = fixture["wrong_version_case"]
    manager = RunManager(
        tmp_path,
        RunConfig.model_validate(
            {
                "predictors_enabled": [str(wrong_version_case["provider_name"])],
                "tool_versions": {
                    str(key): str(value)
                    for key, value in wrong_version_case[
                        "required_tool_versions"
                    ].items()
                },
            }
        ),
    )

    result = manager.run("MPEPTIDE", run_id="preflight-version-mismatch-1")
    failure_report = RuntimeFailureReport.load_json(
        tmp_path
        / "artifacts"
        / "preflight-version-mismatch-1"
        / "failure_report.json"
    )

    assert result["status"] == "failure"
    assert result["failure_type"] == "capability_missing"
    assert failure_report.detail_codes == (
        "spectronaut:expected=19.0:actual=v1",
    )
