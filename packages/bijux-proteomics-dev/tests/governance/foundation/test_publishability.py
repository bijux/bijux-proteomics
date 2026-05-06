from __future__ import annotations

import ast
from pathlib import Path

from bijux_proteomics_dev.governance.foundation.publishability import (
    FOUNDATION_PUBLISHABILITY_PATH,
    build_foundation_publishability_report,
    run,
    validate_foundation_publishability,
)


REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
PRODUCT_IMPORT_ROOTS = {
    "bijux-proteomics-core": "bijux_proteomics",
    "bijux-proteomics-runtime": "bijux_proteomics_runtime",
    "bijux-proteomics-intelligence": "bijux_proteomics_intelligence",
    "bijux-proteomics-knowledge": "bijux_proteomics_knowledge",
    "bijux-proteomics-lab": "bijux_proteomics_lab",
}
FOUNDATION_README = REPO_ROOT / "packages" / "bijux-proteomics-foundation" / "README.md"
FOUNDATION_CONTRACTS = (
    REPO_ROOT / "packages" / "bijux-proteomics-foundation" / "docs" / "CONTRACTS.md"
)
FOUNDATION_SCOPE = (
    REPO_ROOT
    / "docs"
    / "03-bijux-proteomics-foundation"
    / "foundation"
    / "scope-and-non-goals.md"
)
FOUNDATION_DOCS_ROOT = REPO_ROOT / "docs" / "03-bijux-proteomics-foundation"


def _foundation_consumers() -> set[str]:
    consumers: set[str] = set()
    packages_root = REPO_ROOT / "packages"
    for package_name, import_root in PRODUCT_IMPORT_ROOTS.items():
        src_root = packages_root / package_name / "src" / import_root
        for path in src_root.rglob("*.py"):
            tree = ast.parse(path.read_text(), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    if any(
                        alias.name == "bijux_proteomics_foundation"
                        or alias.name.startswith("bijux_proteomics_foundation.")
                        for alias in node.names
                    ):
                        consumers.add(package_name)
                        break
                if isinstance(node, ast.ImportFrom) and node.module is not None:
                    if (
                        node.module == "bijux_proteomics_foundation"
                        or node.module.startswith("bijux_proteomics_foundation.")
                    ):
                        consumers.add(package_name)
                        break
            if package_name in consumers:
                break
    return consumers


def test_foundation_is_a_real_shared_dependency_for_every_product_package() -> None:
    assert _foundation_consumers() == set(PRODUCT_IMPORT_ROOTS)


def test_foundation_publishable_docs_reference_current_contract_entrypoints() -> None:
    readme = FOUNDATION_README.read_text()
    contracts = FOUNDATION_CONTRACTS.read_text()
    docs = "\n".join(
        path.read_text() for path in sorted(FOUNDATION_DOCS_ROOT.rglob("*.md"))
    )
    combined = f"{readme}\n{contracts}\n{docs}"

    for stale_entrypoint in (
        "bijux_proteomics_foundation.schema",
        "bijux_proteomics_foundation.evolution",
    ):
        assert f"`{stale_entrypoint}`" not in combined
    for stale_module in (
        "src/bijux_proteomics_foundation/schema.py",
        "src/bijux_proteomics_foundation/serialization.py",
        "src/bijux_proteomics_foundation/ids.py",
        "src/bijux_proteomics_foundation/documents.py",
        "src/bijux_proteomics_foundation/errors.py",
        "src/bijux_proteomics_foundation/migrations.py",
        "src/bijux_proteomics_foundation/serialization/documents.py",
        "src/bijux_proteomics_foundation/compatibility/migrations.py",
    ):
        assert stale_module not in combined
    for current_entrypoint in (
        "identity",
        "compatibility",
        "outcomes",
        "serialization",
        "support",
    ):
        assert f"`{current_entrypoint}`" in combined


def test_foundation_docs_state_explicit_non_goals_for_kernel_boundary() -> None:
    combined = "\n".join(
        (
            FOUNDATION_README.read_text(),
            FOUNDATION_CONTRACTS.read_text(),
            FOUNDATION_SCOPE.read_text(),
        )
    )

    for expected_text in (
        "product-specific fixtures",
        "workflow examples",
        "route-shaped, CLI-shaped, and Markdown-shaped",
    ):
        assert expected_text in combined


def test_foundation_publishability_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_foundation_publishability_keeps_surface_narrow_and_reused() -> None:
    report = build_foundation_publishability_report()

    assert FOUNDATION_PUBLISHABILITY_PATH.exists()
    assert report.supported_attributes == (
        "DocumentSchema",
        "JsonModel",
        "hash_payload",
        "to_canonical_json",
    )
    assert report.supported_attribute_count == 4
    assert report.root_public_symbol_count == 15
    assert report.downstream_distribution_count == 6
    assert report.supported_multi_distribution_count == 4
    assert report.supported_single_distribution_count == 0
    assert report.unsupported_reuse_gaps == ()
    assert report.kernel_boundaries_ready is True
    assert report.size_reuse_ready is True
    assert report.publishable is True


def test_foundation_publishability_release_guard_has_no_failures() -> None:
    assert validate_foundation_publishability() == ()
