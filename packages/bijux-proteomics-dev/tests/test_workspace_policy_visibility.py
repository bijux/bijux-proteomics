from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_POLICY_PATH = "/Users/bijan/bijuxx/CODEX.md"


def test_root_readme_points_to_workspace_working_agreement() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert WORKSPACE_POLICY_PATH in readme
    assert "workspace working agreement" in readme.lower()


def test_contributing_points_to_workspace_working_agreement() -> None:
    contributing = (REPO_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert WORKSPACE_POLICY_PATH in contributing
