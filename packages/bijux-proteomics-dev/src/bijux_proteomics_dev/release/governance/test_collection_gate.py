from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import sys

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    import_root,
    tests_root,
    workspace_package_names,
    workspace_src_parents,
)
from bijux_proteomics_dev.security.trusted_process import run_text

__all__ = [
    "CollectionGateCheck",
    "CollectionGateReport",
    "build_test_collection_gate_report",
    "run",
]


@dataclass(frozen=True)
class CollectionGateCheck:
    """One import or collection subprocess result in the release gate."""

    check_kind: str
    package_name: str
    target: str
    command: tuple[str, ...]
    ok: bool
    detail: str


@dataclass(frozen=True)
class CollectionGateReport:
    """Workspace-wide import and collection gate report."""

    import_checks: tuple[CollectionGateCheck, ...]
    collection_checks: tuple[CollectionGateCheck, ...]

    @property
    def failed_checks(self) -> tuple[CollectionGateCheck, ...]:
        return tuple(
            check
            for check in (*self.import_checks, *self.collection_checks)
            if not check.ok
        )


def _workspace_pythonpath() -> str:
    return os.pathsep.join(str(path) for path in workspace_src_parents())


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    workspace_pythonpath = _workspace_pythonpath()
    env["PYTHONPATH"] = (
        f"{workspace_pythonpath}{os.pathsep}{existing_pythonpath}"
        if existing_pythonpath
        else workspace_pythonpath
    )
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    return env


def _run_subprocess(
    command: tuple[str, ...],
    *,
    cwd: Path,
) -> tuple[bool, str]:
    completed = run_text(
        command,
        cwd=cwd,
        env=_subprocess_env(),
        capture_output=True,
        check=False,
    )
    output = completed.stdout.strip()
    error_output = completed.stderr.strip()
    detail = (
        output or error_output or f"command exited with status {completed.returncode}"
    )
    return completed.returncode == 0, detail


def _import_check(
    *,
    package_name: str,
    python_executable: str,
    repo_root: Path,
) -> CollectionGateCheck:
    module_name = import_root(package_name)
    command = (
        python_executable,
        "-c",
        f"import {module_name}",
    )
    ok, detail = _run_subprocess(command, cwd=repo_root)
    return CollectionGateCheck(
        check_kind="import",
        package_name=package_name,
        target=module_name,
        command=command,
        ok=ok,
        detail=detail,
    )


def _collection_check(
    *,
    package_name: str,
    python_executable: str,
    repo_root: Path,
) -> CollectionGateCheck:
    test_root = tests_root(package_name)
    relative_test_root = test_root.relative_to(repo_root).as_posix()
    command = (
        python_executable,
        "-m",
        "pytest",
        relative_test_root,
        "--collect-only",
        "-q",
        "-p",
        "no:cov",
        "-c",
        "configs/pytest.ini",
    )
    ok, detail = _run_subprocess(command, cwd=repo_root)
    return CollectionGateCheck(
        check_kind="collection",
        package_name=package_name,
        target=relative_test_root,
        command=command,
        ok=ok,
        detail=detail,
    )


def _workspace_collection_check(
    *,
    python_executable: str,
    repo_root: Path,
) -> CollectionGateCheck:
    command = (
        python_executable,
        "-m",
        "pytest",
        "--collect-only",
        "packages",
        "-q",
    )
    ok, detail = _run_subprocess(command, cwd=repo_root)
    return CollectionGateCheck(
        check_kind="collection",
        package_name="workspace",
        target="packages",
        command=command,
        ok=ok,
        detail=detail,
    )


def build_test_collection_gate_report(
    repo_root: Path = REPO_ROOT,
    *,
    python_executable: str | None = None,
) -> CollectionGateReport:
    """Run package import checks and per-package pytest collection checks."""

    executable = python_executable or sys.executable
    package_names = tuple(
        package_name
        for package_name in workspace_package_names()
        if tests_root(package_name).is_dir()
    )
    import_checks = tuple(
        _import_check(
            package_name=package_name,
            python_executable=executable,
            repo_root=repo_root,
        )
        for package_name in package_names
    )
    collection_checks = (
        _workspace_collection_check(
            python_executable=executable,
            repo_root=repo_root,
        ),
        *(
            _collection_check(
                package_name=package_name,
                python_executable=executable,
                repo_root=repo_root,
            )
            for package_name in package_names
        ),
    )
    return CollectionGateReport(
        import_checks=import_checks,
        collection_checks=collection_checks,
    )


def run(
    repo_root: Path = REPO_ROOT,
    *,
    python_executable: str | None = None,
) -> int:
    """Execute the release-facing test collection gate."""

    report = build_test_collection_gate_report(
        repo_root=repo_root,
        python_executable=python_executable,
    )
    failures = report.failed_checks
    if not failures:
        print("test collection gate passed")
        return 0
    print("test collection gate failed")
    for failure in failures:
        print(
            f"[{failure.check_kind}] {failure.package_name} -> {failure.target}: "
            f"{failure.detail}"
        )
    return 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run workspace import checks and per-package pytest collection before feature tests."
    )
    parser.add_argument(
        "--python-executable",
        default=None,
        help="Python executable to use for import and collection subprocesses.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    return run(python_executable=args.python_executable)


if __name__ == "__main__":
    raise SystemExit(main())
