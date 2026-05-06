from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT

__all__ = [
    "LAB_RUNTIME_BOUNDARY_DRIFT_PATH",
    "LabRuntimeBoundaryDriftReport",
    "build_lab_runtime_boundary_drift_report",
    "run",
    "validate_lab_runtime_boundary_drift",
]


LAB_SRC_ROOT = (
    REPO_ROOT / "packages" / "bijux-proteomics-lab" / "src" / "bijux_proteomics_lab"
)
LAB_RUNTIME_BOUNDARY_DRIFT_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "lab-runtime-boundary-drift.toml"
)
FORBIDDEN_PATH_PARTS = (
    "api",
    "cli",
    "execution",
    "interfaces",
    "provider",
    "providers",
    "route",
    "routes",
    "runtime",
    "transport",
)
FORBIDDEN_IMPORT_PREFIXES = (
    "bijux_proteomics_runtime",
    "fastapi",
    "starlette",
    "uvicorn",
)
FORBIDDEN_DEFINITION_TERMS = (
    "router",
    "endpoint",
    "handler",
    "provider",
    "scheduler",
    "transport",
    "create_app",
    "dispatch_run",
    "run_route",
)


@dataclass(frozen=True)
class LabRuntimeBoundaryDriftReport:
    """Release-blocking drift report for runtime and transport leakage into lab."""

    forbidden_module_paths: tuple[str, ...]
    forbidden_import_edges: tuple[str, ...]
    forbidden_definition_names: tuple[str, ...]


def _source_modules() -> tuple[Path, ...]:
    return tuple(sorted(LAB_SRC_ROOT.rglob("*.py")))


def _matches_forbidden_definition(name: str) -> bool:
    lowered = name.lower()
    return any(term in lowered for term in FORBIDDEN_DEFINITION_TERMS)


def build_lab_runtime_boundary_drift_report() -> LabRuntimeBoundaryDriftReport:
    """Build the checked drift report for runtime and transport leakage."""

    forbidden_module_paths: list[str] = []
    forbidden_import_edges: list[str] = []
    forbidden_definition_names: list[str] = []

    for path in _source_modules():
        relative = path.relative_to(LAB_SRC_ROOT).as_posix()
        if any(part in FORBIDDEN_PATH_PARTS for part in path.relative_to(LAB_SRC_ROOT).parts):
            forbidden_module_paths.append(relative)

        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                        forbidden_import_edges.append(f"{relative}: {alias.name}")
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                if node.module.startswith(FORBIDDEN_IMPORT_PREFIXES):
                    forbidden_import_edges.append(f"{relative}: {node.module}")
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if _matches_forbidden_definition(node.name):
                    forbidden_definition_names.append(f"{relative}: {node.name}")

    return LabRuntimeBoundaryDriftReport(
        forbidden_module_paths=tuple(sorted(forbidden_module_paths)),
        forbidden_import_edges=tuple(sorted(forbidden_import_edges)),
        forbidden_definition_names=tuple(sorted(forbidden_definition_names)),
    )


def validate_lab_runtime_boundary_drift(
    report: LabRuntimeBoundaryDriftReport | None = None,
) -> tuple[str, ...]:
    """Fail release when lab starts owning runtime orchestration or transport."""

    report = report or build_lab_runtime_boundary_drift_report()
    failures: list[str] = []
    if report.forbidden_module_paths:
        failures.append(
            "lab source tree added runtime or transport-shaped module paths: "
            + ", ".join(report.forbidden_module_paths)
        )
    if report.forbidden_import_edges:
        failures.append(
            "lab source imports runtime or route frameworks: "
            + ", ".join(report.forbidden_import_edges)
        )
    if report.forbidden_definition_names:
        failures.append(
            "lab source defines runtime or transport-shaped symbols: "
            + ", ".join(report.forbidden_definition_names)
        )
    return tuple(failures)


def _toml_text(report: LabRuntimeBoundaryDriftReport) -> str:
    module_paths = ", ".join(f'"{value}"' for value in report.forbidden_module_paths)
    import_edges = ", ".join(f'"{value}"' for value in report.forbidden_import_edges)
    definition_names = ", ".join(
        f'"{value}"' for value in report.forbidden_definition_names
    )
    return "\n".join(
        (
            "# Generated lab runtime boundary drift report.",
            "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.lab.runtime_boundary_drift",
            "",
            "[metrics]",
            f"forbidden_module_paths = [{module_paths}]",
            f"forbidden_import_edges = [{import_edges}]",
            f"forbidden_definition_names = [{definition_names}]",
        )
    )


def _is_up_to_date(report: LabRuntimeBoundaryDriftReport) -> bool:
    if not LAB_RUNTIME_BOUNDARY_DRIFT_PATH.exists():
        return False
    return LAB_RUNTIME_BOUNDARY_DRIFT_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_lab_runtime_boundary_drift_report()
    failures = validate_lab_runtime_boundary_drift(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("lab runtime boundary drift report is up to date")
            return 0
        print("lab runtime boundary drift report is stale; regenerate it")
        return 1
    LAB_RUNTIME_BOUNDARY_DRIFT_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated lab runtime boundary drift report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the lab runtime boundary drift report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the lab runtime boundary drift report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
