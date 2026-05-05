from __future__ import annotations

from bijux_proteomics_dev.api.lab_packet_only_modules import (
    LAB_PACKET_ONLY_MODULES_PATH,
    build_lab_module_shape_report,
    run,
    validate_lab_module_shapes,
)


def test_lab_module_shape_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_lab_module_shape_report_tracks_reshaping_only_facades() -> None:
    report = build_lab_module_shape_report()
    entries = report.metrics.entries
    reshaping_only = {entry.module_path for entry in entries if entry.shape == "reshaping_only"}
    packet_only = {entry.module_path for entry in entries if entry.shape == "packet_only"}

    assert LAB_PACKET_ONLY_MODULES_PATH.exists()
    assert report.metrics.packet_only_module_count == 1
    assert report.guard.max_packet_only_module_count == 1
    assert report.metrics.reshaping_only_module_count == 17
    assert report.metrics.reshaping_only_module_count == report.guard.max_reshaping_only_module_count
    assert packet_only == {"charter.py"}
    assert {
        "__init__.py",
        "artifacts.py",
        "handoffs/packets.py",
        "targeted_benchmarking.py",
        "workflow_readiness.py",
    }.issubset(reshaping_only)


def test_lab_module_shape_release_guard_has_no_failures() -> None:
    assert validate_lab_module_shapes() == ()
