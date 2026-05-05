from __future__ import annotations

from bijux_proteomics_dev.api.lab_operational_ownership import (
    LAB_OPERATIONAL_OWNERSHIP_PATH,
    REQUIRED_SOURCE_OWNER_FAMILIES,
    REQUIRED_TEST_FAMILIES,
    build_lab_operational_ownership_report,
    run,
    validate_lab_operational_ownership,
)


def test_lab_operational_ownership_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_lab_operational_ownership_requires_deep_owner_and_test_families() -> None:
    report = build_lab_operational_ownership_report()
    metrics = report.metrics

    assert LAB_OPERATIONAL_OWNERSHIP_PATH.exists()
    assert metrics.source_owner_families == REQUIRED_SOURCE_OWNER_FAMILIES
    assert metrics.test_families == REQUIRED_TEST_FAMILIES
    assert metrics.flat_test_module_count == 0
    assert metrics.mirrored_owner_family_count == len(REQUIRED_SOURCE_OWNER_FAMILIES)
    assert metrics.operational_value_module_count > metrics.thin_abstraction_module_count
    assert report.ownership_ready is True


def test_lab_operational_ownership_release_guard_has_no_failures() -> None:
    assert validate_lab_operational_ownership() == ()
