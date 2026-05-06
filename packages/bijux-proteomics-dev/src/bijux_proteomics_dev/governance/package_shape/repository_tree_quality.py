from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
import tomllib
from typing import Any, cast

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT

__all__ = [
    "REPOSITORY_TREE_QUALITY_PATH",
    "RepositoryTreeQualityGuard",
    "RepositoryTreeQualityPackageMetrics",
    "RepositoryTreeQualityReport",
    "build_repository_tree_quality_report",
    "run",
    "validate_repository_tree_quality",
]


REPOSITORY_TREE_QUALITY_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "repository-tree-quality.toml"
)


@dataclass(frozen=True)
class RepositoryTreeQualityPackageMetrics:
    """Tree-quality metrics for one repository package."""

    distribution_name: str
    import_root: str
    root_python_module_count: int
    public_symbol_count: int
    compatibility_wrapper_count: int
    broad_root_import_count: int
    source_owner_family_count: int
    test_family_count: int
    mirrored_owner_family_count: int
    flatness_score: float
    root_bloat_score: float
    wrapper_density_score: float
    broad_root_import_score: float
    test_tree_mirroring_score: float
    overall_tree_quality_score: float


@dataclass(frozen=True)
class RepositoryTreeQualityGuard:
    """Release guardrails for repository tree quality drift."""

    max_total_root_python_module_count: int
    max_total_wrapper_module_count: int
    max_total_broad_root_import_count: int
    min_average_test_tree_mirroring_score: float


@dataclass(frozen=True)
class RepositoryTreeQualityReport:
    """Checked tree-quality report across every repository package."""

    packages: tuple[RepositoryTreeQualityPackageMetrics, ...]
    guard: RepositoryTreeQualityGuard


def _workspace_metadata() -> dict[str, Any]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    return cast(dict[str, Any], data["tool"]["bijux_proteomics"])


def _package_names() -> tuple[str, ...]:
    workspace = _workspace_metadata()
    return tuple(cast(list[str], workspace["packages"]))


def _import_root(package_name: str) -> str:
    if package_name == "bijux-proteomics-core":
        return "bijux_proteomics"
    return package_name.replace("-", "_")


def _package_root(package_name: str) -> Path:
    return REPO_ROOT / "packages" / package_name


def _src_root(package_name: str) -> Path:
    return _package_root(package_name) / "src" / _import_root(package_name)


def _tests_root(package_name: str) -> Path:
    return _package_root(package_name) / "tests"


def _root_python_modules(src_root: Path) -> tuple[Path, ...]:
    return tuple(
        sorted(
            path
            for path in src_root.glob("*.py")
            if path.name not in {"__init__.py", "charter.py"}
        )
    )


def _is_compatibility_wrapper(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    public_defs = any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and not node.name.startswith("_")
        for node in tree.body
    )
    if public_defs:
        return False
    allowed = (ast.Import, ast.ImportFrom, ast.Assign, ast.Expr, ast.Pass)
    return all(isinstance(node, allowed) for node in tree.body)


def _public_symbol_count(src_root: Path) -> int:
    init_path = src_root / "__init__.py"
    tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    return len(node.value.elts)
    return 0


