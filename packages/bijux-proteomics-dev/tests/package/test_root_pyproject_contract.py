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


def test_root_pyproject_uses_shared_workspace_build_contract() -> None:
    pyproject = _root_pyproject()

    assert pyproject["build-system"] == {
        "requires": ["hatchling>=1.27.0,<1.31", "hatch-vcs>=0.4.0,<1.0"],
        "build-backend": "hatchling.build",
    }

    project = _table(pyproject["project"])
    assert _string_list(project["dynamic"]) == ["version"]
    assert "version" not in project

    hatch_version = _table(_table(_table(pyproject["tool"])["hatch"])["version"])
    assert hatch_version["source"] == "vcs"
    assert hatch_version["tag-pattern"] == "^v(?P<version>.*)$"

    uv_workspace = _table(_table(_table(pyproject["tool"])["uv"])["workspace"])
    assert _string_list(uv_workspace["members"]) == ["packages/*"]
    hatch_wheel = _table(
        _table(_table(_table(pyproject["tool"])["hatch"])["build"])["targets"]
    )["wheel"]
    assert hatch_wheel == {"bypass-selection": True}


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
