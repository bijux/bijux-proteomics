from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass

from bijux_proteomics_dev.api.runtime_topology import REPO_ROOT

__all__ = [
    "ALLOWED_ANALYTICAL_MODULES",
    "LAB_ANALYTICAL_LOGIC_PATH",
    "LabAnalyticalLogicModule",
    "build_lab_analytical_logic_report",
    "run",
    "validate_lab_analytical_logic",
]


LAB_SRC_ROOT = (
    REPO_ROOT / "packages" / "bijux-proteomics-lab" / "src" / "bijux_proteomics_lab"
)
LAB_ANALYTICAL_LOGIC_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "lab-analytical-logic.toml"
)
ANALYTICAL_IDENTIFIER_TERMS = (
    "candidate_assess",
    "contradiction_pressure",
    "decision_path",
    "discovery_ranking",
    "ranking",
    "skeptic",
)
ALLOWED_ANALYTICAL_MODULES = (
    "benchmarks/claims.py",
    "handoffs/explanations.py",
    "lifecycle/progression.py",
    "planning/assays.py",
)


@dataclass(frozen=True)
class LabAnalyticalLogicModule:
    """One lab module that carries governed analytical-adjacent hotspot identifiers."""

    module_path: str
    matched_identifiers: tuple[str, ...]


def _matched_identifiers(path_text: str) -> tuple[str, ...]:
    tree = ast.parse(path_text)
    identifiers: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            identifiers.add(node.name)
        elif isinstance(node, ast.Name):
            identifiers.add(node.id)
        elif isinstance(node, ast.arg):
            identifiers.add(node.arg)
        elif isinstance(node, ast.Attribute):
            identifiers.add(node.attr)
    return tuple(
        sorted(
            identifier
            for identifier in identifiers
            if any(term in identifier.lower() for term in ANALYTICAL_IDENTIFIER_TERMS)
        )
    )


def build_lab_analytical_logic_report() -> tuple[LabAnalyticalLogicModule, ...]:
    """Build the checked report of analytical-adjacent hotspots in lab."""

    modules: list[LabAnalyticalLogicModule] = []
    for path in sorted(LAB_SRC_ROOT.rglob("*.py")):
        relative = path.relative_to(LAB_SRC_ROOT).as_posix()
        matches = _matched_identifiers(path.read_text(encoding="utf-8"))
        if not matches:
            continue
        modules.append(
            LabAnalyticalLogicModule(
                module_path=relative,
                matched_identifiers=matches,
            )
        )
    return tuple(modules)


def validate_lab_analytical_logic(
    report: tuple[LabAnalyticalLogicModule, ...] | None = None,
) -> tuple[str, ...]:
    """Fail release when lab analytical-adjacent hotspots spread."""

    report = report or build_lab_analytical_logic_report()
    observed_modules = tuple(module.module_path for module in report)
    failures: list[str] = []

    if observed_modules != ALLOWED_ANALYTICAL_MODULES:
        failures.append(
            "lab analytical hotspot modules drifted from the governed operational set: "
            + ", ".join(observed_modules)
        )
    unexpected = [
        module.module_path
        for module in report
        if module.module_path not in ALLOWED_ANALYTICAL_MODULES
    ]
    if unexpected:
        failures.append(
            "lab added analytical-adjacent identifiers outside the governed operational modules: "
            + ", ".join(sorted(unexpected))
        )
    return tuple(failures)


def _toml_text(report: tuple[LabAnalyticalLogicModule, ...]) -> str:
    lines = [
        "# Generated lab analytical hotspot report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.lab_analytical_logic",
        "",
    ]
    for module in report:
        matched_identifiers = ", ".join(
            f'"{identifier}"' for identifier in module.matched_identifiers
        )
        lines.extend(
            [
                "[[module]]",
                f'path = "{module.module_path}"',
                f"matched_identifiers = [{matched_identifiers}]",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: tuple[LabAnalyticalLogicModule, ...]) -> bool:
    if not LAB_ANALYTICAL_LOGIC_PATH.exists():
        return False
    return LAB_ANALYTICAL_LOGIC_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_lab_analytical_logic_report()
    failures = validate_lab_analytical_logic(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("lab analytical hotspot report is up to date")
            return 0
        print("lab analytical hotspot report is stale; regenerate it")
        return 1
    LAB_ANALYTICAL_LOGIC_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated lab analytical hotspot report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the lab analytical hotspot report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the lab analytical hotspot report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
