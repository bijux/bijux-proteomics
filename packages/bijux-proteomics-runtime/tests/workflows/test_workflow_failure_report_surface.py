# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.runs.failure_reports import RuntimeFailureCategory
from bijux_proteomics_runtime.support.primitives.failures import FailureType
from bijux_proteomics_runtime.workflows.failure_reports import (
    WorkflowFailureReport,
    build_workflow_failure_report,
    write_workflow_failure_report,
)


def test_workflow_failure_report_preserves_reason_codes_and_category() -> None:
    report = build_workflow_failure_report(
        workflow_id="advanced-diann-runtime-deadbeef",
        workflow_name="advanced_diann",
        stage_id="advanced-diann-input-validation",
        failure_type=FailureType.INPUT_INVALID.value,
        message="design rows were rejected",
        reason_codes=("missing_design_value", "invalid_design_row"),
    )

    assert isinstance(report, WorkflowFailureReport)
    assert report.workflow_name == "advanced_diann"
    assert report.stage_id == "advanced-diann-input-validation"
    assert report.failure_category is RuntimeFailureCategory.VALIDATION
    assert report.reason_codes == ("invalid_design_row", "missing_design_value")


def test_write_workflow_failure_report_persists_failure_report_json(tmp_path: Path) -> None:
    report = build_workflow_failure_report(
        workflow_id="advanced-diann-runtime-deadbeef",
        workflow_name="advanced_diann",
        stage_id="advanced-diann-input-validation",
        failure_type=FailureType.INPUT_INVALID.value,
        message="design rows were rejected",
        reason_codes=("missing_design_value",),
    )

    path = write_workflow_failure_report(tmp_path, report)
    persisted = WorkflowFailureReport.load_json(path)

    assert path.name == "failure_report.json"
    assert persisted.reason_codes == ("missing_design_value",)
    assert persisted.failure_category is RuntimeFailureCategory.VALIDATION
