from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path
import tomllib

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _mypy_config() -> ConfigParser:
    parser = ConfigParser()
    parser.read(REPO_ROOT / "configs" / "mypy.ini", encoding="utf-8")
    return parser


def _root_pyproject() -> dict[str, object]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def test_root_mypy_configuration_uses_namespace_packages() -> None:
    assert _mypy_config()["mypy"]["namespace_packages"] == "true"


def test_root_pyproject_declares_documented_quality_tooling() -> None:
    tool_section = _root_pyproject()["tool"]
    interrogate = tool_section["interrogate"]
    assert interrogate["fail-under"] == 32
    assert interrogate["color"] is True


def test_root_pyproject_declares_documented_security_tooling() -> None:
    tool_section = _root_pyproject()["tool"]
    bandit = tool_section["bandit"]
    assert bandit["skips"] == ["B404", "B311"]
    assert bandit["exclude_dirs"] == [
        ".venv",
        "tests",
        "artifacts",
        ".pytest_cache",
        ".ruff_cache",
    ]
