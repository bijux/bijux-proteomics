from __future__ import annotations

import pytest

from bijux_proteomics_dev.governance.dependencies.package_dependency_dossiers import (
    PACKAGE_DEPENDENCY_DOSSIERS_PATH,
    build_package_dependency_dossier_report,
    run,
    validate_package_dependency_dossiers,
)

pytestmark = pytest.mark.slow


def test_package_dependency_dossiers_are_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_dependency_dossiers_capture_allowed_and_actual_edges() -> None:
    report = build_package_dependency_dossier_report()
    by_package = {entry.distribution_name: entry for entry in report.entries}

    assert PACKAGE_DEPENDENCY_DOSSIERS_PATH.exists()
    assert by_package["bijux-proteomics-runtime"].actual_outbound_edges == (
        "bijux-proteomics-core",
        "bijux-proteomics-foundation",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
    )
    assert (
        "bijux-proteomics-runtime"
        in by_package["bijux-proteomics-core"].actual_outbound_edges
    )
    assert by_package["bijux-proteomics-foundation"].actual_inbound_edges
    assert by_package["bijux-proteomics-foundation"].unexpected_outbound_edges == ()


def test_package_dependency_dossiers_have_no_unexpected_edges() -> None:
    assert validate_package_dependency_dossiers() == ()
