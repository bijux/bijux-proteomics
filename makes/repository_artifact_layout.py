#!/usr/bin/env python3
"""Prepare canonical artifact directories and remove legacy alias spillover."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT_ARTIFACT_DIRECTORIES = (
    Path("artifacts/root"),
    Path("artifacts/root/check-venv"),
    Path("artifacts/root/tox"),
    Path("artifacts/root/hypothesis"),
    Path("artifacts/root/benchmarks"),
)
PACKAGE_ARTIFACT_DIRECTORY_TEMPLATES = (
    Path("artifacts/{package}"),
    Path("artifacts/{package}/venv"),
    Path("artifacts/{package}/hypothesis"),
    Path("artifacts/{package}/benchmarks"),
)
ROOT_SPILLOVER_PATHS = (".tox", ".hypothesis", ".benchmarks")
PACKAGE_SPILLOVER_PATHS = ("artifacts", ".venv", ".hypothesis", ".benchmarks")


def _prepare_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _remove_spillover_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    if path.is_dir():
        shutil.rmtree(path)


def _prepare_root_artifacts(*, repo_root: Path) -> None:
    for relative_path in ROOT_ARTIFACT_DIRECTORIES:
        _prepare_directory(repo_root / relative_path)
    for relative_path in ROOT_SPILLOVER_PATHS:
        _remove_spillover_path(repo_root / relative_path)


def _prepare_package_artifacts(*, repo_root: Path, package_dir: Path) -> None:
    for spillover_name in PACKAGE_SPILLOVER_PATHS:
        _remove_spillover_path(package_dir / spillover_name)

    package_name = package_dir.name
    for template in PACKAGE_ARTIFACT_DIRECTORY_TEMPLATES:
        relative_path = Path(str(template).format(package=package_name))
        _prepare_directory(repo_root / relative_path)


def _discover_package_dirs(*, packages_dir: Path) -> list[Path]:
    if not packages_dir.is_dir():
        return []
    return sorted(
        child
        for child in packages_dir.iterdir()
        if child.is_dir() and (child / "pyproject.toml").is_file()
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare repository-owned artifact directories."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    root_parser = subparsers.add_parser(
        "root",
        help="prepare root artifacts and clean package-root spillover",
    )
    root_parser.add_argument("--repo-root", required=True, type=Path)
    root_parser.add_argument("--packages-dir", type=Path)

    package_parser = subparsers.add_parser(
        "package",
        help="prepare one package artifact tree and clean package-root spillover",
    )
    package_parser.add_argument("--repo-root", required=True, type=Path)
    package_parser.add_argument("--package-dir", required=True, type=Path)

    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repo_root = args.repo_root.resolve()

    if args.command == "root":
        packages_dir = (
            args.packages_dir.resolve()
            if args.packages_dir is not None
            else repo_root / "packages"
        )
        _prepare_root_artifacts(repo_root=repo_root)
        for package_dir in _discover_package_dirs(packages_dir=packages_dir):
            _prepare_package_artifacts(repo_root=repo_root, package_dir=package_dir)
        return 0

    if args.command == "package":
        _prepare_package_artifacts(
            repo_root=repo_root,
            package_dir=args.package_dir.resolve(),
        )
        return 0

    raise AssertionError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
