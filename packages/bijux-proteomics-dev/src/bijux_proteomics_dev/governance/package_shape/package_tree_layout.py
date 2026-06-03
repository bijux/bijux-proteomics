from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import tomllib
from typing import Any, cast

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    package_root,
    root_python_modules,
    source_owner_families,
    workspace_package_names,
)

__all__ = [
    "CANONICAL_PACKAGE_TREE_LAYOUT_PATH",
    "PackageTreeLayoutEntry",
    "PackageTreeLayoutPolicy",
    "build_package_tree_layout_report",
    "load_package_tree_layout_policy",
    "run",
    "validate_package_tree_layout",
]


CANONICAL_PACKAGE_TREE_LAYOUT_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "canonical-package-tree-layout.toml"
)


@dataclass(frozen=True)
class PackageTreeLayoutEntry:
    """Allowed top-level package tree for one workspace distribution."""

    distribution_name: str
    import_roots: tuple[str, ...]
    top_level_families: tuple[str, ...]
    root_module_files: tuple[str, ...]


@dataclass(frozen=True)
class PackageTreeLayoutPolicy:
    """Checked canonical package tree policy across workspace packages."""

    name: str
    packages: tuple[PackageTreeLayoutEntry, ...]


def load_package_tree_layout_policy(
    path: Path = CANONICAL_PACKAGE_TREE_LAYOUT_PATH,
) -> PackageTreeLayoutPolicy:
    """Load the canonical package tree manifest."""

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    policy = cast(dict[str, Any], data["policy"])
    package_tables = cast(list[dict[str, Any]], data.get("package", []))
    return PackageTreeLayoutPolicy(
        name=str(policy["name"]),
        packages=tuple(
            PackageTreeLayoutEntry(
                distribution_name=str(table["distribution_name"]),
                import_roots=tuple(str(value) for value in table["import_roots"]),
                top_level_families=tuple(
                    str(value) for value in table["top_level_families"]
                ),
                root_module_files=tuple(
                    str(value) for value in table["root_module_files"]
                ),
            )
            for table in package_tables
        ),
    )


def build_package_tree_layout_report() -> PackageTreeLayoutPolicy:
    """Build the live top-level package tree report for workspace packages."""

    entries = tuple(
        _actual_package_tree_entry(package_name)
        for package_name in workspace_package_names()
    )
    return PackageTreeLayoutPolicy(
        name="canonical-package-tree-layout",
        packages=tuple(sorted(entries, key=lambda entry: entry.distribution_name)),
    )


def validate_package_tree_layout(
    report: PackageTreeLayoutPolicy | None = None,
    policy: PackageTreeLayoutPolicy | None = None,
) -> tuple[str, ...]:
    """Validate the live package tree against the canonical allowed layout."""

    report = report or build_package_tree_layout_report()
    policy = policy or load_package_tree_layout_policy()
    actual_by_package = {entry.distribution_name: entry for entry in report.packages}
    expected_by_package = {entry.distribution_name: entry for entry in policy.packages}
    failures: list[str] = []
    if tuple(sorted(actual_by_package)) != tuple(sorted(expected_by_package)):
        failures.append("canonical package tree manifest package coverage drifted")
        return tuple(failures)
    for package_name in sorted(expected_by_package):
        expected = expected_by_package[package_name]
        actual = actual_by_package[package_name]
        if actual.import_roots != expected.import_roots:
            failures.append(
                f"{package_name} import roots {actual.import_roots!r} do not match "
                f"the canonical layout {expected.import_roots!r}"
            )
        if actual.top_level_families != expected.top_level_families:
            failures.append(
                f"{package_name} top-level families {actual.top_level_families!r} do "
                f"not match the canonical layout {expected.top_level_families!r}"
            )
        if actual.root_module_files != expected.root_module_files:
            failures.append(
                f"{package_name} root module files {actual.root_module_files!r} do not "
                f"match the canonical layout {expected.root_module_files!r}"
            )
    return tuple(failures)


def _actual_package_tree_entry(package_name: str) -> PackageTreeLayoutEntry:
    src_dir = package_root(package_name) / "src"
    import_roots = tuple(
        sorted(
            path.name
            for path in src_dir.iterdir()
            if path.is_dir() and path.name != "__pycache__"
        )
    )
    root_module_files = tuple(
        sorted(
            path.name
            for path in root_python_modules(package_name)
            if path.name != "__init__.py"
        )
    )
    return PackageTreeLayoutEntry(
        distribution_name=package_name,
        import_roots=import_roots,
        top_level_families=source_owner_families(package_name),
        root_module_files=root_module_files,
    )


def run(*, check: bool = False) -> int:
    """Validate the canonical top-level package tree layout."""

    _ = check
    failures = validate_package_tree_layout()
    if failures:
        for failure in failures:
            print(failure)
        return 1
    print("canonical package tree layout passed")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate the canonical top-level package tree layout."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if live package trees drift from the canonical layout.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
