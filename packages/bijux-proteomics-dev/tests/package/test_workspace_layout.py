"""Workspace artifact alias coverage."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tomllib
from typing import Any, cast

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
ARTIFACT_ALIAS_SCRIPT = (
    REPO_ROOT
    / ".bijux"
    / "shared"
    / "bijux-makes-py"
    / "repository"
    / "artifact_aliases.py"
)
PACKAGE_ARTIFACT_LINKS = {
    "artifacts": "",
    ".venv": "venv",
    ".hypothesis": "hypothesis",
    ".benchmarks": "benchmarks",
}
ROOT_ARTIFACT_LINKS = {
    ".venv": "artifacts/root/check-venv",
    ".tox": "artifacts/root/tox",
    ".hypothesis": "artifacts/root/hypothesis",
    ".benchmarks": "artifacts/root/benchmarks",
}


def _workspace_metadata() -> dict[str, Any]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    return cast(dict[str, Any], data["tool"]["bijux_proteomics"])


def _artifact_alias_paths() -> list[str]:
    workspace = _workspace_metadata()
    package_names = sorted(cast(list[str], workspace["packages"]))
    paths = [".venv", ".tox", ".hypothesis", ".benchmarks"]
    for package_name in package_names:
        paths.extend(
            f"packages/{package_name}/{link_name}"
            for link_name in PACKAGE_ARTIFACT_LINKS
        )
    return paths


def _expected_package_target(package_name: str, link_name: str) -> str:
    suffix = PACKAGE_ARTIFACT_LINKS[link_name]
    base = Path("../..") / "artifacts" / package_name
    return str(base / suffix) if suffix else str(base)


def _assert_symlink(*, link_path: Path, expected_target: str) -> None:
    assert link_path.is_symlink()
    assert os.readlink(link_path) == expected_target


def _create_packages(packages_dir: Path) -> list[str]:
    package_names = sorted(cast(list[str], _workspace_metadata()["packages"]))
    for package_name in package_names:
        package_root = packages_dir / package_name
        package_root.mkdir()
        (package_root / "pyproject.toml").write_text(
            "[project]\nname='test'\n",
            encoding="utf-8",
        )
    return package_names


def _run_setup(
    *, repo_root: Path, packages_dir: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(ARTIFACT_ALIAS_SCRIPT),
            "root",
            "--repo-root",
            str(repo_root),
            "--packages-dir",
            str(packages_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def test_setup_materializes_governed_artifact_aliases(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    packages_dir = repo_root / "packages"
    packages_dir.mkdir(parents=True)
    package_names = _create_packages(packages_dir)

    completed = _run_setup(repo_root=repo_root, packages_dir=packages_dir)

    assert completed.returncode == 0
    assert completed.stderr == ""
    for link_name, target in ROOT_ARTIFACT_LINKS.items():
        _assert_symlink(link_path=repo_root / link_name, expected_target=target)
    for package_name in package_names:
        for link_name in PACKAGE_ARTIFACT_LINKS:
            _assert_symlink(
                link_path=packages_dir / package_name / link_name,
                expected_target=_expected_package_target(package_name, link_name),
            )


def test_setup_preserves_legacy_root_directory(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    packages_dir = repo_root / "packages"
    packages_dir.mkdir(parents=True)
    _create_packages(packages_dir)
    legacy_benchmarks = repo_root / ".benchmarks"
    legacy_benchmarks.mkdir()
    marker = legacy_benchmarks / "results.json"
    marker.write_text("{}\n", encoding="utf-8")

    completed = _run_setup(repo_root=repo_root, packages_dir=packages_dir)

    assert completed.returncode == 0
    assert completed.stderr == ""
    assert legacy_benchmarks.is_dir()
    assert not legacy_benchmarks.is_symlink()
    assert marker.read_text(encoding="utf-8") == "{}\n"


def test_artifact_alias_paths_are_ignored_by_git() -> None:
    paths = _artifact_alias_paths()
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "check-ignore", "--no-index", "--stdin"],
        input="\n".join(paths),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert set(result.stdout.splitlines()) == set(paths)


def test_artifact_alias_paths_stay_untracked_by_git() -> None:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z", "--", *_artifact_alias_paths()],
        check=True,
        capture_output=True,
    )

    assert result.stdout == b""
