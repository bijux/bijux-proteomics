from __future__ import annotations

import argparse
from dataclasses import dataclass
import importlib
from pathlib import Path
from typing import Protocol

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    import_root,
    root_api_policy_path,
    src_root,
    workspace_import_path,
)

__all__ = [
    "PublicApiSnapshotEntry",
    "PublicApiSnapshotPackage",
    "build_public_api_snapshot_packages",
    "run",
    "validate_public_api_snapshots",
]


CANONICAL_PUBLIC_API_PACKAGES = (
    "bijux-proteomics-foundation",
    "bijux-proteomics-core",
    "bijux-proteomics-knowledge",
    "bijux-proteomics-intelligence",
    "bijux-proteomics-lab",
    "bijux-proteomics-runtime",
)


@dataclass(frozen=True)
class PublicApiSnapshotEntry:
    """One stable public root export recorded in the governed snapshot."""

    export_name: str
    owner_module: str
    classification: str | None
    rationale: str


@dataclass(frozen=True)
class PublicApiSnapshotPackage:
    """One canonical package root with its explicit public API snapshot."""

    distribution_name: str
    import_root_name: str
    max_public_symbols: int
    max_init_lines: int
    entries: tuple[PublicApiSnapshotEntry, ...]


class _SnapshotSourceEntry(Protocol):
    export_name: object
    owner_module: object


def _public_api_module_name(package_name: str) -> str:
    return f"{import_root(package_name)}.public_api"


def _entry_list(module: object) -> tuple[_SnapshotSourceEntry, ...]:
    for attribute_name in dir(module):
        if (
            attribute_name.startswith("list_")
            and attribute_name.endswith("_root_api_entries")
        ) or attribute_name == "list_foundation_root_api_entries":
            value = getattr(module, attribute_name)
            return tuple(value())
    raise RuntimeError(f"Unable to locate public API entry list on {module!r}")


def _budget(module: object) -> tuple[int, int]:
    for attribute_name in dir(module):
        if attribute_name.endswith("_ROOT_API_BUDGET"):
            budget = getattr(module, attribute_name)
            return int(budget.max_public_symbols), int(budget.max_init_lines)
    raise RuntimeError(f"Unable to locate public API budget on {module!r}")


def _classification(entry: object) -> str | None:
    value = getattr(entry, "classification", None)
    if value is not None:
        return str(value)
    capability = getattr(entry, "capability", None)
    if capability is not None:
        return str(getattr(capability, "value", capability))
    return None


def _rationale(entry: object) -> str:
    rationale = getattr(entry, "rationale", None)
    if rationale is not None:
        return str(rationale)
    kernel_rationale = getattr(entry, "kernel_rationale", None)
    if kernel_rationale is not None:
        return str(kernel_rationale)
    raise RuntimeError(f"Unable to locate rationale on {entry!r}")


def build_public_api_snapshot_packages() -> tuple[PublicApiSnapshotPackage, ...]:
    """Build the checked public API snapshots for canonical packages."""

    packages: list[PublicApiSnapshotPackage] = []
    with workspace_import_path():
        for package_name in CANONICAL_PUBLIC_API_PACKAGES:
            import_root_name = import_root(package_name)
            public_api_module = importlib.import_module(
                _public_api_module_name(package_name)
            )
            max_public_symbols, max_init_lines = _budget(public_api_module)
            entries = tuple(
                PublicApiSnapshotEntry(
                    export_name=str(entry.export_name),
                    owner_module=str(entry.owner_module),
                    classification=_classification(entry),
                    rationale=_rationale(entry),
                )
                for entry in _entry_list(public_api_module)
            )
            packages.append(
                PublicApiSnapshotPackage(
                    distribution_name=package_name,
                    import_root_name=import_root_name,
                    max_public_symbols=max_public_symbols,
                    max_init_lines=max_init_lines,
                    entries=entries,
                )
            )
    return tuple(packages)


def validate_public_api_snapshots(
    packages: tuple[PublicApiSnapshotPackage, ...] | None = None,
) -> tuple[str, ...]:
    """Validate that explicit package public API files still match live roots."""

    packages = packages or build_public_api_snapshot_packages()
    failures: list[str] = []
    with workspace_import_path():
        for package in packages:
            module = importlib.import_module(package.import_root_name)
            exported_names = tuple(getattr(module, "__all__", ()))
            expected_names = tuple(entry.export_name for entry in package.entries)
            if exported_names != expected_names:
                failures.append(
                    f"{package.distribution_name} public API snapshot no longer matches {package.import_root_name}.__all__"
                )
            if len(set(expected_names)) != len(expected_names):
                failures.append(
                    f"{package.distribution_name} public API snapshot contains duplicate exports"
                )
            if len(expected_names) > package.max_public_symbols:
                failures.append(
                    f"{package.distribution_name} public API exceeded its governed symbol budget"
                )
            init_line_count = len(
                (src_root(package.distribution_name) / "__init__.py")
                .read_text(encoding="utf-8")
                .splitlines()
            )
            if init_line_count > package.max_init_lines:
                failures.append(
                    f"{package.distribution_name} public API exceeded its governed __init__ line budget"
                )
            if not all(entry.owner_module for entry in package.entries):
                failures.append(
                    f"{package.distribution_name} public API snapshot contains a blank owner module"
                )
            if not all(entry.rationale for entry in package.entries):
                failures.append(
                    f"{package.distribution_name} public API snapshot contains a blank rationale"
                )
    return tuple(failures)


def _escape(value: str) -> str:
    return value.replace('"', '\\"')


def _toml_text(package: PublicApiSnapshotPackage) -> str:
    lines = [
        f"# Generated {package.distribution_name} root API policy.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.public_api_snapshots",
        "",
        "[budget]",
        f"max_public_symbols = {package.max_public_symbols}",
        f"max_init_lines = {package.max_init_lines}",
        "",
    ]
    for entry in package.entries:
        lines.extend(
            [
                "[[symbol]]",
                f'name = "{entry.export_name}"',
                f'owner_module = "{entry.owner_module}"',
            ]
        )
        if entry.classification is not None:
            lines.append(f'classification = "{entry.classification}"')
        lines.extend(
            [
                f'rationale = "{_escape(entry.rationale)}"',
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(package: PublicApiSnapshotPackage, path: Path) -> bool:
    if not path.exists():
        return False
    return path.read_text(encoding="utf-8") == _toml_text(package)


def run(check: bool = False) -> int:
    packages = build_public_api_snapshot_packages()
    failures = validate_public_api_snapshots(packages)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    stale_paths: list[str] = []
    for package in packages:
        path = root_api_policy_path(package.distribution_name)
        if path is None:
            continue
        if check:
            if not _is_up_to_date(package, path):
                stale_paths.append(path.relative_to(REPO_ROOT).as_posix())
            continue
        path.write_text(_toml_text(package), encoding="utf-8")
    if check:
        if not stale_paths:
            print("public API snapshots are up to date")
            return 0
        print("public API snapshots are stale:")
        for stale_path in stale_paths:
            print(f" - {stale_path}")
        return 1
    print("generated public API snapshots")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate canonical package root API snapshots."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if any root API snapshot is stale.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
