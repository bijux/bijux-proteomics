from __future__ import annotations

from bijux_proteomics_dev.governance.package_shape.internal_orphan_modules import (
    INTERNAL_ORPHAN_MODULE_ALLOWLIST_PATH,
    INTERNAL_ORPHAN_MODULE_REPORT_PATH,
    build_internal_orphan_module_report,
    load_internal_orphan_module_policy,
    run,
    validate_internal_orphan_module_report,
)
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    package_root,
    package_test_entrypoint_paths,
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

    assert [item.module_import_path for item in policy.justifications] == [
        "bijux_proteomics_dev.tools.golden_path_example",
        "bijux_proteomics_dev.tools.mre_agentic_protein",
        "bijux_proteomics_dev.tools.visualize_invariants",
    ]


def test_package_test_entrypoint_paths_include_test_bootstraps() -> None:
    package_tests_root = package_root("bijux-proteomics-knowledge") / "tests"
    relative_paths = {
        path.relative_to(package_tests_root.parent).as_posix()
        for path in package_test_entrypoint_paths("bijux-proteomics-knowledge")
    }

    assert "tests/conftest.py" in relative_paths
    assert "tests/memory/conftest.py" in relative_paths
    assert "tests/reviews/conftest.py" in relative_paths
    assert "tests/reviews/test_trends.py" in relative_paths


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
