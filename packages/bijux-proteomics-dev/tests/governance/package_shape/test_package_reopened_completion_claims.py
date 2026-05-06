from __future__ import annotations

from bijux_proteomics_dev.governance.package_shape.package_reopened_completion_claims import (
    PACKAGE_REOPENED_COMPLETION_CLAIMS_PATH,
    build_package_reopened_completion_claim_report,
    run,
    validate_package_reopened_completion_claims,
)


def test_package_reopened_completion_claim_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_reopened_completion_claim_report_tracks_structural_reopenings() -> None:
    report = build_package_reopened_completion_claim_report()
    by_package = {entry.distribution_name: entry for entry in report.entries}

    assert PACKAGE_REOPENED_COMPLETION_CLAIMS_PATH.exists()
    assert by_package["bijux-proteomics-foundation"].reopened_reasons
    assert by_package["bijux-proteomics-runtime"].reopened_completion_claim is True
    assert any(entry.reopened_completion_claim for entry in report.entries)


def test_package_reopened_completion_claim_release_guard_has_no_failures() -> None:
    assert validate_package_reopened_completion_claims() == ()
