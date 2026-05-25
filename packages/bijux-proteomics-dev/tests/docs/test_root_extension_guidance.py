from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_root_readme_documents_repository_extension_contract() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "## Repository Extension Contract" in readme
    assert "`interrogate` and `bandit`" in readme
    assert "`api`, `local-esmfold`," in readme
    assert "`local-rosettafold`, `nl`, and `test`" in readme
    assert "`api-freeze` and `openapi-drift`" in readme
    assert "`ensure-venv` and `nlenv`" in readme
    assert "`manage_examples` and `manage_models`" in readme
    assert "`uv sync --group test`" in readme
