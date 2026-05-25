from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    test_modules,
    tests_root,
    workspace_package_names,
)

__all__ = [
    "DuplicateTestModuleFamily",
    "build_duplicate_test_module_families",
    "validate_duplicate_test_module_namespaces",
]


@dataclass(frozen=True)
class DuplicateTestModuleFamily:
    """One duplicated `test_*.py` basename across the workspace."""

    basename: str
    paths: tuple[Path, ...]
    package_names: tuple[str, ...]

    @property
    def package_counts(self) -> tuple[tuple[str, int], ...]:
        counts = Counter(self.package_names)
        return tuple(sorted(counts.items()))

    @property
    def namespace_reason(self) -> str | None:
        counts = Counter(self.package_names)
        repeated_packages = [
            package_name
            for package_name, count in counts.items()
            if count > 1 and not (tests_root(package_name) / "__init__.py").exists()
        ]
        if repeated_packages:
            return None
        if any(count > 1 for count in counts.values()):
            return "packaged-test-root"
        return "distinct-workspace-packages"


def build_duplicate_test_module_families(
    repo_root: Path = REPO_ROOT,
) -> tuple[DuplicateTestModuleFamily, ...]:
    grouped_paths: dict[str, list[Path]] = defaultdict(list)
    grouped_packages: dict[str, list[str]] = defaultdict(list)

    for package_name in workspace_package_names():
        package_tests_root = tests_root(package_name)
        if not package_tests_root.is_dir():
            continue
        for path in test_modules(package_name):
            if repo_root not in path.parents:
                continue
            grouped_paths[path.name].append(path)
            grouped_packages[path.name].append(package_name)

    families: list[DuplicateTestModuleFamily] = []
    for basename, paths in sorted(grouped_paths.items()):
        if len(paths) < 2:
            continue
        families.append(
            DuplicateTestModuleFamily(
                basename=basename,
                paths=tuple(sorted(paths)),
                package_names=tuple(grouped_packages[basename]),
            )
        )
    return tuple(families)


def validate_duplicate_test_module_namespaces(
    repo_root: Path = REPO_ROOT,
) -> tuple[str, ...]:
    issues: list[str] = []
    for family in build_duplicate_test_module_families(repo_root):
        if family.namespace_reason is not None:
            continue
        counts = Counter(family.package_names)
        repeated_packages = sorted(
            package_name for package_name, count in counts.items() if count > 1
        )
        issue_paths = ", ".join(
            path.relative_to(repo_root).as_posix() for path in family.paths
        )
        issues.append(
            f"{family.basename} repeats inside unpackaged test roots for "
            f"{', '.join(repeated_packages)}: {issue_paths}"
        )
    return tuple(issues)
