from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_mkdocs_nav_frontloads_reader_first_categories() -> None:
    mkdocs = _read("mkdocs.yml")

    ordered_labels = [
        "\n  - Home: index.md",
        "\n  - Product Overview:",
        "\n  - Benchmark Assets:",
        "\n  - Execution:",
        "\n  - Workflow Families:",
        "\n  - Decision Support:",
        "\n  - Lab Consequence:",
        "\n  - Maintenance:",
        "\n  - Repository Handbook:",
    ]

    positions = [mkdocs.index(label) for label in ordered_labels]

    assert positions == sorted(positions)


def test_workflow_family_index_covers_family_status_run_mode_and_blockers() -> None:
    text = _read("docs/workflow-families/index.md")

    assert "# Workflow Families" in text
    for workflow_family in (
        "`dda`",
        "`dia`",
        "`lfq`",
        "`multiplex`",
        "`ptm`",
        "`targeted`",
    ):
        assert workflow_family in text
    assert "trust status" in text
    assert "primary run mode" in text
    assert "benchmark coverage" in text
    assert "current blockers" in text
    assert "DDA Cross-Package Handbook" in text
    assert "Scientist Journey" in text
    assert "Benchmark Assets" in text
    assert "Execution" in text
    assert "Decision Support" in text


def test_scientist_operator_and_maintainer_journeys_land_on_owner_surfaces() -> None:
    scientist = _read("docs/workflow-families/scientist-journey.md")
    operator = _read("docs/execution/operator-rerun-journey.md")
    maintainer = _read("docs/maintenance/maintainer-safe-change.md")
    decision_support = _read("docs/decision-support/index.md")
    lab_consequence = _read("docs/lab-consequence/index.md")

    assert "Workflow Claim Grounding" in scientist
    assert "Workflow Recommendation Confidence" in scientist
    assert "Lab Consequence" in scientist
    assert "Current Capability Limits" in scientist
    assert "DDA Cross-Package Handbook" in scientist

    assert "Benchmark Rerun Kits" in operator
    assert "Runtime Environment Contracts" in operator
    assert "Black-Box Benchmark Dashboard" in operator
    assert "Flagship Acceptance Bars" in operator

    assert "Cross-Package Ownership" in maintainer
    assert "Release Support" in maintainer
    assert "Testing And Validation" in maintainer
    assert "Release Readiness Matrix" in maintainer

    assert "Workflow Consequence Maps" in decision_support
    assert "What Changed The Recommendation" in decision_support
    assert "Outcome Learning Loops" in lab_consequence
    assert "Workflow Refusal Handbook" in lab_consequence


def test_package_index_pages_hand_off_shared_routes_before_local_routes() -> None:
    package_index_paths = [
        "docs/02-agentic-proteins/index.md",
        "docs/03-bijux-proteomics-foundation/index.md",
        "docs/04-bijux-proteomics-core/index.md",
        "docs/05-bijux-proteomics-intelligence/index.md",
        "docs/06-bijux-proteomics-knowledge/index.md",
        "docs/07-bijux-proteomics-lab/index.md",
        "docs/08-bijux-proteomics-maintain/index.md",
        "docs/09-bijux-proteomics-runtime/index.md",
    ]

    for path in package_index_paths:
        text = _read(path)
        assert "## Shared Reader Routes" in text
        assert "## Start Inside" in text


def test_mkdocs_config_split_keeps_shared_config_repository_agnostic() -> None:
    mkdocs = _read("mkdocs.yml")
    shared = _read("mkdocs.shared.yml")

    assert "redirect_maps:" in mkdocs
    assert "docs_package: bijux-proteomics-dev" in mkdocs
    assert "repository: bijux-proteomics" in mkdocs
    assert "hub_links:" in mkdocs

    assert "redirect_maps:" not in shared
    assert "docs_package:" not in shared
    assert "repository: bijux-proteomics" not in shared
    assert "hub_links:" not in shared


def test_knowledge_intelligence_and_lab_indexes_route_readers_into_consequence_chain() -> (
    None
):
    knowledge = _read("docs/06-bijux-proteomics-knowledge/index.md")
    intelligence = _read("docs/05-bijux-proteomics-intelligence/index.md")
    lab = _read("docs/07-bijux-proteomics-lab/index.md")

    assert "Workflow Consequence Maps" in knowledge
    assert "What Changed The Recommendation" in knowledge

    assert "Workflow Consequence Maps" in intelligence
    assert "What Changed The Recommendation" in intelligence

    assert "Workflow Consequence Maps" in lab
    assert "Outcome Learning Loops" in lab
    assert "Workflow Refusal Handbook" in lab
