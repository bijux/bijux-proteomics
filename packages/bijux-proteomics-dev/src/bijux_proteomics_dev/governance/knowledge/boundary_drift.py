from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.governance.foundation.root_consumers import REPO_ROOT

__all__ = [
    "KNOWLEDGE_BOUNDARY_DRIFT_PATH",
    "KnowledgeBoundaryDriftReport",
    "build_knowledge_boundary_drift_report",
    "run",
    "validate_knowledge_boundary_drift",
]


KNOWLEDGE_SRC_ROOT = (
    REPO_ROOT
    / "packages"
    / "bijux-proteomics-knowledge"
    / "src"
    / "bijux_proteomics_knowledge"
)
KNOWLEDGE_BOUNDARY_DRIFT_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "knowledge-boundary-drift.toml"
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
    "route",
    "router",
    "endpoint",
    "handler",
    "provider",
    "scheduler",
    "preflight",
    "rerun",
    "create_app",
    "cli",
)


@dataclass(frozen=True)
class KnowledgeBoundaryDriftReport:
    """Release-blocking drift report for execution and route ownership leaks."""

    forbidden_module_paths: tuple[str, ...]
    forbidden_import_edges: tuple[str, ...]
    forbidden_definition_names: tuple[str, ...]


def _source_modules() -> tuple[Path, ...]:
    return tuple(sorted(KNOWLEDGE_SRC_ROOT.rglob("*.py")))


def _matches_forbidden_definition(name: str) -> bool:
    lower_name = name.lower()
    return any(term in lower_name for term in FORBIDDEN_DEFINITION_TERMS)


def build_knowledge_boundary_drift_report() -> KnowledgeBoundaryDriftReport:
    """Build the checked drift report for execution and route-shaped leakage."""

    forbidden_module_paths: list[str] = []
    forbidden_import_edges: list[str] = []
    forbidden_definition_names: list[str] = []

    for path in _source_modules():
        relative = path.relative_to(KNOWLEDGE_SRC_ROOT).as_posix()
        parts = path.relative_to(KNOWLEDGE_SRC_ROOT).parts
        if any(part in FORBIDDEN_PATH_PARTS for part in parts):
            forbidden_module_paths.append(relative)

        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                        forbidden_import_edges.append(f"{relative}: {alias.name}")
            if (
                isinstance(node, ast.ImportFrom)
                and node.module is not None
                and node.module.startswith(FORBIDDEN_IMPORT_PREFIXES)
            ):
                forbidden_import_edges.append(f"{relative}: {node.module}")
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ) and _matches_forbidden_definition(node.name):
                forbidden_definition_names.append(f"{relative}: {node.name}")

    return KnowledgeBoundaryDriftReport(
        forbidden_module_paths=tuple(sorted(forbidden_module_paths)),
        forbidden_import_edges=tuple(sorted(forbidden_import_edges)),
        forbidden_definition_names=tuple(sorted(forbidden_definition_names)),
    )


def validate_knowledge_boundary_drift(
    report: KnowledgeBoundaryDriftReport | None = None,
) -> tuple[str, ...]:
    """Fail release when knowledge begins carrying execution or route ownership."""

    report = report or build_knowledge_boundary_drift_report()
    failures: list[str] = []
    if report.forbidden_module_paths:
        failures.append(
            "knowledge source tree added execution or route-shaped module paths: "
            + ", ".join(report.forbidden_module_paths)
        )
    if report.forbidden_import_edges:
        failures.append(
            "knowledge source imports execution or route frameworks: "
            + ", ".join(report.forbidden_import_edges)
        )
    if report.forbidden_definition_names:
        failures.append(
            "knowledge source defines execution or route-shaped symbols: "
            + ", ".join(report.forbidden_definition_names)
        )
    return tuple(failures)


def _toml_text(report: KnowledgeBoundaryDriftReport) -> str:
    module_paths = ", ".join(f'"{value}"' for value in report.forbidden_module_paths)
    import_edges = ", ".join(f'"{value}"' for value in report.forbidden_import_edges)
    definition_names = ", ".join(
        f'"{value}"' for value in report.forbidden_definition_names
    )
    return "\n".join(
        (
            "# Generated knowledge boundary drift report.",
            "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.knowledge.boundary_drift",
            "",
            "[metrics]",
            f"forbidden_module_paths = [{module_paths}]",
            f"forbidden_import_edges = [{import_edges}]",
            f"forbidden_definition_names = [{definition_names}]",
        )
    )


def _is_up_to_date(report: KnowledgeBoundaryDriftReport) -> bool:
    if not KNOWLEDGE_BOUNDARY_DRIFT_PATH.exists():
        return False
    return KNOWLEDGE_BOUNDARY_DRIFT_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_knowledge_boundary_drift_report()
    failures = validate_knowledge_boundary_drift(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("knowledge boundary drift report is up to date")
            return 0
        print("knowledge boundary drift report is stale; regenerate it")
        return 1
    KNOWLEDGE_BOUNDARY_DRIFT_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated knowledge boundary drift report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the knowledge boundary drift report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the knowledge boundary drift report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
