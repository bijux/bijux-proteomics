from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PRODUCT_IMPORT_ROOTS = {
    "bijux-proteomics-core": "bijux_proteomics",
    "bijux-proteomics-runtime": "bijux_proteomics_runtime",
    "bijux-proteomics-intelligence": "bijux_proteomics_intelligence",
    "bijux-proteomics-knowledge": "bijux_proteomics_knowledge",
    "bijux-proteomics-lab": "bijux_proteomics_lab",
}
FOUNDATION_README = (
    REPO_ROOT / "packages" / "bijux-proteomics-foundation" / "README.md"
)
FOUNDATION_CONTRACTS = (
    REPO_ROOT
    / "packages"
    / "bijux-proteomics-foundation"
    / "docs"
    / "CONTRACTS.md"
)


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
                    if node.module == "bijux_proteomics_foundation" or node.module.startswith(
                        "bijux_proteomics_foundation."
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
    combined = f"{readme}\n{contracts}"

    for stale_entrypoint in ("schema", "serialization"):
        assert f"`{stale_entrypoint}`" not in combined
    for stale_module in ("schema.py", "serialization.py", "evolution.py"):
        assert stale_module not in combined
    for current_entrypoint in (
        "charter",
        "documents",
        "compatibility",
        "hashing",
        "ids",
        "json_models",
        "migrations",
    ):
        assert f"`{current_entrypoint}`" in combined
