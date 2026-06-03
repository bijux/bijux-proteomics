from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re
import tomllib
from typing import Any, cast

from bijux_proteomics_dev.governance.foundation.repository_product_shape import (
    build_repository_product_shape_report,
)
from bijux_proteomics_dev.governance.package_shape.package_module_ledger import (
    build_package_module_ledger_report,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_import_inventory import (
    module_dependency_edges,
    workspace_dependency_edges_for_path,
)
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    package_root,
    package_test_modules,
    root_api_policy_path,
    source_modules,
    tests_root,
    workspace_package_names,
)
from bijux_proteomics_foundation.testing.generated_file_markers import (
    GeneratedFileMarkerKind,
    detect_generated_file_marker,
)

__all__ = [
    "INTERNAL_ORPHAN_MODULE_ALLOWLIST_PATH",
    "INTERNAL_ORPHAN_MODULE_REPORT_PATH",
    "InternalOrphanModuleEntry",
    "InternalOrphanModuleJustification",
    "InternalOrphanModulePolicy",
    "InternalOrphanModuleReport",
    "build_internal_orphan_module_report",
    "load_internal_orphan_module_policy",
    "run",
    "validate_internal_orphan_module_report",
]


INTERNAL_ORPHAN_MODULE_ALLOWLIST_PATH = (
    REPO_ROOT
    / "configs"
    / "package-governance"
    / "internal-orphan-module-allowlist.toml"
)
INTERNAL_ORPHAN_MODULE_REPORT_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "internal-orphan-modules.toml"
)
ENTRYPOINT_MODULE_PATTERN = re.compile(r"-m\s+(?P<module>[A-Za-z0-9_\.]+)")


@dataclass(frozen=True)
class InternalOrphanModuleJustification:
    """One explicitly allowed orphan module."""

    distribution_name: str
    module_path: str
    module_import_path: str
    reason: str


@dataclass(frozen=True)
class InternalOrphanModulePolicy:
    """Manual justifications for intentionally orphan internal modules."""

    justifications: tuple[InternalOrphanModuleJustification, ...]


@dataclass(frozen=True)
class InternalOrphanModuleEntry:
    """One internal module that is not reachable from governed live entrypoints."""

    distribution_name: str
    module_path: str
    module_import_path: str
    module_kind: str
    justification_reason: str | None


@dataclass(frozen=True)
class InternalOrphanModuleReport:
    """Structured report over orphan internal modules across the workspace."""

    entries: tuple[InternalOrphanModuleEntry, ...]
    unexpected_entries: tuple[InternalOrphanModuleEntry, ...]
    stale_justifications: tuple[InternalOrphanModuleJustification, ...]


def load_internal_orphan_module_policy(
    path: Path = INTERNAL_ORPHAN_MODULE_ALLOWLIST_PATH,
) -> InternalOrphanModulePolicy:
    """Load the manual orphan-module justification manifest."""

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    tables = cast(list[dict[str, Any]], data.get("justification", []))
    return InternalOrphanModulePolicy(
        justifications=tuple(
            InternalOrphanModuleJustification(
                distribution_name=str(table["distribution_name"]),
                module_path=str(table["module_path"]),
                module_import_path=str(table["module_import_path"]),
                reason=str(table["reason"]),
            )
            for table in tables
        )
    )


