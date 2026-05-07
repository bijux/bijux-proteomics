from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.release.governance.workflow_authority_docs import (
    validate_workflow_authority_docs,
)

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_workflow_authority_docs_match_matrix() -> None:
    assert validate_workflow_authority_docs(REPO_ROOT) == ()
