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


def test_package_readmes_keep_escalation_guidance_substantive() -> None:
    failures: list[str] = []

    for package_name in _package_names():
        path = _package_dir(package_name) / "README.md"
        text = path.read_text(encoding="utf-8")
        escalation_section = _section(text, "Escalation route")

        if _bullet_count(escalation_section) < 3:
            failures.append(
                f"{path.relative_to(REPO_ROOT).as_posix()}: escalation section needs at least three bullets"
            )

    assert not failures, "package README escalation guidance failed:\n" + "\n".join(
        failures
    )
