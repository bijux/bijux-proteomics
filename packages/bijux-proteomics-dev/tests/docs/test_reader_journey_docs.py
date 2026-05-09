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
    for workflow_family in ("`dda`", "`dia`", "`lfq`", "`multiplex`", "`ptm`", "`targeted`"):
        assert workflow_family in text
    assert "trust status" in text
    assert "primary run mode" in text
    assert "benchmark coverage" in text
    assert "current blockers" in text
    assert "Scientist Journey" in text
    assert "Benchmark Assets" in text
    assert "Execution" in text
    assert "Decision Support" in text


def test_scientist_operator_and_maintainer_journeys_land_on_owner_surfaces() -> None:
    scientist = _read("docs/workflow-families/scientist-journey.md")
    operator = _read("docs/execution/operator-rerun-journey.md")
    maintainer = _read("docs/maintenance/maintainer-safe-change.md")

    assert "Workflow Claim Grounding" in scientist
    assert "Workflow Recommendation Confidence" in scientist
    assert "Lab Consequence" in scientist
    assert "Current Capability Limits" in scientist

    assert "Benchmark Rerun Kits" in operator
    assert "Runtime Environment Contracts" in operator
    assert "Black-Box Benchmark Dashboard" in operator
    assert "Flagship Acceptance Bars" in operator

    assert "Cross-Package Ownership" in maintainer
    assert "Release Support" in maintainer
    assert "Testing And Validation" in maintainer
    assert "Release Readiness Matrix" in maintainer
