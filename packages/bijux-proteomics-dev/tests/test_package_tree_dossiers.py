from __future__ import annotations

from bijux_proteomics_dev.api.package_tree_dossiers import (
    PACKAGE_TREE_DOSSIERS_PATH,
    build_package_tree_dossier_report,
    run,
    validate_package_tree_dossier,
)


def test_package_tree_dossier_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_tree_dossier_report_captures_owner_domains_and_shims() -> None:
    report = build_package_tree_dossier_report()
    entries = {entry.distribution_name: entry for entry in report.entries}

    assert PACKAGE_TREE_DOSSIERS_PATH.exists()
    assert len(report.entries) == 8
    assert "planning" in entries["bijux-proteomics-lab"].owner_domains
    assert "handoffs" in entries["bijux-proteomics-lab"].owner_domains
    assert entries["bijux-proteomics-dev"].public_modules == ("trusted_process",)
    assert len(entries["bijux-proteomics-runtime"].excluded_responsibilities) >= 2
    assert report.guard.min_total_owner_domain_count >= 1
    assert report.guard.min_total_excluded_responsibility_count >= 1


def test_package_tree_dossier_release_guard_has_no_failures() -> None:
    assert validate_package_tree_dossier() == ()
