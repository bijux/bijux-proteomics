from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_artifact_governance_doc_publishes_policy_and_matrix() -> None:
    path = (
        REPO_ROOT
        / "docs"
        / "01-bijux-proteomics"
        / "operations"
        / "artifact-governance.md"
    )
    text = path.read_text(encoding="utf-8")

    expected_bits = [
        "## Transient Artifact Policy",
        "`artifacts/`",
        "make test-clean",
        "make clean-root-artifacts",
        "make quality-artifact-governance",
        "## File Ownership Matrix",
        "configs/package-governance/repository-file-ownership.toml",
        "## Prohibited Spillover",
        "no benchmark roots outside `bijux-proteomics-core`",
    ]
    missing = [bit for bit in expected_bits if bit not in text]
    assert not missing, (
        f"{path.relative_to(REPO_ROOT).as_posix()}: missing {', '.join(missing)}"
    )
