"""Curated architecture regression gate for post-refactor hardening checks."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import sys

from bijux_proteomics_dev.governance.package_shape.public_api_snapshots import (
    CANONICAL_PUBLIC_API_PACKAGES,
)
from bijux_proteomics_dev.governance.dependencies.internal_architecture_map import (
    build_internal_architecture_map_report,
    evaluate_internal_architecture_violations,
    is_internal_architecture_map_up_to_date,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    import_root,
    workspace_src_parents,
)
from bijux_proteomics_dev.security.trusted_process import run_text

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
            surface="canonical-root-imports",
            command=(
                sys.executable,
                "-m",
                "bijux_proteomics_dev.quality.gates.architecture_regression_gate",
                "--canonical-root-imports",
            ),
            rationale="prove canonical product-package roots still import after package-tree hardening",
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
                "bijux_proteomics_dev.quality.gates.architecture_regression_gate",
                "--canonical-internal-architecture-map",
            ),
            rationale="prove the generated internal architecture map still matches live canonical package and module dependencies",
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
            surface="runtime-architecture-demo",
            command=(
                sys.executable,
                "-m",
                "pytest",
                "packages/bijux-proteomics-runtime/tests/workflows/test_runtime_architecture_demo_surface.py",
                "-q",
                "-p",
                "no:cov",
                "--import-mode=importlib",
            ),
            rationale="prove the shipped runtime architecture demo still rehydrates a real completed run after architecture changes",
            required_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_runtime_architecture_demo_surface.py",
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
    completed = run_text(
        command,
        cwd=cwd,
        env=_subprocess_env(),
        capture_output=True,
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
        "canonical-root-imports",
        "public-api-snapshots",
        "internal-architecture-map",
        "canonical-package-tree",
        "runtime-architecture-demo",
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


def run_canonical_root_imports(
    repo_root: Path,
    *,
    python_executable: str | None = None,
) -> int:
    """Run root import checks for the six canonical product packages."""

    executable = python_executable or sys.executable
    failures: list[str] = []
    for package_name in CANONICAL_PUBLIC_API_PACKAGES:
        module_name = import_root(package_name)
        import_command = (
            executable,
            "-c",
            f"import {module_name}",
        )
        ok, detail = _run_subprocess(import_command, cwd=repo_root)
        if not ok:
            failures.append(f"[import] {package_name} -> {module_name}: {detail}")
    if not failures:
        print("canonical root import checks passed")
        return 0
    print("canonical root import checks failed")
    for failure in failures:
        print(failure)
    return 1


def run_canonical_internal_architecture_map() -> int:
    """Validate the internal architecture map without broader workspace cycle discovery."""

    report = build_internal_architecture_map_report()
    failures = [
        violation.detail
        for violation in evaluate_internal_architecture_violations(
            report,
            workspace_cycles=(),
        )
    ]
    if not is_internal_architecture_map_up_to_date(report):
        failures.append("internal architecture map is stale; regenerate it")
    if not failures:
        print("canonical internal architecture map checks passed")
        return 0
    print("canonical internal architecture map checks failed")
    for failure in failures:
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
    parser.add_argument(
        "--canonical-root-imports",
        action="store_true",
        help="Run only the canonical product-package root import checks.",
    )
    parser.add_argument(
        "--canonical-internal-architecture-map",
        action="store_true",
        help="Run only the canonical internal architecture map validation path.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.canonical_root_imports:
        return run_canonical_root_imports(REPO_ROOT)
    if args.canonical_internal_architecture_map:
        return run_canonical_internal_architecture_map()
    return run_architecture_regression_gate(
        REPO_ROOT,
        execute=not args.validate_only,
    )


if __name__ == "__main__":
    raise SystemExit(main())