def _broad_root_import_count(src_root: Path, import_root: str) -> int:
    violations = 0
    for path in sorted(src_root.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == import_root:
                        violations += 1
            if isinstance(node, ast.ImportFrom) and node.module == import_root:
                violations += 1
    return violations


def _owner_families(src_root: Path) -> tuple[str, ...]:
    return tuple(
        sorted(path.name for path in src_root.iterdir() if path.is_dir() and path.name != "__pycache__")
    )


def _test_families(tests_root: Path) -> tuple[str, ...]:
    if not tests_root.exists():
        return ()
    return tuple(
        sorted(
            path.name
            for path in tests_root.iterdir()
            if path.is_dir() and path.name not in {"__pycache__", "fixtures"}
        )
    )


def _score_from_upper_bound(value: int, penalty: int) -> float:
    return round(max(0.0, 100.0 - (value * penalty)), 2)


def _package_metrics(package_name: str) -> RepositoryTreeQualityPackageMetrics:
    src_root = _src_root(package_name)
    tests_root = _tests_root(package_name)
    import_root = _import_root(package_name)
    root_modules = _root_python_modules(src_root)
    source_owner_families = _owner_families(src_root)
    test_families = _test_families(tests_root)
    mirrored_owner_family_count = sum(
        1 for family in source_owner_families if family in set(test_families)
    )
    root_python_module_count = len(root_modules)
    public_symbol_count = _public_symbol_count(src_root)
    compatibility_wrapper_count = sum(1 for path in root_modules if _is_compatibility_wrapper(path))
    broad_root_import_count = _broad_root_import_count(src_root, import_root)

    flatness_score = _score_from_upper_bound(root_python_module_count, penalty=10)
    root_bloat_score = round(
        max(0.0, 100.0 - (max(0, public_symbol_count - 4) * 8)),
        2,
    )
    wrapper_density_score = round(
        100.0
        if root_python_module_count == 0
        else max(
            0.0,
            100.0 - ((compatibility_wrapper_count / root_python_module_count) * 100.0),
        ),
        2,
    )
    broad_root_import_score = _score_from_upper_bound(broad_root_import_count, penalty=20)
    test_tree_mirroring_score = round(
        100.0
        if not source_owner_families
        else (mirrored_owner_family_count / len(source_owner_families)) * 100.0,
        2,
    )
    overall_tree_quality_score = round(
        (
            flatness_score
            + root_bloat_score
            + wrapper_density_score
            + broad_root_import_score
            + test_tree_mirroring_score
        )
        / 5.0,
        2,
    )

    return RepositoryTreeQualityPackageMetrics(
        distribution_name=package_name,
        import_root=import_root,
        root_python_module_count=root_python_module_count,
        public_symbol_count=public_symbol_count,
        compatibility_wrapper_count=compatibility_wrapper_count,
        broad_root_import_count=broad_root_import_count,
        source_owner_family_count=len(source_owner_families),
        test_family_count=len(test_families),
        mirrored_owner_family_count=mirrored_owner_family_count,
        flatness_score=flatness_score,
        root_bloat_score=root_bloat_score,
        wrapper_density_score=wrapper_density_score,
        broad_root_import_score=broad_root_import_score,
        test_tree_mirroring_score=test_tree_mirroring_score,
        overall_tree_quality_score=overall_tree_quality_score,
    )


def build_repository_tree_quality_report() -> RepositoryTreeQualityReport:
    """Build the checked tree-quality report across repository packages."""

    packages = tuple(_package_metrics(package_name) for package_name in _package_names())
    average_test_tree_mirroring_score = round(
        sum(package.test_tree_mirroring_score for package in packages) / len(packages), 2
    )
    return RepositoryTreeQualityReport(
        packages=packages,
        guard=RepositoryTreeQualityGuard(
            max_total_root_python_module_count=sum(
                package.root_python_module_count for package in packages
            ),
            max_total_wrapper_module_count=sum(
                package.compatibility_wrapper_count for package in packages
            ),
            max_total_broad_root_import_count=sum(
                package.broad_root_import_count for package in packages
            ),
            min_average_test_tree_mirroring_score=average_test_tree_mirroring_score,
        ),
    )


def validate_repository_tree_quality(
    report: RepositoryTreeQualityReport | None = None,
) -> tuple[str, ...]:
    """Fail release when repository tree quality worsens across packages."""

    report = report or build_repository_tree_quality_report()
    total_root_python_module_count = sum(
        package.root_python_module_count for package in report.packages
    )
    total_wrapper_module_count = sum(
        package.compatibility_wrapper_count for package in report.packages
    )
    total_broad_root_import_count = sum(
        package.broad_root_import_count for package in report.packages
    )
    average_test_tree_mirroring_score = round(
        sum(package.test_tree_mirroring_score for package in report.packages)
        / len(report.packages),
        2,
    )

    failures: list[str] = []
    if total_root_python_module_count > report.guard.max_total_root_python_module_count:
        failures.append("repository tree quality root-level python module count grew beyond the governed baseline")
    if total_wrapper_module_count > report.guard.max_total_wrapper_module_count:
        failures.append("repository tree quality compatibility-wrapper count grew beyond the governed baseline")
    if total_broad_root_import_count > report.guard.max_total_broad_root_import_count:
        failures.append("repository tree quality broad-root import count grew beyond the governed baseline")
    if (
        average_test_tree_mirroring_score
        < report.guard.min_average_test_tree_mirroring_score
    ):
        failures.append("repository tree quality test-tree mirroring fell below the governed baseline")
    return tuple(failures)


def _toml_text(report: RepositoryTreeQualityReport) -> str:
    lines = [
        "# Generated repository tree-quality report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.repository_tree_quality",
        "",
        "[guard]",
        (
            "max_total_root_python_module_count = "
            f"{report.guard.max_total_root_python_module_count}"
        ),
        f"max_total_wrapper_module_count = {report.guard.max_total_wrapper_module_count}",
        (
            "max_total_broad_root_import_count = "
            f"{report.guard.max_total_broad_root_import_count}"
        ),
        (
            "min_average_test_tree_mirroring_score = "
            f"{report.guard.min_average_test_tree_mirroring_score}"
        ),
        "",
    ]
    for package in report.packages:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{package.distribution_name}"',
                f'import_root = "{package.import_root}"',
                f"root_python_module_count = {package.root_python_module_count}",
                f"public_symbol_count = {package.public_symbol_count}",
                f"compatibility_wrapper_count = {package.compatibility_wrapper_count}",
                f"broad_root_import_count = {package.broad_root_import_count}",
                f"source_owner_family_count = {package.source_owner_family_count}",
                f"test_family_count = {package.test_family_count}",
                f"mirrored_owner_family_count = {package.mirrored_owner_family_count}",
                f"flatness_score = {package.flatness_score}",
                f"root_bloat_score = {package.root_bloat_score}",
                f"wrapper_density_score = {package.wrapper_density_score}",
                f"broad_root_import_score = {package.broad_root_import_score}",
                f"test_tree_mirroring_score = {package.test_tree_mirroring_score}",
                f"overall_tree_quality_score = {package.overall_tree_quality_score}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: RepositoryTreeQualityReport) -> bool:
    if not REPOSITORY_TREE_QUALITY_PATH.exists():
        return False
    return REPOSITORY_TREE_QUALITY_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_repository_tree_quality_report()
    failures = validate_repository_tree_quality(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("repository tree-quality report is up to date")
            return 0
        print("repository tree-quality report is stale; regenerate it")
        return 1
    REPOSITORY_TREE_QUALITY_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated repository tree-quality report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the repository tree-quality report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the repository tree-quality report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
