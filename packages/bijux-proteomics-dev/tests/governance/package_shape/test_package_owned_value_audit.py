from __future__ import annotations

import pytest

from bijux_proteomics_dev.governance.package_shape.package_owned_value_audit import (
    PACKAGE_OWNED_VALUE_AUDIT_PATH,
    build_package_owned_value_audit_report,
    run,
    validate_package_owned_value_audit,
)


@pytest.mark.slow
def test_package_owned_value_audit_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_owned_value_audit_tracks_current_documented_value() -> None:
    report = build_package_owned_value_audit_report()
    by_package = {entry.distribution_name: entry for entry in report.entries}

    assert PACKAGE_OWNED_VALUE_AUDIT_PATH.exists()
    assert len(report.entries) == 16
    assert by_package["bijux-proteomics-foundation"].owned_value_bullets
    assert by_package["bijux-proteomics-core"].owner_depth_count >= 10
    assert (
        "candidate ranking"
        in by_package["bijux-proteomics-intelligence"].owned_value_summary
    )


def test_package_owned_value_audit_release_guard_has_no_failures() -> None:
    assert validate_package_owned_value_audit() == ()
