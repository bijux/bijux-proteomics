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


def _config_parser(path: Path) -> ConfigParser:
    parser = ConfigParser()
    parser.read(path, encoding="utf-8")
    return parser


def _ruff_config() -> dict[str, Any]:
    with (REPO_ROOT / "configs" / "ruff.toml").open("rb") as handle:
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


def _package_roots(kind: str) -> set[str]:
    return {
        path.relative_to(REPO_ROOT).as_posix()
        for path in (REPO_ROOT / "packages").glob(f"*/{kind}")
    }


def _package_source_roots() -> list[str]:
    return sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in (REPO_ROOT / "packages").glob("*/src")
    )


def _package_import_roots() -> set[str]:
    import_roots: set[str] = set()
    for source_dir in (REPO_ROOT / "packages").glob("*/src"):
        import_roots.update(
            child.name for child in source_dir.iterdir() if child.is_dir()
        )
    return import_roots


def test_root_pytest_configuration_matches_shared_python_baseline() -> None:
    pytest_config = _config_parser(REPO_ROOT / "configs" / "pytest.ini")["pytest"]

    assert pytest_config["minversion"] == "8.0"
    assert pytest_config["python_files"] == "test_*.py"
    assert pytest_config["python_classes"] == "Test*"
    assert pytest_config["python_functions"] == "test_*"
    assert pytest_config["asyncio_mode"] == "auto"
    assert pytest_config["timeout"] == "120"
    assert pytest_config["timeout_method"] == "thread"
    assert pytest_config["timeout_func_only"] == "true"
    assert pytest_config["xfail_strict"] == "true"
    assert pytest_config["cache_dir"] == "artifacts/root/pytest-cache"

    assert {
        line.strip()
        for line in pytest_config["norecursedirs"].splitlines()
        if line.strip()
    } == {
        ".venv",
        ".tox",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        ".hypothesis",
        ".benchmarks",
        "build",
        "dist",
        "htmlcov",
        "docs",
        "artifacts",
        "node_modules",
        "site",
    }
    assert [
        line.strip() for line in pytest_config["addopts"].splitlines() if line.strip()
    ] == [
        "-ra",
        "--import-mode=importlib",
        "--strict-markers",
        "--tb=short",
    ]
    assert {
        line.strip() for line in pytest_config["markers"].splitlines() if line.strip()
    } == {
        "api: HTTP API tests (manual, not for CI)",
        "benchmark: performance and benchmark-oriented tests",
        "e2e: end-to-end tests",
        "evaluation: evaluation benchmarks (deterministic, no regressions)",
        "external_data: tests that exercise checked-in external corpora and bundles",
        "governance: repository governance and inventory freshness tests",
        "gpu: requires CUDA",
        "integration: integration tests",
        "live: live provider integration",
        "real: real local model tests (slow, manual, not for CI)",
        "real_local: requires local models or hardware",
        "regression: regression tests",
        "slow: mark test as slow",
        "smoke: smoke tests",
        "unit: unit tests",
        "windows: mark tests for Windows-only",
    }
    assert [
        line.strip()
        for line in pytest_config["filterwarnings"].splitlines()
        if line.strip()
    ] == [
        "ignore:Not saving anything, no benchmarks have been run!",
        "ignore:jsonschema\\.exceptions\\.RefResolutionError is deprecated:DeprecationWarning",
        "ignore:jsonschema\\.exceptions\\.RefResolutionError is deprecated:DeprecationWarning:schemathesis.generation.coverage",
        "ignore:.*forkpty.*:DeprecationWarning",
        "ignore::Bio.BiopythonDeprecationWarning",
        "ignore:datetime\\.datetime\\.utcnow\\(\\) is deprecated:DeprecationWarning",
        "ignore:'asyncio\\.iscoroutinefunction' is deprecated:DeprecationWarning",
        "ignore:'asyncio\\.get_event_loop_policy' is deprecated:DeprecationWarning",
        "ignore:'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated:DeprecationWarning:anyio._backends._asyncio",
    ]


def test_repo_root_pytest_entrypoint_matches_shared_python_baseline() -> None:
    shared_config = _config_parser(REPO_ROOT / "configs" / "pytest.ini")["pytest"]
    root_pytest = _root_pyproject()["tool"]["pytest"]["ini_options"]

    assert root_pytest["minversion"] == shared_config["minversion"]
    assert root_pytest["testpaths"] == [
        line.strip() for line in shared_config["testpaths"].splitlines() if line.strip()
    ]
    assert sorted(root_pytest["pythonpath"]) == _package_source_roots()
    assert root_pytest["python_files"] == [shared_config["python_files"]]
    assert root_pytest["python_classes"] == [shared_config["python_classes"]]
    assert root_pytest["python_functions"] == [shared_config["python_functions"]]
    assert root_pytest["asyncio_mode"] == shared_config["asyncio_mode"]
    assert root_pytest["cache_dir"] == shared_config["cache_dir"]
    assert root_pytest["timeout"] == int(shared_config["timeout"])
    assert root_pytest["timeout_method"] == shared_config["timeout_method"]
    assert root_pytest["timeout_func_only"] is True
    assert root_pytest["xfail_strict"] is True
    assert root_pytest["norecursedirs"] == [
        line.strip()
        for line in shared_config["norecursedirs"].splitlines()
        if line.strip()
    ]
    assert root_pytest["addopts"] == [
        line.strip() for line in shared_config["addopts"].splitlines() if line.strip()
    ]
    assert root_pytest["markers"] == [
        line.strip() for line in shared_config["markers"].splitlines() if line.strip()
    ]
    assert root_pytest["filterwarnings"] == [
        line.strip()
        for line in shared_config["filterwarnings"].splitlines()
        if line.strip()
    ]


