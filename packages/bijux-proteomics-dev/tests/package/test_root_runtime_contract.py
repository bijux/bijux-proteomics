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
    assert "ROOT_PACKAGE_TARGETS += test-all test-all-plus-run-time" in root_make
    assert "ROOT_TARGET_GROUPS_test-all ?= check" in root_make
    assert "ROOT_TARGET_GROUPS_test-all-plus-run-time ?= check" in root_make
    assert "sync-badges:" in root_make
    assert "check-badges:" in root_make
    assert "ensure-venv:" in root_make
    assert "nlenv:" in root_make
    assert "manage_examples:" in root_make
    assert "manage_models:" in root_make
    assert "api-freeze:" in root_make
    assert "openapi-drift:" in root_make
    assert "quality-circular-imports:" in root_make


def test_repository_python_package_profiles_expose_full_test_surfaces() -> None:
    package_make = (REPO_ROOT / "makes" / "proteomics-package.mk").read_text(
        encoding="utf-8"
    )

    assert (
        'TEST_MAIN_ARGS ?= -m "unit and not slow and not benchmark and not external_data and not real_local and not api"'
        in package_make
    )
    assert "test-all: TEST_MAIN_ARGS =" in package_make
    assert "test-all: PYTEST_ADDOPTS_EXTRA = -o timeout=0" in package_make
    assert "test-all: test" in package_make
    assert "test-all-plus-run-time: TEST_MAIN_ARGS =" in package_make
    assert (
        "test-all-plus-run-time: PYTEST_ADDOPTS_EXTRA = -o timeout=0 --durations=0 --durations-min=0"
        in package_make
    )
    assert "test-all-plus-run-time: test" in package_make
    assert 'test-slow: TEST_MAIN_ARGS = -m "slow or benchmark or external_data"' in package_make
    assert "test-slow: test" in package_make


def test_dev_package_profile_exposes_full_test_surfaces() -> None:
    package_make = (
        REPO_ROOT / "makes" / "packages" / "bijux-proteomics-dev.mk"
    ).read_text(encoding="utf-8")

    assert (
        'TEST_MAIN_ARGS := -m "unit and not slow and not benchmark and not external_data"'
        in package_make
    )
    assert "test-all: TEST_MAIN_ARGS =" in package_make
    assert "test-all: PYTEST_ADDOPTS_EXTRA = -o timeout=0" in package_make
    assert "test-all: test" in package_make
    assert "test-all-plus-run-time: TEST_MAIN_ARGS =" in package_make
    assert (
        "test-all-plus-run-time: PYTEST_ADDOPTS_EXTRA = -o timeout=0 --durations=0 --durations-min=0"
        in package_make
    )
    assert "test-all-plus-run-time: test" in package_make


def test_shared_python_test_runner_defines_fast_and_slow_marker_filters() -> None:
    shared_test_make = (
        REPO_ROOT / "makes" / "bijux-py" / "ci" / "test.mk"
    ).read_text(encoding="utf-8")

    assert (
        'TEST_UNIT_DIR_ARGS        ?= -m "unit and not slow and not benchmark and not external_data" --maxfail=1 -q'
        in shared_test_make
    )
    assert (
        'TEST_UNIT_FALLBACK_ARGS   ?= -m "unit and not slow and not benchmark and not external_data" --maxfail=1 -q'
        in shared_test_make
    )
    assert (
        'TEST_SLOW_ARGS            ?= -m "slow or benchmark or external_data" --maxfail=1 -q'
        in shared_test_make
    )
    assert "test-slow:" in shared_test_make
