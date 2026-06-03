from __future__ import annotations

import pytest
from pytest import MonkeyPatch

from bijux_proteomics_dev.governance.dependencies.internal_architecture_map import (
    INTERNAL_ARCHITECTURE_MAP_PATH,
    build_internal_architecture_map_report,
    evaluate_internal_architecture_violations,
    run,
)


@pytest.mark.slow
def test_internal_architecture_map_is_up_to_date() -> None:
    assert INTERNAL_ARCHITECTURE_MAP_PATH.exists()
    assert run(check=True) == 0


def test_internal_architecture_map_reports_package_and_module_owners() -> None:
    report = build_internal_architecture_map_report()

    package_names = {entry.distribution_name for entry in report.package_entries}
    family_names = {
        (entry.distribution_name, entry.family_name)
        for entry in report.module_family_entries
    }

    assert "bijux-proteomics-foundation" in package_names
    assert "bijux-proteomics-core" in package_names
    assert "bijux-proteomics-runtime" in package_names
    assert (
        "bijux-proteomics-core",
        "workflow_pipelines",
    ) in family_names
    assert (
        "bijux-proteomics-core",
        "workflow_compatibility",
    ) in family_names
    assert report.cycle_guard.max_workspace_cycle_count == 0


def test_internal_architecture_map_respects_explicit_empty_workspace_cycles(
    monkeypatch: MonkeyPatch,
) -> None:
    report = build_internal_architecture_map_report()

    def fail_if_called(repo_root: object) -> tuple[tuple[str, ...], ...]:
        raise AssertionError("workspace cycle discovery should be bypassed")

    monkeypatch.setattr(
        "bijux_proteomics_dev.governance.dependencies.internal_architecture_map.find_workspace_dependency_cycles",
        fail_if_called,
    )

    assert evaluate_internal_architecture_violations(report, workspace_cycles=()) == ()
