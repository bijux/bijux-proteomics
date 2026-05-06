from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Any, cast

REPO_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "packages").is_dir() and (parent / "configs").is_dir())


def _workspace_metadata() -> dict[str, Any]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    return cast(dict[str, Any], data["tool"]["bijux_proteomics"])


def _package_names() -> list[str]:
    workspace = _workspace_metadata()
    return list(cast(list[str], workspace["packages"]))


def _package_dir(package_name: str) -> Path:
    return REPO_ROOT / "packages" / package_name


def _boundary_doc_path(package_name: str) -> Path:
    package_dir = _package_dir(package_name)
    if package_name == "bijux-proteomics-dev":
        return package_dir / "docs" / "SCOPE.md"
    return package_dir / "docs" / "BOUNDARIES.md"


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


def test_package_boundary_docs_keep_escalation_guidance_substantive() -> None:
    failures: list[str] = []

    for package_name in _package_names():
        path = _boundary_doc_path(package_name)
        text = path.read_text(encoding="utf-8")

        escalation_section = _section(text, "Escalation signals")
        if _bullet_count(escalation_section) < 3:
            failures.append(
                f"{path.relative_to(REPO_ROOT).as_posix()}: escalation section needs at least three bullets"
            )

        if package_name == "bijux-proteomics-runtime":
            failure_section = _section(text, "Boundary failure signals")
            if _bullet_count(failure_section) < 3:
                failures.append(
                    f"{path.relative_to(REPO_ROOT).as_posix()}: boundary failure section needs at least three bullets"
                )

    assert not failures, "package boundary escalation guidance failed:\n" + "\n".join(
        failures
    )
