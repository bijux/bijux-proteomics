from __future__ import annotations

import pytest

from bijux_proteomics_dev.governance.dependencies.package_dependency_policy import (
    PACKAGE_DEPENDENCY_POLICY_PATH,
    build_package_dependency_policy_report,
    run,
    validate_package_dependency_policy,
)


@pytest.mark.slow
def test_package_dependency_policy_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_dependency_policy_covers_workspace_packages() -> None:
    report = build_package_dependency_policy_report()
    by_package = {entry.distribution_name: entry for entry in report.entries}

    assert PACKAGE_DEPENDENCY_POLICY_PATH.exists()
    assert len(report.entries) == 16
    assert by_package["agentic-proteins"].allowed_outbound_edges == (
        "bijux-proteomics-core",
        "bijux-proteomics-runtime",
    )
    assert by_package["bijux-proteomics-foundation"].allowed_outbound_edges == ()
    assert by_package["bijux-proteomics-knowledge"].allowed_outbound_edges == (
        "bijux-proteomics-core",
        "bijux-proteomics-foundation",
    )
    assert by_package["bijux-proteomics-core"].allowed_outbound_edges == (
        "bijux-proteomics-foundation",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
        "bijux-proteomics-runtime",
    )
    assert by_package["bijux-proteomics-runtime"].allowed_outbound_edges == (
        "bijux-proteomics-core",
        "bijux-proteomics-foundation",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
    )
    assert by_package["bijux-proteomics-intelligence"].allowed_outbound_edges == (
        "bijux-proteomics-core",
        "bijux-proteomics-foundation",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
        "bijux-proteomics-runtime",
    )
    assert by_package["proteomics-runtime"].allowed_outbound_edges == (
        "bijux-proteomics-foundation",
        "bijux-proteomics-runtime",
    )


@pytest.mark.slow
def test_package_dependency_policy_has_no_live_violations() -> None:
    assert validate_package_dependency_policy() == ()
