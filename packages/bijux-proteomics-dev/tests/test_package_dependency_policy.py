from __future__ import annotations

from bijux_proteomics_dev.api.package_dependency_policy import (
    PACKAGE_DEPENDENCY_POLICY_PATH,
    build_package_dependency_policy_report,
    run,
    validate_package_dependency_policy,
)


def test_package_dependency_policy_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_dependency_policy_covers_workspace_packages() -> None:
    report = build_package_dependency_policy_report()
    by_package = {entry.distribution_name: entry for entry in report.entries}

    assert PACKAGE_DEPENDENCY_POLICY_PATH.exists()
    assert len(report.entries) == 8
    assert by_package["bijux-proteomics-foundation"].allowed_outbound_edges == ()
    assert by_package["bijux-proteomics-knowledge"].allowed_outbound_edges == (
        "bijux-proteomics-foundation",
    )
    assert "bijux-proteomics-core" in by_package["bijux-proteomics-runtime"].allowed_outbound_edges


def test_package_dependency_policy_has_no_live_violations() -> None:
    assert validate_package_dependency_policy() == ()
