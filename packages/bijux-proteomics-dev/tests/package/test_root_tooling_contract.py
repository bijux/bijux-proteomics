from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path
import tomllib
from typing import Any, cast

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _mypy_config() -> ConfigParser:
    parser = ConfigParser()
    parser.read(REPO_ROOT / "configs" / "mypy.ini", encoding="utf-8")
    return parser


def _root_pyproject() -> dict[str, Any]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def _table(payload: object) -> dict[str, Any]:
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def _tox_config() -> ConfigParser:
    parser = ConfigParser()
    parser.read(REPO_ROOT / "tox.ini", encoding="utf-8")
    return parser


def test_root_mypy_configuration_uses_namespace_packages() -> None:
    assert _mypy_config()["mypy"]["namespace_packages"] == "true"


def test_root_pyproject_declares_documented_quality_tooling() -> None:
    tool_section = _table(_root_pyproject()["tool"])
    interrogate = tool_section["interrogate"]
    assert interrogate["fail-under"] == 45
    assert interrogate["color"] is True


def test_root_tox_configuration_redirects_state_into_root_artifacts() -> None:
    tox_config = _tox_config()

    assert tox_config["tox"]["toxworkdir"] == "{tox_root}/artifacts/root/tox"


def test_root_pyproject_declares_documented_security_tooling() -> None:
    tool_section = _table(_root_pyproject()["tool"])
    bandit = tool_section["bandit"]
    assert bandit["skips"] == ["B404", "B311"]
    assert bandit["exclude_dirs"] == [
        ".venv",
        "tests",
        "artifacts",
        ".pytest_cache",
        ".ruff_cache",
    ]


def test_root_pyproject_declares_repo_owned_optional_dependency_groups() -> None:
    dependency_groups = _root_pyproject()["dependency-groups"]
    assert isinstance(dependency_groups, dict)
    assert set(dependency_groups) == {
        "test",
        "dev",
        "api",
        "local-esmfold",
        "local-rosettafold",
        "nl",
    }
    assert any(str(entry).startswith("pyright>=") for entry in dependency_groups["dev"])


def test_root_make_declares_documented_repository_extensions() -> None:
    root_make = (REPO_ROOT / "makes" / "root.mk").read_text(encoding="utf-8")

    assert "ensure-venv:" in root_make
    assert "nlenv:" in root_make
    assert "manage_examples:" in root_make
    assert "manage_models:" in root_make
    assert "api-freeze:" in root_make
    assert "openapi-drift:" in root_make
    assert "quality-public-api-types:" in root_make
    assert "quality-circular-imports:" in root_make
    assert "quality-core-dependency-minimization:" in root_make
    assert "$(MAKE) quality-public-api-types" in root_make
    assert "$(MAKE) quality-circular-imports" in root_make
    assert "$(MAKE) quality-core-dependency-minimization" in root_make
