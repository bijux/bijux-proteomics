from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.release.governance.readme_truth import validate_readme_truth

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_root_readme_truth_gate_has_no_live_failures() -> None:
    assert validate_readme_truth(REPO_ROOT) == ()
