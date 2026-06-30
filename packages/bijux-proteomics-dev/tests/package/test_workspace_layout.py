"""Workspace artifact layout coverage."""

from __future__ import annotations

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
ARTIFACT_LAYOUT_SCRIPT = REPO_ROOT / "makes" / "repository_artifact_layout.py"
PACKAGE_ARTIFACT_DIRECTORIES = ("", "venv", "hypothesis", "benchmarks")
ROOT_ARTIFACT_DIRECTORIES = (
    "artifacts/root",
    "artifacts/root/check-venv",
    "artifacts/root/hypothesis",
    "artifacts/root/benchmarks",
    "artifacts/root/tox",
)


def _workspace_metadata() -> dict[str, Any]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    return cast(dict[str, Any], data["tool"]["bijux_proteomics"])


def _artifact_layout_paths() -> list[str]:
    workspace = _workspace_metadata()
    package_names = sorted(cast(list[str], workspace["packages"]))
    paths = ["artifacts", ".venv", ".tox", ".hypothesis", ".benchmarks"]
    for package_name in package_names:
        paths.extend(
            [
                f"packages/{package_name}/artifacts",
                f"packages/{package_name}/.venv",
                f"packages/{package_name}/.hypothesis",
                f"packages/{package_name}/.benchmarks",
            ]
        )
    return paths


def test_setup_prepares_canonical_artifact_directories(tmp_path: Path) -> None:
    workspace = _workspace_metadata()
    repo_root = tmp_path / "repo"
    packages_dir = repo_root / "packages"
    packages_dir.mkdir(parents=True)

    for package_name in sorted(cast(list[str], workspace["packages"])):
        package_root = packages_dir / package_name
        package_root.mkdir()
        (package_root / "pyproject.toml").write_text("[project]\nname='test'\n")

    subprocess.run(
        [
            sys.executable,
            str(ARTIFACT_LAYOUT_SCRIPT),
            "root",
            "--repo-root",
            str(repo_root),
            "--packages-dir",
            str(packages_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    for relative_path in ROOT_ARTIFACT_DIRECTORIES:
        assert (repo_root / relative_path).is_dir()

    assert not (repo_root / ".tox").exists()
    assert not (repo_root / ".hypothesis").exists()
    assert not (repo_root / ".benchmarks").exists()

    for package_name in sorted(cast(list[str], workspace["packages"])):
        package_root = packages_dir / package_name
        for suffix in PACKAGE_ARTIFACT_DIRECTORIES:
            relative_path = Path("artifacts") / package_name
            if suffix:
                relative_path /= suffix
            assert (repo_root / relative_path).is_dir()
        assert not (package_root / "artifacts").exists()
        assert not (package_root / ".venv").exists()
        assert not (package_root / ".hypothesis").exists()
        assert not (package_root / ".benchmarks").exists()


def test_setup_removes_legacy_package_root_aliases(tmp_path: Path) -> None:
    workspace = _workspace_metadata()
    repo_root = tmp_path / "repo"
    packages_dir = repo_root / "packages"
    packages_dir.mkdir(parents=True)

    legacy_root_benchmarks = repo_root / ".benchmarks"
    legacy_root_benchmarks.symlink_to(Path("artifacts/root/benchmarks"))

    for package_name in sorted(cast(list[str], workspace["packages"])):
        package_root = packages_dir / package_name
        package_root.mkdir()
        (package_root / "pyproject.toml").write_text("[project]\nname='test'\n")
        (package_root / ".benchmarks").mkdir()
        (package_root / "artifacts").mkdir()

    subprocess.run(
        [
            sys.executable,
            str(ARTIFACT_LAYOUT_SCRIPT),
            "root",
            "--repo-root",
            str(repo_root),
            "--packages-dir",
            str(packages_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert not legacy_root_benchmarks.exists()
    for package_name in sorted(cast(list[str], workspace["packages"])):
        package_root = packages_dir / package_name
        assert not (package_root / "artifacts").exists()
        assert not (package_root / ".benchmarks").exists()


def test_artifact_layout_paths_are_ignored_by_git() -> None:
    paths = _artifact_layout_paths()
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "check-ignore", "--no-index", "--stdin"],
        input="\n".join(paths),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert set(result.stdout.splitlines()) == set(paths)


def test_artifact_layout_paths_stay_untracked_by_git() -> None:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z", "--", *_artifact_layout_paths()],
        check=True,
        capture_output=True,
    )

    assert result.stdout == b""
