from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.quality.package_graph import load_workspace_packages


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() and (parent / "packages").exists():
            return parent
    raise RuntimeError("Unable to resolve repository root for contributor onboarding")


REPO_ROOT = _repo_root()
ONBOARDING_PATH = (
    REPO_ROOT
    / "docs"
    / "01-bijux-proteomics"
    / "operations"
    / "package-contributor-onboarding.md"
)


@dataclass(frozen=True)
class ContributorOnboardingEntry:
    package_name: str
    distribution_name: str
    import_root: str
    workspace_dependencies: tuple[str, ...]
    readme_path: str
    tests_path: str
    docs_root: str


def _docs_root_for_package(repo_root: Path, package_name: str) -> str:
    if package_name == "bijux-proteomics-dev":
        return "docs/08-bijux-proteomics-maintain/bijux-proteomics-dev"
    candidates = sorted((repo_root / "docs").glob(f"*-{package_name}"))
    if len(candidates) != 1:
        raise ValueError(f"unable to resolve docs root for {package_name!r}")
    return candidates[0].relative_to(repo_root).as_posix()


def build_contributor_onboarding_entries(
    repo_root: Path,
) -> tuple[ContributorOnboardingEntry, ...]:
    """Build the package family onboarding map."""
    entries = [
        ContributorOnboardingEntry(
            package_name=package.package_name,
            distribution_name=package.distribution_name,
            import_root=package.import_root,
            workspace_dependencies=package.workspace_dependencies,
            readme_path=package.readme_path.relative_to(repo_root).as_posix(),
            tests_path=package.tests_dir.relative_to(repo_root).as_posix(),
            docs_root=_docs_root_for_package(repo_root, package.package_name),
        )
        for package in load_workspace_packages(repo_root)
    ]
    return tuple(entries)


def _render_markdown(entries: tuple[ContributorOnboardingEntry, ...]) -> str:
    lines = [
        "---",
        "title: Package Contributor Onboarding",
        "audience: contributor",
        "type: guide",
        "status: canonical",
        "owner: bijux-proteomics-dev",
        "last_reviewed: 2026-04-29",
        "---",
        "",
        "# Package Contributor Onboarding",
        "",
        "Use this page when a contributor is new to the package family and needs the shortest honest path to the right package, docs, and tests.",
        "",
        "## First Moves",
        "",
        "1. start with the repository handbook and the target package `README.md` before editing code",
        "2. open the package docs root and package tests before inventing a new pattern",
        "3. check direct workspace dependencies so boundary pressure is visible before implementation",
        "",
        "## Package Map",
        "",
        "| package | distribution | import root | direct workspace dependencies | read first | tests | docs |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for entry in entries:
        dependencies = (
            ", ".join(f"`{dependency}`" for dependency in entry.workspace_dependencies)
            if entry.workspace_dependencies
            else "_none_"
        )
        lines.append(
            f"| `{entry.package_name}` | `{entry.distribution_name}` | `{entry.import_root}` | {dependencies} | `{entry.readme_path}` | `{entry.tests_path}` | `{entry.docs_root}` |"
        )
    lines.extend(
        [
            "",
            "## Reading Order",
            "",
            "- choose `bijux-proteomics-dev` for repo policy, docs integrity, release validation, and package boundary checks",
            "- choose `bijux-proteomics-core` for scientific contracts and stable proteomics model behavior",
            "- choose `bijux-proteomics-runtime` only when the concern is orchestration, replay, or execution control",
            "- treat `agentic-proteins` as compatibility stewardship, not a place for new product growth",
            "",
        ]
    )
    return "\n".join(lines)


def _is_up_to_date(entries: tuple[ContributorOnboardingEntry, ...]) -> bool:
    if not ONBOARDING_PATH.exists():
        return False
    return ONBOARDING_PATH.read_text(encoding="utf-8") == _render_markdown(entries)


def run(check: bool = False) -> int:
    entries = build_contributor_onboarding_entries(REPO_ROOT)
    if check:
        if _is_up_to_date(entries):
            print(f"contributor onboarding is up to date for {len(entries)} packages")
            return 0
        print("contributor onboarding is stale; regenerate it")
        return 1
    ONBOARDING_PATH.parent.mkdir(parents=True, exist_ok=True)
    ONBOARDING_PATH.write_text(_render_markdown(entries), encoding="utf-8")
    print(f"generated contributor onboarding for {len(entries)} packages")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package contributor onboarding page."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the generated contributor onboarding page is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
