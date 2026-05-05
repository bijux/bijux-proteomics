from __future__ import annotations

from bijux_proteomics_dev.api.package_thin_modules import (
    PACKAGE_THIN_MODULES_PATH,
    build_package_thin_module_report,
    run,
    validate_package_thin_modules,
)


def test_package_thin_module_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_thin_module_report_tracks_current_merge_or_delete_follow_up() -> None:
    report = build_package_thin_module_report()
    module_paths = {entry.module_path for entry in report.entries}

    assert PACKAGE_THIN_MODULES_PATH.exists()
    assert len(report.entries) >= 10
    assert not any(path.endswith("benchmarks/targeted.py") for path in module_paths)
    assert not any(path.endswith("handoffs/packets.py") for path in module_paths)
    assert any(path.endswith("agents/analysis/failure_analysis.py") for path in module_paths)
    assert not any(path.endswith("ptm_follow_up.py") for path in module_paths)
    assert not any(path.endswith("workflow_readiness.py") for path in module_paths)
    assert not any(path.endswith("targeted_benchmarking.py") for path in module_paths)


def test_package_thin_module_release_guard_has_no_failures() -> None:
    assert validate_package_thin_modules() == ()