def test_root_ruff_configuration_matches_shared_python_baseline() -> None:
    ruff_config = _ruff_config()

    assert ruff_config["target-version"] == "py311"
    assert ruff_config["line-length"] == 88
    assert ruff_config["respect-gitignore"] is True
    assert ruff_config["cache-dir"] == "artifacts/root/ruff-cache"
    assert set(_string_list(ruff_config["src"])) == _package_roots(
        "src"
    ) | _package_roots("tests")
    exclude_entries = set(_string_list(ruff_config["exclude"]))
    assert {
        ".git",
        ".hg",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "artifacts",
        "build",
        "dist",
        "docs/report",
        "htmlcov",
        "migrations",
        "node_modules",
        "*.egg-info",
        "site",
    } <= exclude_entries

    lint = _table(ruff_config["lint"])
    assert _string_list(lint["select"]) == [
        "E",
        "F",
        "I",
        "B",
        "UP",
        "SIM",
        "C4",
        "PIE",
        "RET",
        "ISC",
    ]
    assert _string_list(lint["ignore"]) == ["E501", "E203"]
    assert lint["per-file-ignores"] == {"__init__.py": ["F401"]}
    assert _table(lint["isort"])["force-sort-within-sections"] is True
    assert set(
        _string_list(_table(lint["isort"])["known-first-party"])
    ) == _package_import_roots() | {"tests"}
    assert _table(lint["mccabe"])["max-complexity"] == 10


def test_root_mypy_configuration_matches_shared_python_baseline() -> None:
    mypy_config = _config_parser(REPO_ROOT / "configs" / "mypy.ini")
    root_mypy = mypy_config["mypy"]

    assert root_mypy["python_version"] == "3.11"
    assert root_mypy["strict"] == "true"
    assert root_mypy["pretty"] == "true"
    assert root_mypy["show_error_codes"] == "true"
    assert root_mypy["warn_unreachable"] == "true"
    assert root_mypy["warn_unused_configs"] == "true"
    assert root_mypy["warn_unused_ignores"] == "true"
    assert root_mypy["namespace_packages"] == "true"
    assert root_mypy["plugins"] == "pydantic.mypy"
    assert root_mypy["exclude"].startswith(
        "^(\\.venv|build|dist|docs|htmlcov|\\.mypy_cache|\\.pytest_cache|"
    )
    assert "\\.ruff_cache|" in root_mypy["exclude"]
    assert "\\.tox|" in root_mypy["exclude"]
    assert "migrations|" in root_mypy["exclude"]
    assert "\\.egg-info|" in root_mypy["exclude"]
    assert "node_modules|" in root_mypy["exclude"]
    assert "artifacts|site)/" in root_mypy["exclude"]

    configured_files = {
        entry.strip() for entry in root_mypy["files"].split(",") if entry.strip()
    }
    assert configured_files == _package_roots("src") | _package_roots("tests")

    configured_paths = {
        entry.strip() for entry in root_mypy["mypy_path"].split(":") if entry.strip()
    }
    assert configured_paths == _package_roots("src")

    assert mypy_config["mypy-agentic_proteins.*"]["ignore_errors"] == "true"
    assert mypy_config["mypy-openprotein"]["ignore_missing_imports"] == "true"
    assert mypy_config["mypy-torch"]["ignore_missing_imports"] == "true"
    assert mypy_config["mypy-transformers"]["ignore_missing_imports"] == "true"


def test_public_api_mypy_configuration_matches_curated_public_contract() -> None:
    mypy_config = _config_parser(REPO_ROOT / "configs" / "mypy-public-api.ini")
    public_mypy = mypy_config["mypy"]

    assert public_mypy["python_version"] == "3.11"
    assert public_mypy["strict"] == "true"
    assert public_mypy["namespace_packages"] == "true"
    assert public_mypy["plugins"] == "pydantic.mypy"
    configured_paths = {
        entry.strip() for entry in public_mypy["mypy_path"].split(":") if entry.strip()
    }
    assert configured_paths == set(_package_source_roots())
