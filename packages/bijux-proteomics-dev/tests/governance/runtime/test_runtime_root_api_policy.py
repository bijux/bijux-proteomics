from __future__ import annotations

import ast
from pathlib import Path
import tomllib
from typing import Any, cast

import bijux_proteomics_runtime

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
RUNTIME_ROOT = (
    REPO_ROOT
    / "packages"
    / "bijux-proteomics-runtime"
    / "src"
    / "bijux_proteomics_runtime"
)
RUNTIME_ROOT_INIT = RUNTIME_ROOT / "__init__.py"
RUNTIME_ROOT_API_POLICY = (
    REPO_ROOT / "configs" / "package-governance" / "runtime-root-api.toml"
)
PUBLIC_SURFACE_TESTS = {
    "packages/bijux-proteomics-runtime/tests/package/test_runtime_boundary_guards.py",
    "packages/bijux-proteomics-runtime/tests/package/test_runtime_package_smoke.py",
    "packages/bijux-proteomics-runtime/tests/package/test_public_function_docstring_contract.py",
    "packages/bijux-proteomics-runtime/tests/package/test_public_api_surface.py",
}


def _policy() -> dict[str, Any]:
    return tomllib.loads(RUNTIME_ROOT_API_POLICY.read_text(encoding="utf-8"))


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


def _imports_runtime_root(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "bijux_proteomics_runtime":
                    return True
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "bijux_proteomics_runtime"
        ):
            return True
    return False


def test_runtime_root_api_matches_curated_policy() -> None:
    policy = _policy()
    entries = _symbol_entries(policy)

    assert [entry["name"] for entry in entries] == list(
        bijux_proteomics_runtime.__all__
    )
    assert all(entry["owner_module"] for entry in entries)
    assert all(entry["classification"] for entry in entries)
    assert all(entry["rationale"] for entry in entries)


def test_runtime_root_api_stays_within_budget() -> None:
    policy = _policy()
    budget = _budget(policy)
    init_lines = RUNTIME_ROOT_INIT.read_text(encoding="utf-8").splitlines()

    assert len(bijux_proteomics_runtime.__all__) <= budget["max_public_symbols"]
    assert len(init_lines) <= budget["max_init_lines"]


def test_runtime_root_excludes_internal_support_exports() -> None:
    removed = {
        "RunConfig",
        "RuntimeFailureReport",
        "RuntimePreflightReport",
        "WorkflowRunDiffReport",
    }

    assert removed.isdisjoint(bijux_proteomics_runtime.__all__)


def test_runtime_root_is_not_used_inside_runtime_owners() -> None:
    violations: list[str] = []
    for path in sorted(RUNTIME_ROOT.rglob("*.py")):
        if _imports_runtime_root(path):
            violations.append(path.relative_to(REPO_ROOT).as_posix())
    runtime_tests = REPO_ROOT / "packages" / "bijux-proteomics-runtime" / "tests"
    for path in sorted(runtime_tests.rglob("*.py")):
        relative = path.relative_to(REPO_ROOT).as_posix()
        if relative in PUBLIC_SURFACE_TESTS:
            continue
        if _imports_runtime_root(path):
            violations.append(relative)

    assert violations == []
