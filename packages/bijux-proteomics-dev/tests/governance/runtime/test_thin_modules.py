from __future__ import annotations

from bijux_proteomics_dev.governance.runtime.thin_modules import (
    RUNTIME_THIN_MODULES_PATH,
    build_runtime_thin_module_report,
    run,
    validate_runtime_thin_modules,
)


def test_runtime_thin_module_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_runtime_thin_module_report_tracks_namespace_initializers_only() -> None:
    report = build_runtime_thin_module_report()
    metrics = report.metrics
    guard = report.guard

    assert RUNTIME_THIN_MODULES_PATH.exists()
    assert metrics.thin_module_count == guard.baseline_thin_module_count
    assert metrics.thin_module_count == 34
    assert metrics.namespace_initializer_count == 34
    assert metrics.non_initializer_thin_module_count == 0
    assert metrics.documented_boundary_doc_count == 8
    assert all(
        entry.module_path.endswith("__init__.py") for entry in metrics.thin_modules
    )


def test_runtime_thin_module_release_guard_has_no_failures() -> None:
    assert validate_runtime_thin_modules() == ()
