from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Any, cast

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
WORKSPACE_TOOL = "bijux_proteomics"


def _root_pyproject() -> dict[str, Any]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def _table(payload: object) -> dict[str, Any]:
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def _string_list(payload: object) -> list[str]:
    assert isinstance(payload, list)
    return [str(entry) for entry in payload]


def test_root_pyproject_keeps_distribution_builds_in_workspace_packages() -> None:
    pyproject = _root_pyproject()
    assert "project" not in pyproject
    assert "build-system" not in pyproject
    assert "hatch" not in pyproject["tool"]
    uv_workspace = _table(_table(_table(pyproject["tool"])["uv"])["workspace"])
    assert _string_list(uv_workspace["members"]) == ["packages/*"]
    names = []
    for path in sorted((REPO_ROOT / "packages").glob("*/pyproject.toml")):
        package = tomllib.loads(path.read_text())
        names.append(package["project"]["name"])
        assert "build-system" in package
    workspace_packages = _table(_table(pyproject["tool"])[WORKSPACE_TOOL])["packages"]
    assert set(names) == set(workspace_packages)
    assert len(names) == len(set(names))


def test_root_pyproject_exposes_all_workspace_packages_to_root_dev_installs() -> None:
    pyproject = _root_pyproject()
    workspace_packages = set(
        _string_list(_table(_table(pyproject["tool"])[WORKSPACE_TOOL])["packages"])
    )
    dev_group = _string_list(_table(pyproject["dependency-groups"])["dev"])
    dev_group_entries = {entry.split("[", 1)[0] for entry in dev_group}

    assert dev_group_entries.issuperset(workspace_packages)


def test_root_pyproject_exposes_all_workspace_packages_to_root_test_installs() -> None:
    pyproject = _root_pyproject()
    workspace_packages = set(
        _string_list(_table(_table(pyproject["tool"])[WORKSPACE_TOOL])["packages"])
    )
    test_group = _string_list(_table(pyproject["dependency-groups"])["test"])
    test_group_entries = {entry.split("[", 1)[0] for entry in test_group}

    assert test_group_entries == workspace_packages


def test_root_pyproject_uses_workspace_sources_for_every_workspace_package() -> None:
    pyproject = _root_pyproject()
    workspace_packages = set(
        _string_list(_table(_table(pyproject["tool"])[WORKSPACE_TOOL])["packages"])
    )
    uv_sources = _table(_table(pyproject["tool"])["uv"])["sources"]
    assert isinstance(uv_sources, dict)

    assert set(uv_sources) == workspace_packages
    assert {
        name for name, config in uv_sources.items() if config == {"workspace": True}
    } == (workspace_packages)
