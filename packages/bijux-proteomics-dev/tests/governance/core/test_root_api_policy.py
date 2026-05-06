from __future__ import annotations

from pathlib import Path
import tomllib

import bijux_proteomics


REPO_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "packages").is_dir() and (parent / "configs").is_dir())
CORE_ROOT = (
    REPO_ROOT
    / "packages"
    / "bijux-proteomics-core"
    / "src"
    / "bijux_proteomics"
    / "__init__.py"
)
CORE_ROOT_API_POLICY = (
    REPO_ROOT / "configs" / "package-governance" / "core-root-api.toml"
)


def _policy() -> dict[str, object]:
    return tomllib.loads(CORE_ROOT_API_POLICY.read_text(encoding="utf-8"))


def test_core_root_api_matches_curated_policy() -> None:
    policy = _policy()
    entries = policy["symbol"]

    assert [entry["name"] for entry in entries] == list(bijux_proteomics.__all__)
    assert all(entry["owner_module"] for entry in entries)
    assert all(entry["classification"] for entry in entries)
    assert all(entry["rationale"] for entry in entries)


def test_core_root_api_stays_within_budget() -> None:
    policy = _policy()
    budget = policy["budget"]
    init_lines = CORE_ROOT.read_text(encoding="utf-8").splitlines()

    assert len(bijux_proteomics.__all__) <= budget["max_public_symbols"]
    assert len(init_lines) <= budget["max_init_lines"]


def test_core_root_api_excludes_removed_convenience_exports() -> None:
    removed = {
        "ExperimentalDesignEntry",
        "ProgramSpec",
        "SearchAdapterKind",
        "SpectrumModel",
        "WorkflowTemplateKind",
    }

    assert removed.isdisjoint(bijux_proteomics.__all__)
