from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import tomllib
from typing import Any

__all__ = [
    "WorkspaceDependencyEdge",
    "WorkspacePackage",
    "WorkspacePackageGraph",
    "build_workspace_package_graph",
    "load_workspace_packages",
]


_DEPENDENCY_NAME_PATTERN = re.compile(r"([A-Za-z0-9_.-]+)")


@dataclass(frozen=True)
class WorkspacePackage:
    """Resolved metadata for one workspace package."""

    package_name: str
    distribution_name: str
    import_root: str
    package_dir: Path
    pyproject_path: Path
    readme_path: Path
    src_dir: Path
    tests_dir: Path
    layer_index: int
    workspace_dependencies: tuple[str, ...]
    external_dependencies: tuple[str, ...]


@dataclass(frozen=True)
class WorkspaceDependencyEdge:
    """One declared dependency edge between workspace packages."""

    depender_package: str
    dependee_package: str


@dataclass(frozen=True)
class WorkspacePackageGraph:
    """Stable view of workspace packages and their declared dependency graph."""

    packages: tuple[WorkspacePackage, ...]
    dependency_edges: tuple[WorkspaceDependencyEdge, ...]

    def package_by_name(self, package_name: str) -> WorkspacePackage:
        """Return one package by workspace package name."""
        for package in self.packages:
            if package.package_name == package_name:
                return package
        raise KeyError(f"unknown workspace package {package_name!r}")

    def direct_dependencies_of(self, package_name: str) -> tuple[str, ...]:
        """Return direct workspace dependencies for one package."""
        package = self.package_by_name(package_name)
        return package.workspace_dependencies

    def reverse_dependencies_of(self, package_name: str) -> tuple[str, ...]:
        """Return direct reverse workspace dependencies for one package."""
        dependers = [
            edge.depender_package
            for edge in self.dependency_edges
            if edge.dependee_package == package_name
        ]
        return tuple(sorted(dependers))


def _load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _workspace_package_names(repo_root: Path) -> tuple[str, ...]:
    workspace = _load_toml(repo_root / "pyproject.toml")
    raw_packages = workspace["tool"]["bijux_proteomics"]["packages"]
    return tuple(str(item) for item in raw_packages)


def _normalize_dependency_name(requirement: str) -> str:
    match = _DEPENDENCY_NAME_PATTERN.match(requirement.strip())
    return match.group(1).lower() if match else requirement.strip().lower()


def _detect_import_root(src_dir: Path) -> str:
    candidates = [
        path.name
        for path in sorted(src_dir.iterdir())
        if path.is_dir()
        and path.name != "__pycache__"
        and not path.name.endswith("_testsupport")
    ]
    if len(candidates) != 1:
        raise ValueError(
            f"expected exactly one import root under {src_dir}, found {candidates}"
        )
    return candidates[0]


def load_workspace_packages(repo_root: Path) -> tuple[WorkspacePackage, ...]:
    """Load workspace package metadata from package pyproject files."""
    package_names = _workspace_package_names(repo_root)
    distribution_by_package: dict[str, str] = {}
    dependencies_by_package: dict[str, tuple[str, ...]] = {}

    for package_name in package_names:
        pyproject_path = repo_root / "packages" / package_name / "pyproject.toml"
        project = _load_toml(pyproject_path)["project"]
        distribution_name = str(project["name"])
        distribution_by_package[package_name] = distribution_name
        dependencies_by_package[package_name] = tuple(
            _normalize_dependency_name(dependency)
            for dependency in project.get("dependencies", [])
        )

    package_name_by_distribution = {
        distribution_name.lower(): package_name
        for package_name, distribution_name in distribution_by_package.items()
    }

    packages: list[WorkspacePackage] = []
    for layer_index, package_name in enumerate(package_names):
        package_dir = repo_root / "packages" / package_name
        pyproject_path = package_dir / "pyproject.toml"
        src_dir = package_dir / "src"
        dependencies = dependencies_by_package[package_name]
        workspace_dependencies = sorted(
            {
                package_name_by_distribution[dependency]
                for dependency in dependencies
                if dependency in package_name_by_distribution
            }
        )
        external_dependencies = sorted(
            {
                dependency
                for dependency in dependencies
                if dependency not in package_name_by_distribution
            }
        )
        packages.append(
            WorkspacePackage(
                package_name=package_name,
                distribution_name=distribution_by_package[package_name],
                import_root=_detect_import_root(src_dir),
                package_dir=package_dir,
                pyproject_path=pyproject_path,
                readme_path=package_dir / "README.md",
                src_dir=src_dir,
                tests_dir=package_dir / "tests",
                layer_index=layer_index,
                workspace_dependencies=tuple(workspace_dependencies),
                external_dependencies=tuple(external_dependencies),
            )
        )
    return tuple(packages)


def build_workspace_package_graph(repo_root: Path) -> WorkspacePackageGraph:
    """Build the declared workspace dependency graph."""
    packages = load_workspace_packages(repo_root)
    edges = [
        WorkspaceDependencyEdge(
            depender_package=package.package_name,
            dependee_package=dependency,
        )
        for package in packages
        for dependency in package.workspace_dependencies
    ]
    return WorkspacePackageGraph(
        packages=packages,
        dependency_edges=tuple(
            sorted(
                edges, key=lambda edge: (edge.depender_package, edge.dependee_package)
            )
        ),
    )
