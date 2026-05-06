from __future__ import annotations

from bijux_proteomics_dev.governance.foundation.kernel_boundaries import (
    FOUNDATION_KERNEL_BOUNDARIES_PATH,
    build_foundation_kernel_boundaries,
    run,
    validate_foundation_kernel_boundaries,
)


def test_foundation_kernel_boundary_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_foundation_kernel_boundary_report_tracks_release_blockers() -> None:
    checks = {check.policy_id: check for check in build_foundation_kernel_boundaries()}

    assert FOUNDATION_KERNEL_BOUNDARIES_PATH.exists()
    assert set(checks) == {
        "no-product-specific-fixtures",
        "no-route-cli-markdown-helpers",
    }
    assert checks["no-product-specific-fixtures"].checked_path_count >= 8
    assert checks["no-product-specific-fixtures"].checked_symbol_count >= 20
    assert checks["no-product-specific-fixtures"].violations == ()
    assert checks["no-route-cli-markdown-helpers"].checked_path_count >= 20
    assert checks["no-route-cli-markdown-helpers"].checked_symbol_count >= 40
    assert checks["no-route-cli-markdown-helpers"].violations == ()


def test_foundation_kernel_boundary_release_guard_has_no_failures() -> None:
    assert validate_foundation_kernel_boundaries() == ()
