from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Any, cast

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _deptry_config() -> dict[str, Any]:
    with (REPO_ROOT / "configs" / "deptry.toml").open("rb") as handle:
        return tomllib.load(handle)


def _root_pyproject() -> dict[str, Any]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def _table(payload: object) -> dict[str, Any]:
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def _string_list(payload: object) -> list[str]:
    assert isinstance(payload, list)
    return [str(entry) for entry in payload]


def test_root_deptry_configuration_uses_supported_dev_group_contract() -> None:
    deptry_config = _table(_table(_deptry_config()["tool"])["deptry"])

    assert _string_list(deptry_config["optional_dependencies_dev_groups"]) == ["dev"]
    assert "pep621_dev_dependency_groups" not in deptry_config


def test_root_deptry_configuration_maps_all_workspace_distributions() -> None:
    deptry_config = _table(_table(_deptry_config()["tool"])["deptry"])
    workspace_packages = _string_list(
        _table(_table(_root_pyproject()["tool"])["bijux_proteomics"])["packages"]
    )

    module_map = _table(deptry_config["package_module_name_map"])
    assert set(workspace_packages).issubset(module_map)
    assert module_map["bijux-proteomics-runtime"] == "bijux_proteomics_runtime"
    assert module_map["bijux-proteomics-dev"] == "bijux_proteomics_dev"
    assert module_map["langchain-text-splitters"] == "langchain_text_splitters"
    assert module_map["langsmith"] == "langsmith"
    assert module_map["openapi-spec-validator"] == "openapi_spec_validator"


def test_root_deptry_configuration_covers_every_workspace_package_override() -> None:
    root_pyproject = _root_pyproject()
    workspace_packages = set(
        _string_list(
            _table(_table(root_pyproject["tool"])["bijux_proteomics"])["packages"]
        )
    )
    package_overrides = set(
        _table(_table(_deptry_config()["tool"])["repo_deptry"])["packages"]
    )

    assert package_overrides == workspace_packages
