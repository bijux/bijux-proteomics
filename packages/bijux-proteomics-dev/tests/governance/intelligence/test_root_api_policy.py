from __future__ import annotations

import ast
from pathlib import Path
import tomllib
from typing import Any, cast

import bijux_proteomics_intelligence

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
INTELLIGENCE_ROOT = (
    REPO_ROOT
    / "packages"
    / "bijux-proteomics-intelligence"
    / "src"
    / "bijux_proteomics_intelligence"
)
INTELLIGENCE_ROOT_INIT = INTELLIGENCE_ROOT / "__init__.py"
INTELLIGENCE_ROOT_API_POLICY = (
    REPO_ROOT / "configs" / "package-governance" / "intelligence-root-api.toml"
)
PUBLIC_SURFACE_TESTS = {
    "packages/bijux-proteomics-intelligence/tests/package/test_public_api_surface.py",
}


def _policy() -> dict[str, Any]:
    return tomllib.loads(INTELLIGENCE_ROOT_API_POLICY.read_text(encoding="utf-8"))


def _symbol_entries(policy: dict[str, Any]) -> list[dict[str, Any]]:
    entries = policy["symbol"]
    assert isinstance(entries, list)
    assert all(isinstance(entry, dict) for entry in entries)
    return [cast(dict[str, Any], entry) for entry in entries]


def _budget(policy: dict[str, Any]) -> dict[str, int]:
    budget = policy["budget"]
    assert isinstance(budget, dict)
    return {
        "max_public_symbols": int(budget["max_public_symbols"]),
        "max_init_lines": int(budget["max_init_lines"]),
    }


def _imports_intelligence_root(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "bijux_proteomics_intelligence":
                    return True
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "bijux_proteomics_intelligence"
        ):
            return True
    return False


def test_intelligence_root_api_matches_curated_policy() -> None:
    policy = _policy()
    entries = _symbol_entries(policy)

    assert [entry["name"] for entry in entries] == list(
        bijux_proteomics_intelligence.__all__
    )
    assert all(entry["owner_module"] for entry in entries)
    assert all(entry["classification"] for entry in entries)
    assert all(entry["rationale"] for entry in entries)


def test_intelligence_root_api_stays_within_budget() -> None:
    policy = _policy()
    budget = _budget(policy)
    init_lines = INTELLIGENCE_ROOT_INIT.read_text(encoding="utf-8").splitlines()

    assert len(bijux_proteomics_intelligence.__all__) <= budget["max_public_symbols"]
    assert len(init_lines) <= budget["max_init_lines"]


def test_intelligence_root_excludes_convenience_symbol_exports() -> None:
    removed = {
        "benchmark_reviews",
        "briefs",
        "charter",
        "decision_paths",
        "evidence_posture",
        "evaluators",
        "follow_up_learning",
        "policies",
        "skeptical_review",
    }

    assert removed.isdisjoint(bijux_proteomics_intelligence.__all__)


def test_intelligence_root_is_not_used_inside_intelligence_owners() -> None:
    violations: list[str] = []
    for path in sorted(INTELLIGENCE_ROOT.rglob("*.py")):
        if _imports_intelligence_root(path):
            violations.append(path.relative_to(REPO_ROOT).as_posix())

    intelligence_tests = (
        REPO_ROOT / "packages" / "bijux-proteomics-intelligence" / "tests"
    )
    for path in sorted(intelligence_tests.rglob("*.py")):
        relative = path.relative_to(REPO_ROOT).as_posix()
        if relative in PUBLIC_SURFACE_TESTS:
            continue
        if _imports_intelligence_root(path):
            violations.append(relative)

    assert violations == []
