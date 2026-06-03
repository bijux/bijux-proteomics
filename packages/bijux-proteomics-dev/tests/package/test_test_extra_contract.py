from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Any, cast

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _root_pyproject() -> dict[str, Any]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def _package_pyproject(package_name: str) -> dict[str, Any]:
    with (REPO_ROOT / "packages" / package_name / "pyproject.toml").open(
        "rb"
    ) as handle:
        return tomllib.load(handle)


def _table(payload: object) -> dict[str, Any]:
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def _string_list(payload: object) -> list[str]:
    assert isinstance(payload, list)
    return [str(entry) for entry in payload]


def test_root_test_dependency_group_routes_through_package_test_surfaces() -> None:
    test_group = _string_list(_table(_root_pyproject()["dependency-groups"])["test"])
    expected_entries = {
        "agentic-proteins[test]",
        "bijux-proteomics-dev[test]",
        "bijux-proteomics-foundation[test]",
        "bijux-proteomics-core[test]",
        "bijux-proteomics-runtime[test]",
        "bijux-proteomics-knowledge[test]",
    }

    assert expected_entries.issubset(set(test_group))


def test_package_test_extras_cover_owned_optional_test_dependencies() -> None:
    expected = {
        "agentic-proteins": {
            "pytest>=8.4.1,<10.0",
            "pytest-asyncio>=1.0.0,<2.0",
            "pytest-timeout>=2.4.0,<3.0",
            "httpx>=0.27.0,<1.0",
        },
        "bijux-proteomics-core": {
            "pytest>=8.4.1,<10.0",
            "pytest-asyncio>=1.0.0,<2.0",
            "pytest-benchmark>=4.0.0,<6.0",
            "pytest-timeout>=2.4.0,<3.0",
        },
        "bijux-proteomics-dev": {
            "pytest>=9.0.3,<10.0",
            "pytest-asyncio>=1.0.0,<2.0",
            "pytest-timeout>=2.4.0,<3.0",
        },
        "bijux-proteomics-foundation": {
            "biopython>=1.86,<2.0",
            "pytest>=8.4.1,<10.0",
            "pytest-asyncio>=1.0.0,<2.0",
            "pytest-benchmark>=4.0.0,<6.0",
            "pytest-timeout>=2.4.0,<3.0",
            "hypothesis>=6.103.0,<7.0",
        },
        "bijux-proteomics-knowledge": {
            "pytest>=8.4.1,<10.0",
            "pytest-asyncio>=1.0.0,<2.0",
            "pytest-benchmark>=4.0.0,<6.0",
            "pytest-timeout>=2.4.0,<3.0",
        },
        "bijux-proteomics-runtime": {
            "pytest>=8.4.1,<10.0",
            "pytest-asyncio>=1.0.0,<2.0",
            "pytest-benchmark>=4.0.0,<6.0",
            "pytest-timeout>=2.4.0,<3.0",
            "httpx>=0.27.0,<1.0",
        },
    }

    for package_name, expected_dependencies in expected.items():
        optional_dependencies = _table(
            _table(_package_pyproject(package_name)["project"])["optional-dependencies"]
        )
        assert set(_string_list(optional_dependencies["test"])) == expected_dependencies
