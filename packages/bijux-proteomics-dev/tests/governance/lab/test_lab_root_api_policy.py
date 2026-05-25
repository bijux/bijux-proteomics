from __future__ import annotations

import ast
from pathlib import Path
import tomllib
from typing import Any, cast

import pytest

import bijux_proteomics_lab

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
LAB_ROOT = (
    REPO_ROOT / "packages" / "bijux-proteomics-lab" / "src" / "bijux_proteomics_lab"
)
LAB_ROOT_INIT = LAB_ROOT / "__init__.py"
LAB_ROOT_API_POLICY = REPO_ROOT / "configs" / "package-governance" / "lab-root-api.toml"
PUBLIC_SURFACE_TESTS = {
    "packages/bijux-proteomics-dev/tests/governance/lab/test_lab_root_api_policy.py",
    "packages/bijux-proteomics-lab/tests/handoffs/test_artifact_contracts_surface.py",
    "packages/bijux-proteomics-lab/tests/handoffs/test_artifact_serialization_surface.py",
    "packages/bijux-proteomics-lab/tests/package/test_package_operational_guards.py",
    "packages/bijux-proteomics-lab/tests/package/test_public_api_surface.py",
    "packages/proteomics-lab/tests/compatibility/test_proteomics_lab_alias.py",
}


def _policy() -> dict[str, Any]:
    return tomllib.loads(LAB_ROOT_API_POLICY.read_text(encoding="utf-8"))


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


def _imports_lab_root(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "bijux_proteomics_lab":
                    return True
        if isinstance(node, ast.ImportFrom) and node.module == "bijux_proteomics_lab":
            return True
    return False


def test_lab_root_api_matches_curated_policy() -> None:
    policy = _policy()
    entries = _symbol_entries(policy)

    assert [entry["name"] for entry in entries] == list(bijux_proteomics_lab.__all__)
    assert all(entry["owner_module"] for entry in entries)
    assert all(entry["classification"] for entry in entries)
    assert all(entry["rationale"] for entry in entries)


def test_lab_root_api_stays_within_budget() -> None:
    policy = _policy()
    budget = _budget(policy)
    init_lines = LAB_ROOT_INIT.read_text(encoding="utf-8").splitlines()

    assert len(bijux_proteomics_lab.__all__) <= budget["max_public_symbols"]
    assert len(init_lines) <= budget["max_init_lines"]


def test_lab_root_excludes_convenience_only_exports() -> None:
    removed = {
        "AssayLifecycleStage",
        "OperationalReadinessReport",
        "TargetedBenchmarkReport",
        "build_lims_export_bundle",
        "recommend_rerun_policy",
    }

    assert removed.isdisjoint(bijux_proteomics_lab.__all__)


@pytest.mark.slow
def test_lab_root_is_not_used_outside_public_surface_checks() -> None:
    violations: list[str] = []
    for path in sorted((REPO_ROOT / "packages").rglob("*.py")):
        relative = path.relative_to(REPO_ROOT).as_posix()
        if relative in PUBLIC_SURFACE_TESTS:
            continue
        if _imports_lab_root(path):
            violations.append(relative)

    assert violations == []
