from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.quality.graphs.package_graph import load_workspace_packages


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
        "last_reviewed: 2026-07-21",
        "---",
        "",
        "# Package Contributor Onboarding",
        "",
        "A safe change begins by locating the package that owns the behavior, the contracts it consumes, and the evidence that can prove the change. The repository contains canonical product packages, compatibility distributions, and maintainer automation; similar names do not imply shared ownership.",
        "",
        "```mermaid",
        "flowchart LR",
        '    question["behavior or contract to change"] --> owner{"which package owns its meaning?"}',
        '    owner --> docs["package README + handbook"]',
        '    docs --> source["owned source and public interfaces"]',
        '    source --> tests["package tests + boundary checks"]',
        '    tests --> evidence["repository gates and release evidence"]',
        '    owner -. unclear .-> stop["inspect ownership boundaries before editing"]',
        "```",
        "",
        "## Establish Ownership",
        "",
        "1. state the user-visible or scientific behavior that will change;",
        "2. read the repository handbook and the candidate package `README.md`;",
        "3. open the package handbook, source tree, and tests before choosing an implementation seam;",
        "4. inspect direct workspace dependencies and confirm their direction will remain valid;",
        "5. identify the narrow package checks and repository gates that prove the change.",
        "",
        "Do not choose an owner from an import name alone. Alias distributions can forward to a canonical package, Runtime can execute a Core contract without owning its scientific meaning, and Intelligence can consume Knowledge evidence without owning its history.",
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
            "## Dependency Direction",
            "",
            "Foundation owns portable identifiers, schemas, serialization, and typed outcomes. Core adds proteomics meaning. Knowledge adds evidence custody. Intelligence adds advisory judgment. Lab adds operational consequence. Runtime may integrate those packages to execute a request, but that dependency breadth does not transfer their authority to Runtime.",
            "",
            "```mermaid",
            "flowchart LR",
            '    foundation["Foundation contracts"] --> core["Core science"]',
            '    foundation --> knowledge["Knowledge evidence"]',
            "    core --> intelligence[\"Intelligence judgment\"]",
            "    knowledge --> intelligence",
            "    core --> lab[\"Lab consequence\"]",
            "    knowledge --> lab",
            "    core --> runtime[\"Runtime execution\"]",
            "    knowledge --> runtime",
            "    intelligence --> runtime",
            "    lab --> runtime",
            "```",
            "",
            "An import that points against these meanings needs an explicit boundary review. Do not solve a circular dependency by moving domain behavior into Foundation or a compatibility package.",
            "",
            "## Choose The Maintained Surface",
            "",
            "| Change concern | Canonical owner | First proof |",
            "| --- | --- | --- |",
            "| identifiers, schemas, serialization, typed outcomes | `bijux-proteomics-foundation` | contract and schema tests |",
            "| proteomics algorithms, workflow meaning, QC, benchmark acceptance | `bijux-proteomics-core` | scientific tests and benchmark evidence |",
            "| evidence records, grounding, contradiction, reconciliation | `bijux-proteomics-knowledge` | provenance and graph-integrity tests |",
            "| ranking, challenge, downgrade, recommendation, refusal | `bijux-proteomics-intelligence` | decision and calibration tests |",
            "| assay planning, readiness, handoff, observation | `bijux-proteomics-lab` | readiness, control, and outcome tests |",
            "| provider selection, run state, artifacts, replay | `bijux-proteomics-runtime` | execution and replay tests |",
            "| repository governance, docs integrity, release validation | `bijux-proteomics-dev` | targeted governance check |",
            "| historical imports, commands, and routes | compatibility distribution | parity test against canonical owner |",
            "",
            "Treat `agentic-proteins`, `bijux-proteomics`, and the `proteomics-*` distributions as compatibility commitments. Preserve or deliberately retire their observable behavior; do not place new product ownership there.",
            "",
            "## Prove The Change",
            "",
            "Before committing, a reviewer should be able to answer:",
            "",
            "- which package owns the changed meaning and which packages only consume it?",
            "- which public import, CLI, schema, artifact, or documentation contract changed?",
            "- which tests cover success, refusal, malformed input, and boundary behavior?",
            "- which generated outputs were refreshed from their owning source?",
            "- which benchmark or run evidence supports any widened scientific claim?",
            "- which known limitation remains after the change?",
            "",
            "Use [Testing and Validation](testing-and-validation.md) to select repository gates, [Artifact Governance](artifact-governance.md) for output placement, and [Maintainer Safe Change](../../08-bijux-proteomics-maintain/bijux-proteomics-dev/maintainer-safe-change.md) for the complete review path.",
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
