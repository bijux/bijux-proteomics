from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _read_runtime_doc(name: str) -> str:
    return (REPO_ROOT / "docs" / "09-bijux-proteomics-runtime" / name).read_text(
        encoding="utf-8"
    )


def test_runtime_index_routes_reviewers_to_black_box_rerun_surfaces() -> None:
    text = _read_runtime_doc("index.md")

    expected_bits = [
        "Runtime Execution Boundary",
        "Black-Box Run Verification",
        "Raw Versus Import Execution",
        "Runtime Replay Challenges",
        "Runtime Environment Contracts",
        "Runtime Artifact Stability",
        "Runtime Rerun Refusals",
    ]
    missing = [bit for bit in expected_bits if bit not in text]
    assert not missing, f"missing runtime handbook routes: {missing}"


def test_runtime_execution_boundary_page_starts_from_public_manifest_routes() -> None:
    text = _read_runtime_doc("runtime-execution-boundary.md")

    assert "# Runtime Execution Boundary" in text
    assert "independent reviewer reopen a shipped workflow family" in text
    assert (
        "| workflow family | start from | runtime entrypoint | checked bundle | current limit |"
        in text
    )
    assert "source_locator_manifest.json" in text
    assert "runtime-rerun-refusals.md" not in text


def test_runtime_black_box_docs_name_execution_modes_replay_and_refusal_paths() -> None:
    verification = _read_runtime_doc("black-box-run-verification.md")
    execution = _read_runtime_doc("raw-versus-import-execution.md")
    replay = _read_runtime_doc("runtime-replay-challenges.md")
    environment = _read_runtime_doc("runtime-environment-contracts.md")
    stability = _read_runtime_doc("runtime-artifact-stability.md")
    refusals = _read_runtime_doc("runtime-rerun-refusals.md")

    assert "# Black-Box Run Verification" in verification
    assert "stage lineage artifact" in verification
    assert "failure_replay.json" in verification

    assert "# Raw Versus Import Execution" in execution
    assert "`import_only`" in execution
    assert "`raw_executable`" in execution
    assert "vendor-parity" in execution

    assert "# Runtime Replay Challenges" in replay
    assert "Clean-environment requirements:" in replay
    assert "Minimal steps:" in replay

    assert "# Runtime Environment Contracts" in environment
    assert "## Qualify an environment" in environment
    assert "## Record the qualification" in environment
    assert "irreproducible" in environment
    assert "supported combinations:" in environment
    assert "unsupported combinations:" in environment

    assert "# Runtime Artifact Stability" in stability
    assert "## Classify Drift Before Comparing Runs" in stability
    assert "## Minimum comparison record" in stability
    assert "unclassified drift" in stability
    assert "bit-stable paths:" in stability
    assert "review-stable surfaces:" in stability

    assert "# Runtime Rerun Refusals" in refusals
    assert "## Current family posture" in refusals
    assert "## Close or preserve a refusal" in refusals
    assert "strongest supported lane" in refusals
    assert "refusal reasons:" in refusals
    assert "next evidence paths:" in refusals
