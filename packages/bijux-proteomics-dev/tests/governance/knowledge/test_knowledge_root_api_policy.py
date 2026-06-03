from __future__ import annotations

import ast
from pathlib import Path
import tomllib
from typing import Any, cast

import pytest

import bijux_proteomics_knowledge

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
KNOWLEDGE_ROOT = (
    REPO_ROOT
    / "packages"
    / "bijux-proteomics-knowledge"
    / "src"
    / "bijux_proteomics_knowledge"
)
KNOWLEDGE_ROOT_INIT = KNOWLEDGE_ROOT / "__init__.py"
KNOWLEDGE_ROOT_API_POLICY = (
    REPO_ROOT / "configs" / "package-governance" / "knowledge-root-api.toml"
)
PUBLIC_SURFACE_TESTS = {
    "packages/bijux-proteomics-dev/src/bijux_proteomics_dev/release/governance/cross_package_smoke.py",
    "packages/bijux-proteomics-dev/tests/governance/knowledge/test_knowledge_root_api_policy.py",
    "packages/bijux-proteomics-knowledge/tests/package/test_package_grounding_guards.py",
    "packages/bijux-proteomics-knowledge/tests/package/test_public_function_docstring_contract.py",
    "packages/bijux-proteomics-knowledge/tests/contracts/test_schema.py",
    "packages/bijux-proteomics-knowledge/tests/package/test_public_api_surface.py",
    "packages/bijux-proteomics-knowledge/tests/package/test_serialization.py",
    "packages/proteomics-knowledge/tests/compatibility/test_proteomics_knowledge_alias.py",
}


def _policy() -> dict[str, Any]:
    return tomllib.loads(KNOWLEDGE_ROOT_API_POLICY.read_text(encoding="utf-8"))


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


def _imports_knowledge_root(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "bijux_proteomics_knowledge":
                    return True
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "bijux_proteomics_knowledge"
        ):
            return True
    return False


def test_knowledge_root_api_matches_curated_policy() -> None:
    policy = _policy()
    entries = _symbol_entries(policy)

    assert [entry["name"] for entry in entries] == list(
        bijux_proteomics_knowledge.__all__
    )
    assert all(entry["owner_module"] for entry in entries)
    assert all(entry["classification"] for entry in entries)
    assert all(entry["rationale"] for entry in entries)


def test_knowledge_root_api_stays_within_budget() -> None:
    policy = _policy()
    budget = _budget(policy)
    init_lines = KNOWLEDGE_ROOT_INIT.read_text(encoding="utf-8").splitlines()

    assert len(bijux_proteomics_knowledge.__all__) <= budget["max_public_symbols"]
    assert len(init_lines) <= budget["max_init_lines"]


def test_knowledge_root_excludes_convenience_symbol_exports() -> None:
    removed = {
        "EvidenceKind",
        "KnowledgeGap",
        "build_claim",
        "build_knowledge_decision_brief",
        "evidence_gaps",
    }

    assert removed.isdisjoint(bijux_proteomics_knowledge.__all__)


@pytest.mark.slow
def test_knowledge_root_is_not_used_inside_repo_owners() -> None:
    violations: list[str] = []
    for path in sorted((REPO_ROOT / "packages").rglob("*.py")):
        relative = path.relative_to(REPO_ROOT).as_posix()
        if relative in PUBLIC_SURFACE_TESTS:
            continue
        if _imports_knowledge_root(path):
            violations.append(relative)

    assert violations == []
