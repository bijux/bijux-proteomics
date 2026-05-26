from __future__ import annotations

from bijux_proteomics_dev.governance.package_shape.internal_orphan_modules import (
    INTERNAL_ORPHAN_MODULE_ALLOWLIST_PATH,
    INTERNAL_ORPHAN_MODULE_REPORT_PATH,
    build_internal_orphan_module_report,
    load_internal_orphan_module_policy,
    run,
    validate_internal_orphan_module_report,
)


def test_internal_orphan_module_artifacts_are_repository_owned() -> None:
    assert INTERNAL_ORPHAN_MODULE_ALLOWLIST_PATH.as_posix().endswith(
        "configs/package-governance/internal-orphan-module-allowlist.toml"
    )
    assert INTERNAL_ORPHAN_MODULE_REPORT_PATH.as_posix().endswith(
        "configs/package-governance/internal-orphan-modules.toml"
    )


def test_internal_orphan_module_allowlist_covers_only_manual_example_tools() -> None:
    policy = load_internal_orphan_module_policy()

    assert [
        item.module_import_path for item in policy.justifications
    ] == [
        "bijux_proteomics_dev.tools.golden_path_example",
        "bijux_proteomics_dev.tools.mre_agentic_protein",
        "bijux_proteomics_dev.tools.visualize_invariants",
    ]


def test_live_internal_orphan_module_report_is_fully_justified() -> None:
    report = build_internal_orphan_module_report()

    assert [entry.module_import_path for entry in report.entries] == [
        "bijux_proteomics_dev.tools.golden_path_example",
        "bijux_proteomics_dev.tools.mre_agentic_protein",
        "bijux_proteomics_dev.tools.visualize_invariants",
    ]
    assert report.unexpected_entries == ()
    assert report.stale_justifications == ()
    assert validate_internal_orphan_module_report(report) == ()
    assert run(check=True) == 0
