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


def _release_doc_packages() -> list[str]:
    return [
        package_name
        for package_name in _package_names()
        if (_package_dir(package_name) / "docs" / "maintainer" / "pypi.md").exists()
    ]


def test_publishable_packages_expose_maintainer_release_docs() -> None:
    missing = [
        path.relative_to(REPO_ROOT).as_posix()
        for package_name in _release_doc_packages()
        for path in [_package_dir(package_name) / "docs" / "maintainer" / "pypi.md"]
        if not path.exists()
    ]
    assert not missing, "missing maintainer release docs:\n" + "\n".join(missing)


def test_release_docs_share_identity_and_release_sections() -> None:
    failures: list[str] = []

    for package_name in _release_doc_packages():
        path = _package_dir(package_name) / "docs" / "maintainer" / "pypi.md"
        text = path.read_text(encoding="utf-8")
        expected_bits = [
            "# PyPI Maintainer Notes",
            "## Package identity",
            f"- package: `{package_name}`",
            f"- import root: `{_import_root(package_name)}`",
            "- repository: `bijux/bijux-proteomics`",
            "## Release surface",
            "## Release contract",
            "## Validation focus",
            "## Publication checkpoints",
            "## Release escalation signals",
            "## Release review questions",
            "## Release impact signals",
            "## Release checklist",
            "## Explicit non-goals",
        ]
        missing = [bit for bit in expected_bits if bit not in text]
        if missing:
            failures.append(
                f"{path.relative_to(REPO_ROOT).as_posix()}: missing {', '.join(missing)}"
            )

    assert not failures, "maintainer release docs contract failed:\n" + "\n".join(
        failures
    )


def test_maintainer_package_entry_doc_has_role_and_routing_sections() -> None:
    path = REPO_ROOT / "packages" / "bijux-proteomics-dev" / "docs" / "index.md"
    text = path.read_text(encoding="utf-8")
    expected_bits = [
        "## Package identity",
        "- Distribution name: `bijux-proteomics-dev`",
        "- Import root: `bijux_proteomics_dev`",
        "## Package role",
        "## Boundary reminders",
        "## Key maintainer entrypoints",
        "## Release policy entrypoints",
        "## Release escalation surfaces",
        "## Release review questions",
        "## Release impact signals",
        "## Source guide",
        "## Downstream expectation",
    ]
    missing = [bit for bit in expected_bits if bit not in text]
    assert not missing, (
        f"{path.relative_to(REPO_ROOT).as_posix()}: missing {', '.join(missing)}"
    )


def test_maintainer_test_doc_has_scope_and_expectation_sections() -> None:
    path = REPO_ROOT / "packages" / "bijux-proteomics-dev" / "docs" / "TESTS.md"
    text = path.read_text(encoding="utf-8")
    expected_bits = [
        "## Test scope",
        "## Required test strata",
        "## Maintainer expectations",
        "## Common validation surfaces",
        "## Release proof expectations",
        "## Release-blocking signals",
        "## Non-goals",
    ]
    missing = [bit for bit in expected_bits if bit not in text]
    assert not missing, (
        f"{path.relative_to(REPO_ROOT).as_posix()}: missing {', '.join(missing)}"
    )


def test_maintainer_release_docs_keep_publication_guidance_substantive() -> None:
    failures: list[str] = []

    for package_name in _release_doc_packages():
        path = _package_dir(package_name) / "docs" / "maintainer" / "pypi.md"
        text = path.read_text(encoding="utf-8")
        publication_section = _section(text, "Publication checkpoints")
        if _bullet_count(publication_section) < 3:
            failures.append(
                f"{path.relative_to(REPO_ROOT).as_posix()}: publication section needs at least three bullets"
            )
        escalation_section = _section(text, "Release escalation signals")
        if _bullet_count(escalation_section) < 3:
            failures.append(
                f"{path.relative_to(REPO_ROOT).as_posix()}: release escalation section needs at least three bullets"
            )

    index_path = REPO_ROOT / "packages" / "bijux-proteomics-dev" / "docs" / "index.md"
    index_text = index_path.read_text(encoding="utf-8")
    if _bullet_count(_section(index_text, "Release policy entrypoints")) < 3:
        failures.append(
            f"{index_path.relative_to(REPO_ROOT).as_posix()}: release policy entrypoints section needs at least three bullets"
        )
    if _bullet_count(_section(index_text, "Release escalation surfaces")) < 3:
        failures.append(
            f"{index_path.relative_to(REPO_ROOT).as_posix()}: release escalation surfaces section needs at least three bullets"
        )

    tests_path = REPO_ROOT / "packages" / "bijux-proteomics-dev" / "docs" / "TESTS.md"
    tests_text = tests_path.read_text(encoding="utf-8")
    if _bullet_count(_section(tests_text, "Release proof expectations")) < 3:
        failures.append(
            f"{tests_path.relative_to(REPO_ROOT).as_posix()}: release proof expectations section needs at least three bullets"
        )
    if _bullet_count(_section(tests_text, "Release-blocking signals")) < 3:
        failures.append(
            f"{tests_path.relative_to(REPO_ROOT).as_posix()}: release-blocking signals section needs at least three bullets"
        )

    assert not failures, (
        "maintainer release publication guidance failed:\n" + "\n".join(failures)
    )