def build_internal_orphan_module_report(
    policy: InternalOrphanModulePolicy | None = None,
) -> InternalOrphanModuleReport:
    """Return the live orphan-module report across internal owner modules."""

    policy = policy or load_internal_orphan_module_policy()
    justification_by_key = {
        (item.distribution_name, item.module_path): item
        for item in policy.justifications
    }
    entries: list[InternalOrphanModuleEntry] = []
    seen_orphans: set[tuple[str, str]] = set()
    ledger_entries = build_package_module_ledger_report().entries
    for package_name in _audited_package_names():
        reachable_modules = _reachable_modules(package_name)
        for ledger_entry in ledger_entries:
            if ledger_entry.distribution_name != package_name:
                continue
            if ledger_entry.module_kind != "owner_logic":
                continue
            if ledger_entry.module_import_path in reachable_modules:
                continue
            key = (ledger_entry.distribution_name, ledger_entry.module_path)
            seen_orphans.add(key)
            justification = justification_by_key.get(key)
            entries.append(
                InternalOrphanModuleEntry(
                    distribution_name=ledger_entry.distribution_name,
                    module_path=ledger_entry.module_path,
                    module_import_path=ledger_entry.module_import_path,
                    module_kind=ledger_entry.module_kind,
                    justification_reason=(
                        None if justification is None else justification.reason
                    ),
                )
            )

    stale_justifications = tuple(
        item
        for item in policy.justifications
        if (item.distribution_name, item.module_path) not in seen_orphans
    )
    ordered_entries = tuple(
        sorted(
            entries,
            key=lambda entry: (entry.distribution_name, entry.module_path),
        )
    )
    unexpected_entries = tuple(
        entry for entry in ordered_entries if entry.justification_reason is None
    )
    return InternalOrphanModuleReport(
        entries=ordered_entries,
        unexpected_entries=unexpected_entries,
        stale_justifications=stale_justifications,
    )


def validate_internal_orphan_module_report(
    report: InternalOrphanModuleReport | None = None,
) -> tuple[str, ...]:
    """Validate that orphan modules are either absent or explicitly justified."""

    report = report or build_internal_orphan_module_report()
    failures: list[str] = []
    for entry in report.unexpected_entries:
        failures.append(
            f"{entry.module_path} is not reachable from public API, workflow, test, "
            "or governed entrypoint seeds and is missing an explicit justification"
        )
    for item in report.stale_justifications:
        failures.append(
            f"{item.module_path} is no longer orphaned and should be removed from "
            "internal-orphan-module-allowlist.toml"
        )
    return tuple(failures)


def _reachable_modules(package_name: str) -> set[str]:
    existing_modules = {
        entry.module_import_path
        for entry in build_package_module_ledger_report().entries
        if entry.distribution_name == package_name
        and not entry.module_path.endswith("/__pycache__")
        and entry.module_path.endswith(".py")
    }
    adjacency: dict[str, set[str]] = {
        module_name: set() for module_name in existing_modules
    }
    for edge in module_dependency_edges(package_name):
        if not edge.internal:
            continue
        if edge.source_module not in existing_modules:
            continue
        target_module = _nearest_existing_module(edge.target_module, existing_modules)
        if target_module is not None:
            adjacency[edge.source_module].add(target_module)

    seeds = _seed_modules(package_name, existing_modules)
    queue = deque(sorted(seeds))
    reachable: set[str] = set()
    while queue:
        module_name = queue.popleft()
        if module_name in reachable:
            continue
        reachable.add(module_name)
        for dependency in sorted(adjacency.get(module_name, ())):
            if dependency not in reachable:
                queue.append(dependency)
    return _expand_parent_packages(reachable, existing_modules)


def _seed_modules(package_name: str, existing_modules: set[str]) -> set[str]:
    seeds: set[str] = set()
    seeds.update(_root_api_owner_modules(package_name, existing_modules))
    seeds.update(_workflow_modules(package_name, existing_modules))
    seeds.update(_test_imported_modules(package_name, existing_modules))
    seeds.update(_workspace_consumer_modules(package_name, existing_modules))
    seeds.update(_operational_entrypoint_modules(existing_modules))
    return _expand_parent_packages(seeds, existing_modules)


def _root_api_owner_modules(
    package_name: str,
    existing_modules: set[str],
) -> set[str]:
    path = root_api_policy_path(package_name)
    if path is None:
        return set()
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    modules = {
        str(symbol["owner_module"])
        for symbol in cast(list[dict[str, Any]], data.get("symbol", []))
    }
    return {module for module in modules if module in existing_modules}


