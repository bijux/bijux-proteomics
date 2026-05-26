"""Curated architecture regression gate for post-refactor hardening checks."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess  # nosec B404
import sys

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    workspace_src_parents,
)

__all__ = [
    "ArchitectureRegressionTarget",
    "default_architecture_regression_targets",
    "run_architecture_regression_gate",
    "validate_architecture_regression_targets",
]


@dataclass(frozen=True)
class ArchitectureRegressionTarget:
    """One hardening check in the architecture regression gate."""

    surface: str
    command: tuple[str, ...]
    rationale: str
    required_paths: tuple[str, ...] = ()


def default_architecture_regression_targets() -> tuple[ArchitectureRegressionTarget, ...]:
    """Return the curated post-refactor architecture regression targets."""

    return (
        ArchitectureRegressionTarget(
            surface="imports-and-collection",
            command=(
                sys.executable,
                "-m",
                "bijux_proteomics_dev.release.governance.test_collection_gate",
            ),
            rationale="prove workspace imports and pytest collection remain intact after package-tree hardening",
        ),
        ArchitectureRegressionTarget(
            surface="public-api-snapshots",
            command=(
                sys.executable,
                "-m",
                "bijux_proteomics_dev.governance.package_shape.public_api_snapshots",
                "--check",
            ),
            rationale="prove canonical package root exports still match governed public API snapshots",
        ),
        ArchitectureRegressionTarget(
            surface="internal-architecture-map",
            command=(
                sys.executable,
                "-m",
                "bijux_proteomics_dev.governance.dependencies.internal_architecture_map",
                "--check",
            ),
            rationale="prove the generated internal architecture map still matches live package and module dependencies",
        ),
        ArchitectureRegressionTarget(
            surface="canonical-package-tree",
            command=(
                sys.executable,
                "-m",
                "bijux_proteomics_dev.governance.package_shape.package_tree_layout",
                "--check",
            ),
            rationale="prove top-level package roots and owner families still match the canonical tree contract",
        ),
        ArchitectureRegressionTarget(
            surface="runtime-output-snapshots",
            command=(
                sys.executable,
                "-m",
                "pytest",
                "packages/bijux-proteomics-runtime/tests/workflows/test_flagship_run_bundle_surface.py",
                "-q",
                "-p",
                "no:cov",
                "--import-mode=importlib",
            ),
            rationale="prove checked runtime flagship run bundle snapshots still match live builders",
            required_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_flagship_run_bundle_surface.py",
            ),
        ),
        ArchitectureRegressionTarget(
            surface="workflow-output-validation",
            command=(
                sys.executable,
                "-m",
                "pytest",
                "packages/bijux-proteomics-core/tests/workflow/test_workflow_output_validation_surface.py",
                "-q",
                "-p",
                "no:cov",
                "--import-mode=importlib",
            ),
            rationale="prove governed workflow artifact manifests still validate after refactor pressure",
            required_paths=(
                "packages/bijux-proteomics-core/tests/workflow/test_workflow_output_validation_surface.py",
            ),
        ),
        ArchitectureRegressionTarget(
            surface="shipped-demo-cli",
            command=(
                sys.executable,
                "-m",
                "pytest",
                "packages/bijux-proteomics-core/tests/cli/test_shipped_demo_cli_tutorial_surface.py",
                "-q",
                "-p",
                "no:cov",
                "--import-mode=importlib",
            ),
            rationale="prove the shipped demo still runs, validates, and queries through the documented CLI path",
            required_paths=(
                "packages/bijux-proteomics-core/tests/cli/test_shipped_demo_cli_tutorial_surface.py",
            ),
        ),
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


def _run_subprocess(command: tuple[str, ...], *, cwd: Path) -> tuple[bool, str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=_subprocess_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    output = completed.stdout.strip()
    error_output = completed.stderr.strip()
    detail = output or error_output or f"command exited with status {completed.returncode}"
    return completed.returncode == 0, detail


def validate_architecture_regression_targets(repo_root: Path) -> list[str]:
    """Validate the curated architecture regression targets."""

    failures: list[str] = []
    expected_surfaces = {
        "imports-and-collection",
        "public-api-snapshots",
        "internal-architecture-map",
        "canonical-package-tree",
        "runtime-output-snapshots",
        "workflow-output-validation",
        "shipped-demo-cli",
    }
    surfaces = {target.surface for target in default_architecture_regression_targets()}
    if surfaces != expected_surfaces:
        failures.append(
            "architecture regression surfaces changed from "
            f"{sorted(expected_surfaces)} to {sorted(surfaces)}"
        )
    for target in default_architecture_regression_targets():
        for relative_path in target.required_paths:
            if not (repo_root / relative_path).exists():
                failures.append(
                    f"missing architecture regression target path: {relative_path}"
                )
    return failures


def run_architecture_regression_gate(repo_root: Path, *, execute: bool = False) -> int:
    """Validate or execute the curated architecture regression gate."""

    failures = validate_architecture_regression_targets(repo_root)
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    if not execute:
        return 0

    gate_failures: list[str] = []
    for target in default_architecture_regression_targets():
        ok, detail = _run_subprocess(target.command, cwd=repo_root)
        if not ok:
            gate_failures.append(f"[{target.surface}] {detail}")
    if not gate_failures:
        print("architecture regression gate passed")
        return 0
    print("architecture regression gate failed")
    for failure in gate_failures:
        print(failure)
    return 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the curated post-refactor architecture regression gate."
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate the target list without executing the gate commands.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    return run_architecture_regression_gate(
        REPO_ROOT,
        execute=not args.validate_only,
    )


if __name__ == "__main__":
    raise SystemExit(main())
