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


def test_package_readmes_keep_selection_and_routing_guidance_substantive() -> None:
    failures: list[str] = []

    for package_name in _package_names():
        path = _package_dir(package_name) / "README.md"
        text = path.read_text(encoding="utf-8")

        choose_section = _section(text, "Choose this package when")
        route_section = _section(text, "Route elsewhere when")
        verification_section = _section(text, "Verification route")

        if _bullet_count(choose_section) < 3:
            failures.append(
                f"{path.relative_to(REPO_ROOT).as_posix()}: choose section needs at least three bullets"
            )
        if _bullet_count(route_section) < 3:
            failures.append(
                f"{path.relative_to(REPO_ROOT).as_posix()}: route section needs at least three bullets"
            )
        if _bullet_count(verification_section) < 3:
            failures.append(
                f"{path.relative_to(REPO_ROOT).as_posix()}: verification section needs at least three bullets"
            )

    assert not failures, "package README routing guidance failed:\n" + "\n".join(
        failures
    )


def test_knowledge_intelligence_and_lab_readmes_route_through_shared_consequence_surfaces() -> (
    None
):
    expected_bits = {
        "bijux-proteomics-knowledge": (
            "## Consequence chain route",
            "Workflow Consequence Maps",
            "What Changed The Recommendation",
            "Outcome Learning Loops",
        ),
        "bijux-proteomics-intelligence": (
            "## Consequence chain route",
            "Workflow Consequence Maps",
            "What Changed The Recommendation",
            "Workflow Refusal Handbook",
        ),
        "bijux-proteomics-lab": (
            "## Consequence chain route",
            "Workflow Consequence Maps",
            "Outcome Learning Loops",
            "Workflow Refusal Handbook",
        ),
    }

    failures: list[str] = []
    for package_name, bits in expected_bits.items():
        path = _package_dir(package_name) / "README.md"
        text = path.read_text(encoding="utf-8")
        missing = [bit for bit in bits if bit not in text]
        if missing:
            failures.append(
                f"{path.relative_to(REPO_ROOT).as_posix()}: missing {', '.join(missing)}"
            )

    assert not failures, "package README consequence routing failed:\n" + "\n".join(
        failures
    )