def _workflow_modules(
    package_name: str,
    existing_modules: set[str],
) -> set[str]:
    workflow_modules: set[str] = set()
    root = package_root(package_name) / "src"
    for module_path in source_modules(package_name):
        relative = module_path.relative_to(root).as_posix()
        if "/workflow/" in relative or "/workflows/" in relative:
            module_name = _ledger_module_name(package_name, module_path)
            if module_name in existing_modules:
                workflow_modules.add(module_name)
    return workflow_modules


def _test_imported_modules(
    package_name: str,
    existing_modules: set[str],
) -> set[str]:
    modules: set[str] = set()
    for path in package_test_modules(package_name):
        source_module_name = _test_module_name(package_name, path)
        for edge in workspace_dependency_edges_for_path(
            package_name,
            path,
            source_module_name=source_module_name,
        ):
            if not edge.internal:
                continue
            target_module = _nearest_existing_module(
                edge.target_module, existing_modules
            )
            if target_module is not None:
                modules.add(target_module)
    return modules


def _workspace_consumer_modules(
    package_name: str,
    existing_modules: set[str],
) -> set[str]:
    modules: set[str] = set()
    for module_name in _workspace_consumer_targets().get(package_name, ()):
        target_module = _nearest_existing_module(module_name, existing_modules)
        if target_module is not None:
            modules.add(target_module)
    return modules


@lru_cache(maxsize=1)
def _workspace_consumer_targets() -> dict[str, tuple[str, ...]]:
    targets_by_distribution: dict[str, set[str]] = {}
    for consumer_package_name in workspace_package_names():
        for path in source_modules(consumer_package_name):
            for edge in workspace_dependency_edges_for_path(
                consumer_package_name, path
            ):
                targets_by_distribution.setdefault(edge.target_distribution, set()).add(
                    edge.target_module
                )
        for path in package_test_modules(consumer_package_name):
            source_module_name = _test_module_name(consumer_package_name, path)
            for edge in workspace_dependency_edges_for_path(
                consumer_package_name,
                path,
                source_module_name=source_module_name,
            ):
                targets_by_distribution.setdefault(edge.target_distribution, set()).add(
                    edge.target_module
                )
    return {
        distribution_name: tuple(sorted(module_names))
        for distribution_name, module_names in targets_by_distribution.items()
    }


def _operational_entrypoint_modules(existing_modules: set[str]) -> set[str]:
    modules: set[str] = set()
    for package_name in workspace_package_names():
        for path in source_modules(package_name):
            if path.name != "__main__.py":
                continue
            module_name = _ledger_module_name(package_name, path)
            target_module = _nearest_existing_module(module_name, existing_modules)
            if target_module is not None:
                modules.add(target_module)
    for path in _entrypoint_source_paths():
        text = path.read_text(encoding="utf-8")
        for match in ENTRYPOINT_MODULE_PATTERN.finditer(text):
            module_name = match.group("module")
            target_module = _nearest_existing_module(module_name, existing_modules)
            if target_module is not None:
                modules.add(target_module)
    for module_name in _project_script_modules():
        target_module = _nearest_existing_module(module_name, existing_modules)
        if target_module is not None:
            modules.add(target_module)
    return modules


def _entrypoint_source_paths() -> tuple[Path, ...]:
    paths: list[Path] = [REPO_ROOT / "makes" / "root.mk"]
    paths.extend(sorted((REPO_ROOT / "makes").rglob("*.mk")))
    docs_root = REPO_ROOT / "docs"
    if docs_root.exists():
        paths.extend(sorted(docs_root.rglob("*.md")))
    packages_root = REPO_ROOT / "packages"
    if packages_root.exists():
        paths.extend(sorted(packages_root.rglob("rebuild_instructions.md")))
        paths.extend(sorted(packages_root.rglob("generated_boundary.json")))
    for path in sorted((REPO_ROOT / "configs" / "package-governance").rglob("*.toml")):
        marker = detect_generated_file_marker(path)
        if (
            marker is not None
            and marker.kind == GeneratedFileMarkerKind.GENERATED_HEADER
        ):
            paths.append(path)
    return tuple(dict.fromkeys(paths))


