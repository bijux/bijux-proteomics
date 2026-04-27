from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[3]


def _workspace_metadata() -> dict[str, Any]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    return cast(dict[str, Any], data["tool"]["bijux_proteomics"])


def _package_names() -> list[str]:
    workspace = _workspace_metadata()
    return list(cast(list[str], workspace["packages"]))


def _package_dir(package_name: str) -> Path:
    return REPO_ROOT / "packages" / package_name


def _import_root(package_name: str) -> str:
    if package_name == "bijux-proteomics-core":
        return "bijux_proteomics"
    return package_name.replace("-", "_")


def test_workspace_packages_expose_contract_docs() -> None:
    missing = [
        path.relative_to(REPO_ROOT).as_posix()
        for package_name in _package_names()
        for path in [_package_dir(package_name) / "docs" / "CONTRACTS.md"]
        if not path.exists()
    ]
    assert not missing, "missing package contract docs:\n" + "\n".join(missing)


def test_contract_docs_share_identity_and_change_sections() -> None:
    failures: list[str] = []

    for package_name in _package_names():
        path = _package_dir(package_name) / "docs" / "CONTRACTS.md"
        text = path.read_text(encoding="utf-8")
        expected_bits = [
            "## Public package identity",
            f"- Distribution name: `{package_name}`",
            f"- Import root: `{_import_root(package_name)}`",
            "## Stable contracts",
            "## Change requirements",
            "## Consumer upgrade expectations",
            "## Change routing signals",
            "## Validation checkpoints",
            "## Explicit non-contracts",
        ]
        missing = [bit for bit in expected_bits if bit not in text]
        if missing:
            failures.append(
                f"{path.relative_to(REPO_ROOT).as_posix()}: missing {', '.join(missing)}"
            )

    assert not failures, "package contract docs contract failed:\n" + "\n".join(
        failures
    )


def test_package_readmes_share_identity_boundary_and_docs_sections() -> None:
    failures: list[str] = []

    for package_name in _package_names():
        path = _package_dir(package_name) / "README.md"
        text = path.read_text(encoding="utf-8")
        expected_bits = [
            "## Package identity",
            f"- Distribution name: `{package_name}`",
            f"- Import root: `{_import_root(package_name)}`",
            "## Package boundaries",
            "## Contract checkpoints",
            "## Choose this package when",
            "## Route elsewhere when",
            "## Documentation",
        ]
        missing = [bit for bit in expected_bits if bit not in text]
        if missing:
            failures.append(
                f"{path.relative_to(REPO_ROOT).as_posix()}: missing {', '.join(missing)}"
            )

    assert not failures, "package README contract failed:\n" + "\n".join(failures)
