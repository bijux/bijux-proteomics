from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.api.foundation.root_consumers import REPO_ROOT

__all__ = [
    "FOUNDATION_KERNEL_BOUNDARIES_PATH",
    "FoundationKernelBoundaryCheck",
    "build_foundation_kernel_boundaries",
    "run",
    "validate_foundation_kernel_boundaries",
]


FOUNDATION_PACKAGE_ROOT = REPO_ROOT / "packages" / "bijux-proteomics-foundation"
FOUNDATION_SRC_ROOT = FOUNDATION_PACKAGE_ROOT / "src" / "bijux_proteomics_foundation"
FOUNDATION_TEST_ROOT = FOUNDATION_PACKAGE_ROOT / "tests"
FOUNDATION_KERNEL_BOUNDARIES_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "foundation-kernel-boundaries.toml"
)

PRODUCT_TOKENS = (
    "agentic",
    "core",
    "intelligence",
    "knowledge",
    "lab",
    "runtime",
)
FIXTURE_TOKENS = (
    "example",
    "examples",
    "fixture",
    "fixtures",
    "golden",
    "sample",
    "samples",
    "snapshot",
    "snapshots",
)
PRESENTATION_TOKENS = (
    "cli",
    "console",
    "markdown",
    "render",
    "response",
    "route",
    "router",
)


@dataclass(frozen=True)
class FoundationKernelBoundaryCheck:
    """One release-blocking kernel boundary check."""

    policy_id: str
    checked_path_count: int
    checked_symbol_count: int
    violations: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return not self.violations


def _python_files(root: Path) -> tuple[Path, ...]:
    return tuple(
        sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)
    )


def _defined_names(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return tuple(
        node.name.lower()
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    )


def _path_signature(path: Path, *, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _product_fixture_check() -> FoundationKernelBoundaryCheck:
    scanned_paths = (*_python_files(FOUNDATION_SRC_ROOT), *_python_files(FOUNDATION_TEST_ROOT))
    checked_symbol_count = 0
    violations: list[str] = []

    for path in scanned_paths:
        relative_path = _path_signature(path, root=FOUNDATION_PACKAGE_ROOT)
        path_text = relative_path.lower()
        defined_names = _defined_names(path)
        checked_symbol_count += len(defined_names)

        if any(token in path_text for token in PRODUCT_TOKENS) and any(
            token in path_text for token in FIXTURE_TOKENS
        ):
            violations.append(relative_path)
            continue

        for name in defined_names:
            if any(token in name for token in PRODUCT_TOKENS) and any(
                token in name for token in FIXTURE_TOKENS
            ):
                violations.append(f"{relative_path}::{name}")

    return FoundationKernelBoundaryCheck(
        policy_id="no-product-specific-fixtures",
        checked_path_count=len(scanned_paths),
        checked_symbol_count=checked_symbol_count,
        violations=tuple(sorted(set(violations))),
    )


def _presentation_helper_check() -> FoundationKernelBoundaryCheck:
    scanned_paths = _python_files(FOUNDATION_SRC_ROOT)
    checked_symbol_count = 0
    violations: list[str] = []

    for path in scanned_paths:
        relative_path = _path_signature(path, root=FOUNDATION_PACKAGE_ROOT)
        path_text = relative_path.lower()
        defined_names = _defined_names(path)
        checked_symbol_count += len(defined_names)

        if any(token in path_text for token in PRESENTATION_TOKENS):
            violations.append(relative_path)
            continue

        for name in defined_names:
            if any(token in name for token in PRESENTATION_TOKENS):
                violations.append(f"{relative_path}::{name}")

    return FoundationKernelBoundaryCheck(
        policy_id="no-route-cli-markdown-helpers",
        checked_path_count=len(scanned_paths),
        checked_symbol_count=checked_symbol_count,
        violations=tuple(sorted(set(violations))),
    )


def build_foundation_kernel_boundaries() -> tuple[FoundationKernelBoundaryCheck, ...]:
    """Build the checked foundation kernel boundary report."""

    return (
        _product_fixture_check(),
        _presentation_helper_check(),
    )


def validate_foundation_kernel_boundaries() -> tuple[str, ...]:
    """Fail release when foundation crosses its kernel boundary."""

    failures: list[str] = []
    for check in build_foundation_kernel_boundaries():
        if check.ready:
            continue
        failures.append(
            f"{check.policy_id} failed: {', '.join(check.violations)}"
        )
    return tuple(failures)


def _toml_text(checks: tuple[FoundationKernelBoundaryCheck, ...]) -> str:
    lines = [
        "# Generated foundation kernel boundary report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.foundation.kernel_boundaries",
        "",
    ]
    for check in checks:
        violations = ", ".join(f'"{value}"' for value in check.violations)
        lines.extend(
            [
                "[[check]]",
                f'policy_id = "{check.policy_id}"',
                f"checked_path_count = {check.checked_path_count}",
                f"checked_symbol_count = {check.checked_symbol_count}",
                f"ready = {str(check.ready).lower()}",
                f"violations = [{violations}]",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(checks: tuple[FoundationKernelBoundaryCheck, ...]) -> bool:
    if not FOUNDATION_KERNEL_BOUNDARIES_PATH.exists():
        return False
    return FOUNDATION_KERNEL_BOUNDARIES_PATH.read_text(encoding="utf-8") == _toml_text(
        checks
    )


def run(check: bool = False) -> int:
    checks = build_foundation_kernel_boundaries()
    failures = validate_foundation_kernel_boundaries()
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(checks):
            print("foundation kernel boundary report is up to date")
            return 0
        print("foundation kernel boundary report is stale; regenerate it")
        return 1
    FOUNDATION_KERNEL_BOUNDARIES_PATH.write_text(
        _toml_text(checks),
        encoding="utf-8",
    )
    print("generated foundation kernel boundary report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the foundation kernel boundary report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the foundation kernel boundary report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
