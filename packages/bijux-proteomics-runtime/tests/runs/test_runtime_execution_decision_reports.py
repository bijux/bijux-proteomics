from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics_runtime.runs import RunManager
from bijux_proteomics_runtime.runs.context import RunContext, create_run_context
from bijux_proteomics_runtime.runs.execution_decisions import (
    ExecutionDecisionState,
    build_runtime_degraded_execution_report,
    build_runtime_refusal_decision_report,
    load_runtime_execution_decision_report,
)
from bijux_proteomics_runtime.runs.failure_reports import (
    build_runtime_failure_report,
)
from bijux_proteomics_runtime.runs.preflight import (
    build_runtime_preflight_report,
)
from bijux_proteomics_runtime.runs.run_config import RunConfig
from bijux_proteomics_runtime.support.workspace import RunWorkspace


def test_runtime_refusal_decision_report_explains_failed_preflight_checks(
    tmp_path: Path,
) -> None:
    context, _ = create_run_context(tmp_path, run_id="execution-decision-refusal-1")
    missing_source = tmp_path / "missing-import.json"
    preflight_report = build_runtime_preflight_report(
        context.workspace,
        run_id=context.run_id,
        provider_name="spectronaut",
        source_path=missing_source,
        required_tool_versions={"spectronaut": "19.0"},
        available_tool_versions={"spectronaut": "18.5"},
    )
    failure_report = build_runtime_failure_report(
        run_id=context.run_id,
        failure_type="invalid_output",
        message="source dataset is missing",
        detail_codes=("source_dataset_missing",),
    )

    report = build_runtime_refusal_decision_report(
        provider_name="spectronaut",
        preflight_report=preflight_report,
        failure_report=failure_report,
    )

    assert report.decision_state is ExecutionDecisionState.REFUSED
    assert report.failure_category == "validation"
    assert {finding.source_id for finding in report.findings} >= {
        "source_dataset",
        "tool_versions",
        "source_dataset_missing",
    }


def test_runtime_degraded_execution_report_explains_cpu_fallback() -> None:
    report = build_runtime_degraded_execution_report(
        {
            "run_id": "execution-decision-degraded-1",
            "provider": "local_esmfold",
            "tool_status": "degraded",
            "warnings": ["cpu_fallback:local_esmfold_to_cpu"],
        }
    )

    assert report.decision_state is ExecutionDecisionState.DEGRADED
    assert report.findings[0].source_id == "cpu_fallback"


def test_runtime_refusal_decision_report_is_written_for_failed_import_preflight(
    tmp_path: Path,
) -> None:
    manager = RunManager(tmp_path)

    result = manager.import_result(
        sequence="MPEPTIDE",
        source_path=tmp_path / "missing-dia.json",
        imported_payload={"peptides": ["PEPTIDE"]},
        engine_name="spectronaut",
        engine_version="19.0",
        run_id="execution-decision-refusal-2",
    )
    workspace = RunWorkspace.for_run(tmp_path, "execution-decision-refusal-2")
    report = load_runtime_execution_decision_report(workspace)

    assert result["status"] == "failure"
    assert report.decision_state is ExecutionDecisionState.REFUSED
    assert any(finding.source_id == "source_dataset" for finding in report.findings)


def test_runtime_degraded_execution_report_is_written_for_cpu_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_create_run_context = create_run_context

    def _create_run_context_with_cpu_fallback(
        base_dir: Path,
        config: RunConfig | None = None,
        run_id: str | None = None,
    ) -> tuple[RunContext, list[str]]:
        context, warnings = real_create_run_context(base_dir, config, run_id=run_id)
        return context, [*warnings, "cpu_fallback:local_esmfold_to_cpu"]

    monkeypatch.setattr(
        "bijux_proteomics_runtime.runs.manager.create_run_context",
        _create_run_context_with_cpu_fallback,
    )
    manager = RunManager(tmp_path)

    result = manager.run("MPEPTIDE", run_id="execution-decision-degraded-2")
    workspace = RunWorkspace.for_run(tmp_path, "execution-decision-degraded-2")
    report = load_runtime_execution_decision_report(workspace)

    assert result["status"] == "success"
    assert report.decision_state is ExecutionDecisionState.DEGRADED
    assert report.findings[0].source_id == "cpu_fallback"
    assert "degraded mode" in report.operator_summary
