from __future__ import annotations

from bijux_proteomics_dev.governance.package_shape.package_module_ledger import (
    PACKAGE_MODULE_LEDGER_PATH,
    build_package_module_ledger_report,
    validate_package_module_ledger,
)


def test_package_module_ledger_classifies_owner_wrapper_and_test_modules() -> None:
    report = build_package_module_ledger_report()
    by_path = {entry.module_path: entry for entry in report.entries}

    assert PACKAGE_MODULE_LEDGER_PATH.exists()
    assert (
        by_path[
            "packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation/__init__.py"
        ].module_kind
        == "root_export_surface"
    )
    assert (
        by_path[
            "packages/bijux-proteomics-core/src/bijux_proteomics/governance/charter.py"
        ].module_kind
        == "owner_logic"
    )
    assert (
        by_path[
            "packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge/memory/models/claims.py"
        ].module_kind
        == "owner_logic"
    )
    assert (
        by_path["packages/bijux-proteomics-knowledge/tests/conftest.py"].module_kind
        == "test_only_helper"
    )


def test_package_module_ledger_release_guard_has_no_failures() -> None:
    assert validate_package_module_ledger() == ()
