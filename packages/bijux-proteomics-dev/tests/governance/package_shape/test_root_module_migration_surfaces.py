from __future__ import annotations

from bijux_proteomics_dev.governance.package_shape.root_module_migration_surfaces import (
    ROOT_MODULE_MIGRATION_SURFACES_PATH,
    RootModuleMigrationSurfaceEntry,
    build_root_module_migration_surface_report,
    run,
    validate_root_module_migration_surface_report,
)


def test_root_module_migration_surface_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_root_module_migration_surface_report_tracks_legacy_import_paths() -> None:
    report = build_root_module_migration_surface_report()
    by_legacy_import = {
        entry.legacy_import_path: entry for entry in report.entries
    }

    assert ROOT_MODULE_MIGRATION_SURFACES_PATH.exists()
    assert len(report.entries) == 3
    assert by_legacy_import["bijux_proteomics.tabular"] == RootModuleMigrationSurfaceEntry(
        distribution_name="bijux-proteomics-core",
        legacy_import_path="bijux_proteomics.tabular",
        canonical_import_path="bijux_proteomics._tabular",
        module_file="tabular.py",
        retirement_condition=(
            "retire when downstream callers import the canonical private delimited-table "
            "owner or move to narrower package-owned contracts"
        ),
        rationale="shared delimited-table parsing moved behind a private implementation owner",
    )
    assert by_legacy_import[
        "bijux_proteomics.scientific_tables"
    ] == RootModuleMigrationSurfaceEntry(
        distribution_name="bijux-proteomics-core",
        legacy_import_path="bijux_proteomics.scientific_tables",
        canonical_import_path="bijux_proteomics._scientific_tables",
        module_file="scientific_tables.py",
        retirement_condition=(
            "retire when downstream callers import the canonical private scientific-table "
            "owner or move to narrower workflow and contract surfaces"
        ),
        rationale="governed scientific-table schema validation moved behind a private owner",
    )
    assert by_legacy_import[
        "bijux_proteomics_foundation.package_aliases"
    ] == RootModuleMigrationSurfaceEntry(
        distribution_name="bijux-proteomics-foundation",
        legacy_import_path="bijux_proteomics_foundation.package_aliases",
        canonical_import_path="bijux_proteomics_foundation._package_aliases",
        module_file="package_aliases.py",
        retirement_condition=(
            "retire when alias-package wrappers and downstream imports use the private owner "
            "or stop depending on package-level alias forwarding entirely"
        ),
        rationale="alias-package helper ownership moved behind a private implementation module",
    )


def test_root_module_migration_surface_report_has_no_validation_failures() -> None:
    assert validate_root_module_migration_surface_report() == ()
