from __future__ import annotations

from bijux_proteomics_dev.api.package_release_dossiers import (
    PACKAGE_RELEASE_DOSSIERS_PATH,
    build_package_release_dossier_report,
    run,
    validate_package_release_dossiers,
)


def test_package_release_dossiers_are_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_release_dossiers_keep_strengths_limits_and_debt_explicit() -> None:
    report = build_package_release_dossier_report()
    by_package = {entry.distribution_name: entry for entry in report.entries}

    assert PACKAGE_RELEASE_DOSSIERS_PATH.exists()
    assert len(report.entries) == 8
    assert by_package["bijux-proteomics-core"].proofs
    assert by_package["bijux-proteomics-foundation"].limits
    assert by_package["bijux-proteomics-lab"].unresolved_debt_ids
    assert by_package["bijux-proteomics-lab"].publishable is False
    assert by_package["bijux-proteomics-runtime"].strengths


def test_package_release_dossiers_do_not_mark_debt_as_publishable() -> None:
    assert validate_package_release_dossiers() == ()
