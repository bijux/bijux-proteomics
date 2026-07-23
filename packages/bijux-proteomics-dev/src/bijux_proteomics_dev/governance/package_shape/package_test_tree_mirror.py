from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    flat_test_modules,
    source_owner_families,
    test_families,
    workspace_package_names,
)

__all__ = [
    "PACKAGE_TEST_TREE_MIRROR_PATH",
    "PackageTestTreeMirrorEntry",
    "PackageTestTreeMirrorGuard",
    "PackageTestTreeMirrorReport",
    "build_package_test_tree_mirror_report",
    "run",
    "validate_package_test_tree_mirror",
]


PACKAGE_TEST_TREE_MIRROR_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-test-tree-mirror.toml"
)


@dataclass(frozen=True)
class PackageTestTreeMirrorEntry:
    """How closely one package's tests mirror its source owner families."""

    distribution_name: str
    source_owner_families: tuple[str, ...]
    test_families: tuple[str, ...]
    mirrored_owner_families: tuple[str, ...]
    missing_test_families: tuple[str, ...]
    extra_test_families: tuple[str, ...]
    flat_test_module_count: int


@dataclass(frozen=True)
class PackageTestTreeMirrorGuard:
    """Release-blocking guardrails over test-tree drift."""

    min_total_mirrored_owner_family_count: int
    max_total_missing_test_family_count: int
    max_total_flat_test_module_count: int


@dataclass(frozen=True)
class PackageTestTreeMirrorReport:
    """Checked test-tree mirror report across repository packages."""

    entries: tuple[PackageTestTreeMirrorEntry, ...]
    guard: PackageTestTreeMirrorGuard


def build_package_test_tree_mirror_report() -> PackageTestTreeMirrorReport:
    """Build the checked test-tree mirror report."""

    entries: list[PackageTestTreeMirrorEntry] = []
    for package_name in workspace_package_names():
        owners = source_owner_families(package_name)
        tests = test_families(package_name)
        mirrored = tuple(sorted(set(owners) & set(tests)))
        missing = tuple(sorted(set(owners) - set(tests)))
        extra = tuple(sorted(set(tests) - set(owners)))
        entries.append(
            PackageTestTreeMirrorEntry(
                distribution_name=package_name,
                source_owner_families=owners,
                test_families=tests,
                mirrored_owner_families=mirrored,
                missing_test_families=missing,
                extra_test_families=extra,
                flat_test_module_count=len(flat_test_modules(package_name)),
            )
        )
    return PackageTestTreeMirrorReport(
        entries=tuple(entries),
        guard=PackageTestTreeMirrorGuard(
            min_total_mirrored_owner_family_count=sum(
                len(entry.mirrored_owner_families) for entry in entries
            ),
            max_total_missing_test_family_count=sum(
                len(entry.missing_test_families) for entry in entries
            ),
            max_total_flat_test_module_count=sum(
                entry.flat_test_module_count for entry in entries
            ),
        ),
    )


def validate_package_test_tree_mirror(
    report: PackageTestTreeMirrorReport | None = None,
) -> tuple[str, ...]:
    """Fail release when source-to-test mirroring gets worse."""

    report = report or build_package_test_tree_mirror_report()
    failures: list[str] = []
    mirrored_owner_family_count = sum(
        len(entry.mirrored_owner_families) for entry in report.entries
    )
    missing_test_family_count = sum(
        len(entry.missing_test_families) for entry in report.entries
    )
    flat_test_module_count = sum(
        entry.flat_test_module_count for entry in report.entries
    )
    if mirrored_owner_family_count < report.guard.min_total_mirrored_owner_family_count:
        failures.append(
            "test-tree mirroring dropped below the governed source alignment baseline"
        )
    if missing_test_family_count > report.guard.max_total_missing_test_family_count:
        failures.append(
            "test-tree missing-family count grew beyond the governed source alignment baseline"
        )
    if flat_test_module_count > report.guard.max_total_flat_test_module_count:
        failures.append(
            "flat root test-module count grew beyond the governed source alignment baseline"
        )
    return tuple(failures)


def _render_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(f'"{value}"' for value in values)


def _toml_text(report: PackageTestTreeMirrorReport) -> str:
    lines = [
        "# Generated package test-tree mirror report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.package_test_tree_mirror",
        "",
        "[guard]",
        (
            "min_total_mirrored_owner_family_count = "
            f"{report.guard.min_total_mirrored_owner_family_count}"
        ),
        (
            "max_total_missing_test_family_count = "
            f"{report.guard.max_total_missing_test_family_count}"
        ),
        f"max_total_flat_test_module_count = {report.guard.max_total_flat_test_module_count}",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f"source_owner_families = [{_render_tuple(entry.source_owner_families)}]",
                f"test_families = [{_render_tuple(entry.test_families)}]",
                f"mirrored_owner_families = [{_render_tuple(entry.mirrored_owner_families)}]",
                f"missing_test_families = [{_render_tuple(entry.missing_test_families)}]",
                f"extra_test_families = [{_render_tuple(entry.extra_test_families)}]",
                f"flat_test_module_count = {entry.flat_test_module_count}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageTestTreeMirrorReport) -> bool:
    if not PACKAGE_TEST_TREE_MIRROR_PATH.exists():
        return False
    return PACKAGE_TEST_TREE_MIRROR_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_package_test_tree_mirror_report()
    failures = validate_package_test_tree_mirror(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package test-tree mirror report is up to date")
            return 0
        print("package test-tree mirror report is stale; regenerate it")
        return 1
    PACKAGE_TEST_TREE_MIRROR_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package test-tree mirror report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package test-tree mirror report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the package test-tree mirror report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
