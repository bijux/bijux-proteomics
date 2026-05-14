from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.governance.foundation.repository_product_shape import (
    build_repository_product_shape_report,
)
from bijux_proteomics_dev.governance.package_shape.public_surfaces import (
    default_public_surface_contracts,
)

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_agentic_contract_keeps_compatibility_role_explicit() -> None:
    report = build_repository_product_shape_report()
    package = next(
        entry
        for entry in report.packages
        if entry.distribution_name == "agentic-proteins"
    )
    public_surface = next(
        entry
        for entry in default_public_surface_contracts()
        if entry.distribution_name == "agentic-proteins"
    )

    assert package.role_kind == "compatibility"
    assert package.role_summary == (
        "legacy compatibility bridge for runtime entrypoints and imports"
    )
    assert public_surface.supported_attributes == (
        "AppConfig",
        "create_app",
        "RunManager",
        "cli",
    )
    assert public_surface.supported_modules == ()


def test_agentic_contract_spans_docs_readme_and_release_guidance() -> None:
    contract = (
        REPO_ROOT
        / "docs"
        / "02-agentic-proteins"
        / "foundation"
        / "compatibility-contract.md"
    ).read_text(encoding="utf-8")
    overview = (
        REPO_ROOT
        / "docs"
        / "02-agentic-proteins"
        / "foundation"
        / "package-overview.md"
    ).read_text(encoding="utf-8")
    public_imports = (
        REPO_ROOT / "docs" / "02-agentic-proteins" / "interfaces" / "public-imports.md"
    ).read_text(encoding="utf-8")
    runtime_migration = (
        REPO_ROOT
        / "docs"
        / "01-bijux-proteomics"
        / "operations"
        / "runtime-migration-validation.md"
    ).read_text(encoding="utf-8")
    readme = (REPO_ROOT / "packages" / "agentic-proteins" / "README.md").read_text(
        encoding="utf-8"
    )

    assert "compatibility bridge" in contract
    assert "canonical runtime package" in contract
    assert "does not own" in contract
    assert "Compatibility Contract" in overview
    assert "compatibility forwarding" in public_imports
    assert "canonical runtime" in public_imports
    assert "quality-runtime-migration-validation" in runtime_migration
    assert "agentic-proteins` as compatibility" in runtime_migration
    assert "legacy compatibility bridge for runtime entrypoints and imports" in readme
