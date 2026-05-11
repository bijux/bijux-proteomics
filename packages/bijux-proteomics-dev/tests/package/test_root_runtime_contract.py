from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _tox_config() -> ConfigParser:
    parser = ConfigParser()
    parser.read(REPO_ROOT / "tox.ini", encoding="utf-8")
    return parser


def _envlist() -> set[str]:
    envlist = _tox_config()["tox"]["envlist"]
    return {line.strip() for line in envlist.splitlines() if line.strip()}


def test_root_tox_keeps_shared_env_families_and_treats_special_commands_as_make_only() -> (
    None
):
    envlist = _envlist()

    assert "security" in envlist
    assert "docs" in envlist
    assert (
        "fmt-{dev,runtime,core,foundation,intelligence,knowledge,lab,agentic}"
        not in envlist
    )
    assert "api-freeze-core" not in envlist
    assert "openapi-drift-core" not in envlist


def test_root_make_declares_shared_and_repo_owned_maintainer_commands() -> None:
    root_make = (REPO_ROOT / "makes" / "root.mk").read_text(encoding="utf-8")

    assert "check:" in root_make
    assert "sync-badges:" in root_make
    assert "check-badges:" in root_make
    assert "ensure-venv:" in root_make
    assert "nlenv:" in root_make
    assert "manage_examples:" in root_make
    assert "manage_models:" in root_make
    assert "api-freeze:" in root_make
    assert "openapi-drift:" in root_make
