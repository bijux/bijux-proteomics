from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_root_readme_documents_local_artifact_contract() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "transient local outputs belong under `artifacts/`" in readme
    assert "`make quality-artifact-governance`" in readme
    assert "`make quality-architecture-regression`" in readme
    assert "`make release-preflight`" in readme
    assert "`artifacts/root/check-venv/`" in readme
    assert "`artifacts/root/docs/site/`" in readme
    assert "package roots must stay free of local `artifacts/`, `.venv`" in readme
