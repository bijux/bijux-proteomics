from __future__ import annotations

from bijux_proteomics_dev.governance.package_shape.package_readme_maturity import (
    PACKAGE_README_MATURITY_PATH,
    build_package_readme_maturity_report,
    run,
    validate_package_readme_maturity,
)


def test_package_readme_maturity_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_readme_maturity_report_tracks_current_overclaim_pressure() -> None:
    report = build_package_readme_maturity_report()
    by_package = {entry.distribution_name: entry for entry in report.entries}

    assert PACKAGE_README_MATURITY_PATH.exists()
    assert len(report.entries) == 16
    assert by_package["bijux-proteomics-runtime"].proof_depth_count >= 1
    assert by_package["bijux-proteomics-core"].maturity_claim_count == 0
    assert by_package["bijux-proteomics-core"].completion_claim_count == 0
    assert by_package["bijux-proteomics-runtime"].maturity_claim_count == 0
    assert not any(entry.maturity_outpaces_owner_logic for entry in report.entries)
    assert not any(entry.completion_claims_while_not_ready for entry in report.entries)


def test_package_readme_maturity_release_guard_has_no_failures() -> None:
    assert validate_package_readme_maturity() == ()
