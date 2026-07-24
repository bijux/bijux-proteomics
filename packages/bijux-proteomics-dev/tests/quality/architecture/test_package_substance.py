from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.architecture.package_substance import (
    PACKAGE_SUBSTANCE_CSV_PATH,
    PACKAGE_SUBSTANCE_SUMMARY_PATH,
    PackageBoundaryRole,
    build_package_substance_inventory,
    package_substance_report_is_up_to_date,
    validate_package_substance,
)

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_package_substance_report_is_up_to_date() -> None:
    assert package_substance_report_is_up_to_date()


def test_package_substance_inventory_keeps_real_products_and_bridge_explicit() -> None:
    entries = {
        entry.package_name: entry
        for entry in build_package_substance_inventory(REPO_ROOT)
    }

    assert set(entries) == {
        "agentic-proteins",
        "bijux-proteomics-core",
        "bijux-proteomics-dev",
        "bijux-proteomics-foundation",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
        "bijux-proteomics-runtime",
    }
    assert (
        entries["agentic-proteins"].boundary_role
        is PackageBoundaryRole.COMPATIBILITY_BRIDGE
    )
    assert entries["agentic-proteins"].owned_logic_count == 0
    assert entries["agentic-proteins"].wrapper_module_count >= 100
    assert (
        entries["bijux-proteomics-foundation"].boundary_role
        is PackageBoundaryRole.SHARED_KERNEL
    )
    assert entries["bijux-proteomics-foundation"].owned_logic_count >= 12
    assert entries["bijux-proteomics-foundation"].wrapper_module_count == 0
    assert entries["bijux-proteomics-foundation"].thin_module_count <= 2
    assert entries["bijux-proteomics-runtime"].owned_logic_count >= 60
    assert entries["bijux-proteomics-intelligence"].owned_logic_count >= 8
    assert entries["bijux-proteomics-knowledge"].owned_logic_count >= 12
    assert entries["bijux-proteomics-lab"].owned_logic_count >= 10
    assert entries["bijux-proteomics-core"].owned_logic_count >= 70
    assert (
        entries["bijux-proteomics-dev"].boundary_role
        is PackageBoundaryRole.MAINTAINER_SUPPORT
    )
    assert PACKAGE_SUBSTANCE_CSV_PATH.exists()
    assert PACKAGE_SUBSTANCE_SUMMARY_PATH.exists()


def test_package_substance_is_release_clean() -> None:
    assert validate_package_substance(REPO_ROOT) == ()
