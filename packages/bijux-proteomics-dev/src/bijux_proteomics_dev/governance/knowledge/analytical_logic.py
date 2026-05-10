from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass

from bijux_proteomics_dev.governance.knowledge.boundary_drift import KNOWLEDGE_SRC_ROOT
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT

__all__ = [
    "KNOWLEDGE_ANALYTICAL_LOGIC_PATH",
    "KnowledgeAnalyticalLogicModule",
    "build_knowledge_analytical_logic_report",
    "run",
    "validate_knowledge_analytical_logic",
]


KNOWLEDGE_ANALYTICAL_LOGIC_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "knowledge-analytical-logic.toml"
)
ANALYTICAL_IDENTIFIER_TERMS = (
    "disposition",
    "intelligence_index",
    "priorit",
    "ranking",
    "recommendation",
    "recommendations",
    "score",
)
ALLOWED_ANALYTICAL_MODULES = (
    "memory/models/claims.py",
    "memory/models/evidence.py",
    "memory/reconciliation/resolution.py",
    "references/grounding/rules.py",
    "references/workflows/comparator_scorecards.py",
    "references/workflows/lookups.py",
    "references/workflows/scientific_release.py",
    "references/workflows/scientific_risk.py",
    "reviews/decision_briefs.py",
    "reviews/explanations.py",
    "reviews/trends.py",
)


@dataclass(frozen=True)
class KnowledgeAnalyticalLogicModule:
    """One module that currently carries analytical scoring or recommendation identifiers."""

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


def build_knowledge_analytical_logic_report() -> tuple[
    KnowledgeAnalyticalLogicModule, ...
]:
    """Build the checked report of analytical logic hotspots in knowledge."""

    modules: list[KnowledgeAnalyticalLogicModule] = []
    for path in sorted(KNOWLEDGE_SRC_ROOT.rglob("*.py")):
        relative = path.relative_to(KNOWLEDGE_SRC_ROOT).as_posix()
        matches = _matched_identifiers(path.read_text(encoding="utf-8"))
        if not matches:
            continue
        modules.append(
            KnowledgeAnalyticalLogicModule(
                module_path=relative,
                matched_identifiers=matches,
            )
        )
    return tuple(modules)


def validate_knowledge_analytical_logic(
    report: tuple[KnowledgeAnalyticalLogicModule, ...] | None = None,
) -> tuple[str, ...]:
    """Fail release when analytical scoring or recommendation logic spreads."""

    report = report or build_knowledge_analytical_logic_report()
    observed_modules = tuple(module.module_path for module in report)
    failures: list[str] = []

    if observed_modules != ALLOWED_ANALYTICAL_MODULES:
        failures.append(
            "knowledge analytical logic modules drifted from the governed hotspot set: "
            + ", ".join(observed_modules)
        )
    unexpected = [
        module.module_path
        for module in report
        if module.module_path not in ALLOWED_ANALYTICAL_MODULES
    ]
    if unexpected:
        failures.append(
            "knowledge added analytical scoring or recommendation identifiers outside the governed hotspot modules: "
            + ", ".join(sorted(unexpected))
        )
    return tuple(failures)


def _toml_text(report: tuple[KnowledgeAnalyticalLogicModule, ...]) -> str:
    lines = [
        "# Generated knowledge analytical logic hotspot report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.knowledge.analytical_logic",
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


def _is_up_to_date(report: tuple[KnowledgeAnalyticalLogicModule, ...]) -> bool:
    if not KNOWLEDGE_ANALYTICAL_LOGIC_PATH.exists():
        return False
    return KNOWLEDGE_ANALYTICAL_LOGIC_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_knowledge_analytical_logic_report()
    failures = validate_knowledge_analytical_logic(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("knowledge analytical logic report is up to date")
            return 0
        print("knowledge analytical logic report is stale; regenerate it")
        return 1
    KNOWLEDGE_ANALYTICAL_LOGIC_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated knowledge analytical logic report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the knowledge analytical logic report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the knowledge analytical logic report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
