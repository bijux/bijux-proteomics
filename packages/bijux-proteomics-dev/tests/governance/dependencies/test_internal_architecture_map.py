from __future__ import annotations

import pytest

from bijux_proteomics_dev.governance.dependencies.internal_architecture_map import (
    INTERNAL_ARCHITECTURE_MAP_PATH,
    build_internal_architecture_map_report,
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
