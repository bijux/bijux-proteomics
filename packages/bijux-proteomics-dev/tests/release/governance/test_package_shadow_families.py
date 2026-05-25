from __future__ import annotations

from pathlib import Path
import tomllib

from bijux_proteomics_dev.governance.dependencies.package_responsibility_map import (
    build_package_responsibility_map_report,
)
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    package_root,
    src_root,
)


def _package_description(package_name: str) -> str:
    with (package_root(package_name) / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    return str(data["project"]["description"]).lower()


def test_shadow_package_families_keep_declared_purpose() -> None:
    report = build_package_responsibility_map_report()
    by_package = {entry.distribution_name: entry for entry in report.entries}

    expected_roles = {
        "agentic-proteins": "compatibility_bridge",
        "bijux-proteomics": "app_wrapper",
        "proteomics": "short_alias",
        "proteomics-core": "short_alias",
        "proteomics-foundation": "short_alias",
        "proteomics-intelligence": "short_alias",
        "proteomics-knowledge": "short_alias",
        "proteomics-lab": "short_alias",
        "proteomics-runtime": "short_alias",
    }
    for package_name, responsibility_kind in expected_roles.items():
        assert by_package[package_name].responsibility_kind == responsibility_kind

    assert "compatibility bridge" in _package_description("agentic-proteins")
    assert "alias package" in _package_description("bijux-proteomics")
    for package_name in (
        "proteomics",
        "proteomics-core",
        "proteomics-foundation",
        "proteomics-intelligence",
        "proteomics-knowledge",
        "proteomics-lab",
        "proteomics-runtime",
    ):
        assert "alias package" in _package_description(package_name)


def test_thin_alias_packages_only_keep_wrapper_source_files() -> None:
    expected_files = {
        "bijux-proteomics": {"__init__.py", "py.typed"},
        "proteomics": {"__init__.py", "__main__.py", "cli.py", "py.typed"},
        "proteomics-core": {"__init__.py", "__main__.py", "cli.py", "py.typed"},
        "proteomics-foundation": {"__init__.py", "py.typed"},
        "proteomics-intelligence": {"__init__.py", "py.typed"},
        "proteomics-knowledge": {"__init__.py", "py.typed"},
        "proteomics-lab": {"__init__.py", "py.typed"},
        "proteomics-runtime": {"__init__.py", "__main__.py", "cli.py", "py.typed"},
    }

    for package_name, expected in expected_files.items():
        observed = {
            path.relative_to(src_root(package_name)).as_posix()
            for path in src_root(package_name).rglob("*")
            if path.is_file() and "__pycache__" not in Path(path).parts
        }
        assert observed == expected
        assert "runtime_alias.py" not in observed
