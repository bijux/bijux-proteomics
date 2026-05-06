from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Any, cast

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _workspace_metadata() -> dict[str, Any]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    return cast(dict[str, Any], data["tool"]["bijux_proteomics"])


def _package_names() -> list[str]:
    workspace = _workspace_metadata()
    return list(cast(list[str], workspace["packages"]))


def _package_dir(package_name: str) -> Path:
    return REPO_ROOT / "packages" / package_name


def _release_doc_packages() -> list[str]:
    return [
        package_name
        for package_name in _package_names()
        if (_package_dir(package_name) / "docs" / "maintainer" / "pypi.md").exists()
    ]


def _section(text: str, heading: str) -> str:
    marker = f"## {heading}\n"
    start = text.find(marker)
    assert start >= 0, f"missing section heading: {heading}"
    start += len(marker)
    end = text.find("\n## ", start)
    if end < 0:
        end = len(text)
    return text[start:end]


def _bullet_count(section: str) -> int:
    return sum(1 for line in section.splitlines() if line.startswith("- "))


def test_maintainer_release_docs_keep_communication_guidance_substantive() -> None:
    failures: list[str] = []

    for package_name in _release_doc_packages():
        path = _package_dir(package_name) / "docs" / "maintainer" / "pypi.md"
        text = path.read_text(encoding="utf-8")
        communication_section = _section(text, "Release communication signals")
        if _bullet_count(communication_section) < 3:
            failures.append(
                f"{path.relative_to(REPO_ROOT).as_posix()}: release communication section needs at least three bullets"
            )

    index_path = REPO_ROOT / "packages" / "bijux-proteomics-dev" / "docs" / "index.md"
    index_text = index_path.read_text(encoding="utf-8")
    if _bullet_count(_section(index_text, "Release communication signals")) < 3:
        failures.append(
            f"{index_path.relative_to(REPO_ROOT).as_posix()}: release communication section needs at least three bullets"
        )

    assert not failures, (
        "maintainer release communication guidance failed:\n" + "\n".join(failures)
    )
