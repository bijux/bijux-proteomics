from __future__ import annotations

import pytest

from bijux_proteomics_dev.governance.lab.publishability import (
    LAB_PUBLISHABILITY_PATH,
    build_lab_publishability_report,
    run,
    validate_lab_publishability,
)


@pytest.mark.slow
def test_lab_publishability_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_lab_publishability_requires_operator_trust_signals() -> None:
    report = build_lab_publishability_report()

    assert LAB_PUBLISHABILITY_PATH.exists()
    assert report.root_entrypoint_count == 3
    assert report.source_owner_family_count == 8
    assert report.test_family_count == 9
    assert report.mirrored_owner_family_count == 8
    assert report.flat_test_module_count == 0
    assert report.honesty_ready is True
    assert report.feasibility_ready is True
    assert report.traceability_ready is True
    assert report.ownership_ready is True
    assert report.boundary_ready is True
    assert report.operations_reviewer_ready is True
    assert report.publishable is True


def test_lab_publishability_release_guard_has_no_failures() -> None:
    assert validate_lab_publishability() == ()
