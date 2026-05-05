from __future__ import annotations

from bijux_proteomics_runtime.agents.catalog import AgentCatalog
from bijux_proteomics_runtime.runs.failure_reports import RuntimeFailureCategory
from bijux_proteomics_runtime.runs.failure_reports import RuntimeFailureReport
from bijux_proteomics_runtime.runs.failure_reports import build_runtime_failure_report
from bijux_proteomics_runtime.runs.failure_reports import write_runtime_failure_report
from bijux_proteomics_runtime.runs.integrity import verify_runtime_artifact_integrity
from bijux_proteomics_runtime.runs.preflight import build_runtime_preflight_report
from bijux_proteomics_runtime.runs.reruns import build_runtime_partial_rerun_plan
from bijux_proteomics_runtime.workflows.paths import run_reviewable_import_path
from bijux_proteomics_runtime.workflows.paths import run_reviewable_sequence_path


def test_runtime_registry_surface_smoke() -> None:
    AgentCatalog.clear()

    class ExampleAgent:
        name = "example"

    AgentCatalog.register(ExampleAgent)
    assert AgentCatalog.get("example") is ExampleAgent


def test_runtime_control_surface_exports_review_and_failure_helpers() -> None:
    _ = RuntimeFailureReport
    _ = build_runtime_preflight_report
    _ = build_runtime_partial_rerun_plan
    _ = run_reviewable_sequence_path
    _ = run_reviewable_import_path
    _ = verify_runtime_artifact_integrity
    _ = write_runtime_failure_report


def test_runtime_control_surface_builds_failure_reports() -> None:
    report = build_runtime_failure_report(
        run_id="run-1",
        failure_type="tool_crash",
        message="provider crashed",
        detail_codes=["scheduler_timeout"],
    )

    assert report.failure_category is RuntimeFailureCategory.SCHEDULER
    assert report.next_action
