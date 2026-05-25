from __future__ import annotations

from bijux_proteomics_dev.governance.package_shape.top_level_module_visibility import (
    TOP_LEVEL_MODULE_VISIBILITY_PATH,
    PackageTopLevelModuleVisibilityEntry,
    PackageTopLevelModuleVisibilityReport,
    build_top_level_module_visibility_report,
    run,
    validate_top_level_module_visibility,
)


def test_top_level_module_visibility_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_top_level_module_visibility_report_tracks_public_and_private_leaf_modules() -> None:
    report = build_top_level_module_visibility_report()
    entries = {entry.distribution_name: entry for entry in report.entries}

    assert TOP_LEVEL_MODULE_VISIBILITY_PATH.exists()
    assert len(report.entries) == 6
    assert entries["bijux-proteomics-foundation"] == PackageTopLevelModuleVisibilityEntry(
        distribution_name="bijux-proteomics-foundation",
        public_module_files=(),
        private_module_files=("_package_aliases.py",),
    )
    assert entries["bijux-proteomics-core"] == PackageTopLevelModuleVisibilityEntry(
        distribution_name="bijux-proteomics-core",
        public_module_files=("programs.py",),
        private_module_files=("_scientific_tables.py", "_tabular.py"),
    )
    assert entries["bijux-proteomics-intelligence"] == PackageTopLevelModuleVisibilityEntry(
        distribution_name="bijux-proteomics-intelligence",
        public_module_files=(
            "belief_audit.py",
            "contradictions.py",
            "falsifiers.py",
            "next_steps.py",
            "query.py",
            "refusal.py",
        ),
        private_module_files=(),
    )


def test_top_level_module_visibility_validator_rejects_unhidden_private_modules() -> None:
    report = PackageTopLevelModuleVisibilityReport(
        entries=(
            PackageTopLevelModuleVisibilityEntry(
                distribution_name="bijux-proteomics-core",
                public_module_files=("programs.py",),
                private_module_files=("scientific_tables.py",),
            ),
        )
    )

    failures = validate_top_level_module_visibility(report)

    assert failures == (
        "bijux-proteomics-core exposes undeclared top-level modules without private naming: scientific_tables.py",
    )