def _project_script_modules() -> tuple[str, ...]:
    modules: list[str] = []
    for package_name in workspace_package_names():
        pyproject_path = package_root(package_name) / "pyproject.toml"
        if not pyproject_path.exists():
            continue
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        project = cast(dict[str, Any], data.get("project", {}))
        scripts = cast(dict[str, str], project.get("scripts", {}))
        for target in scripts.values():
            modules.append(str(target).split(":", 1)[0])
    return tuple(sorted(set(modules)))


def _audited_package_names() -> tuple[str, ...]:
    report = build_repository_product_shape_report()
    return tuple(
        package.distribution_name
        for package in report.packages
        if package.role_kind in {"maintainer", "product"}
    )


def _nearest_existing_module(
    module_name: str,
    existing_modules: set[str],
) -> str | None:
    candidate = module_name
    while candidate:
        if candidate in existing_modules:
            return candidate
        if "." not in candidate:
            break
        candidate = candidate.rsplit(".", 1)[0]
    return None


def _expand_parent_packages(
    module_names: set[str],
    existing_modules: set[str],
) -> set[str]:
    expanded = set(module_names)
    for module_name in tuple(module_names):
        candidate = module_name
        while "." in candidate:
            candidate = candidate.rsplit(".", 1)[0]
            if candidate in existing_modules:
                expanded.add(candidate)
    return expanded


def _ledger_module_name(package_name: str, path: Path) -> str:
    relative = path.relative_to(package_root(package_name) / "src").with_suffix("")
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _test_module_name(package_name: str, path: Path) -> str:
    relative = path.relative_to(tests_root(package_name)).with_suffix("")
    return ".".join(("tests", package_name.replace("-", "_"), *relative.parts))


def _render_toml(report: InternalOrphanModuleReport) -> str:
    lines = [
        "# Generated internal orphan-module report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.internal_orphan_modules",
        "",
        "[summary]",
        f"orphan_module_count = {len(report.entries)}",
        f"unexpected_orphan_module_count = {len(report.unexpected_entries)}",
        f"stale_justification_count = {len(report.stale_justifications)}",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[orphan_module]]",
                f'distribution_name = "{entry.distribution_name}"',
                f'module_path = "{entry.module_path}"',
                f'module_import_path = "{entry.module_import_path}"',
                f'module_kind = "{entry.module_kind}"',
            ]
        )
        if entry.justification_reason is not None:
            lines.append(
                f'justification_reason = "{_escape(entry.justification_reason)}"'
            )
        lines.append("")
    for item in report.stale_justifications:
        lines.extend(
            [
                "[[stale_justification]]",
                f'distribution_name = "{item.distribution_name}"',
                f'module_path = "{item.module_path}"',
                f'module_import_path = "{item.module_import_path}"',
                f'reason = "{_escape(item.reason)}"',
                "",
            ]
        )
    return "\n".join(lines)


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def run(*, check: bool = False) -> int:
    """Generate or validate the orphan-module report."""

    report = build_internal_orphan_module_report()
    failures = validate_internal_orphan_module_report(report)
    rendered = _render_toml(report)
    if check:
        if failures:
            for failure in failures:
                print(failure)
            return 1
        if not INTERNAL_ORPHAN_MODULE_REPORT_PATH.exists():
            print("internal orphan-module report is missing")
            return 1
        if INTERNAL_ORPHAN_MODULE_REPORT_PATH.read_text(encoding="utf-8") != rendered:
            print("internal orphan-module report is stale; regenerate it")
            return 1
        print("internal orphan-module report is up to date")
        return 0
    INTERNAL_ORPHAN_MODULE_REPORT_PATH.write_text(rendered, encoding="utf-8")
    print("generated internal orphan-module report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the internal orphan-module report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the internal orphan-module report is stale or unjustified.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
